"""CLI contract smoke against a local synthetic HTTP server; no real media or credentials."""
import json
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import pytest

from app import cli

ASSET_ID = "00000000-0000-4000-8000-000000000042"


@contextmanager
def fake_server():
    events = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def respond(self, status, result=None, raw=None):
            data = raw if raw is not None else json.dumps(result or {}).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            events.append(("GET", self.path, self.headers.get("Authorization", "")))
            if self.path == "/health":
                self.respond(200, {"status": "ok"})
            elif self.path.startswith("/v1/assets?"):
                self.respond(200, {"items": [], "total": 0})
            elif self.path.startswith("/v1/assets/") and self.path.endswith("/original"):
                self.respond(200, raw=b"synthetic-test-bytes")
            elif self.path == "/v1/albums":
                self.respond(200, {"items": []})
            elif self.path == "/redirect":
                self.send_response(302)
                self.send_header("Location", "https://example.org/")
                self.end_headers()
            else:
                self.respond(404, {"detail": "missing"})

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            data = self.rfile.read(length)
            events.append(("POST", self.path, self.headers.get("Authorization", ""), data))
            if self.path == "/v1/session":
                self.respond(200, {"access_token": "session-from-test-only"})
            elif self.path == "/v1/assets":
                assert b"synthetic-test-bytes" in data
                self.respond(201, {"id": ASSET_ID, "bytes": 20})
            elif self.path == "/v1/albums":
                self.respond(201, {"id": ASSET_ID, "name": "Family"})
            elif self.path == "/v1/settings/password":
                self.respond(200, {"changed": True, "sessions_revoked": True})
            else:
                self.respond(200, {"id": ASSET_ID})

        def do_PATCH(self):
            events.append(("PATCH", self.path, self.headers.get("Authorization", "")))
            self.respond(200, {"id": ASSET_ID, "favorite": True})

        def do_DELETE(self):
            events.append(("DELETE", self.path, self.headers.get("Authorization", "")))
            self.respond(204, raw=b"")

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", events
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.parametrize("url", [
    "http://external.example", "ftp://127.0.0.1",
    "https://user:password@example.com", "https://example.com/private",
    "https://example.com/?token=secret", "https://example.com/#fragment",
    "http://127.0.0.1:0",
])
def test_cli_rejects_insecure_or_malformed_server_urls(url):
    with pytest.raises(cli.PhotosError):
        cli.validate_server(url)


def test_cli_health_read_and_token_is_not_echoed(monkeypatch, capsys):
    monkeypatch.setenv("PHOTOS_ACCESS_TOKEN", "private-test-token")
    with fake_server() as (server, events):
        assert cli.main(["--server", server, "health"]) == 0
        assert json.loads(capsys.readouterr().out) == {"status": "ok"}
        assert cli.main(["--server", server, "list", "--search", "family photo", "--limit", "2"]) == 0
        output = capsys.readouterr()
        assert json.loads(output.out)["total"] == 0
        assert "private-test-token" not in output.out + output.err
        assert any("family+photo" in event[1] for event in events if event[0] == "GET")
        assert cli.main(["--server", server, "create-album", "Family"]) == 0
        assert json.loads(capsys.readouterr().out)["name"] == "Family"
        assert cli.main(["--server", server, "favorite", ASSET_ID]) == 0
        assert json.loads(capsys.readouterr().out)["favorite"] is True
        assert cli.main(["--server", server, "trash", ASSET_ID]) == 2
        assert "--yes" in capsys.readouterr().err
        assert cli.main(["--server", server, "trash", ASSET_ID, "--yes"]) == 0
        assert any(event[0] == "DELETE" for event in events)


def test_cli_upload_download_no_overwrite(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("PHOTOS_ACCESS_TOKEN", "private-test-token")
    source = tmp_path / "input.bin"
    source.write_bytes(b"synthetic-test-bytes")
    with fake_server() as (server, _):
        assert cli.main(["--server", server, "upload", str(source)]) == 0
        assert json.loads(capsys.readouterr().out)["id"] == ASSET_ID
        target = tmp_path / "download.bin"
        assert cli.main(["--server", server, "download", ASSET_ID, "--output", str(target)]) == 0
        assert target.read_bytes() == b"synthetic-test-bytes"
        assert target.stat().st_mode & 0o777 == 0o600
        assert cli.main(["--server", server, "download", ASSET_ID, "--output", str(target)]) == 2
        assert target.read_bytes() == b"synthetic-test-bytes"
        assert "refusing to overwrite" in capsys.readouterr().err
        assert cli.main(["--server", server, "download", "../bad", "--output", str(tmp_path / "bad")]) == 2


def test_cli_ephemeral_login_revokes_session(monkeypatch, capsys):
    monkeypatch.delenv("PHOTOS_ACCESS_TOKEN", raising=False)
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt: "example-password")
    with fake_server() as (server, events):
        assert cli.main(["--server", server, "albums"]) == 0
        result = capsys.readouterr()
        assert "example-password" not in result.out + result.err
        assert events[-1][:2] == ("DELETE", "/v1/session")
        assert events[-1][2] == "Bearer session-from-test-only"


def test_cli_disallows_redirect_following():
    with fake_server() as (server, events):
        api = cli.Api(server)
        with pytest.raises(cli.PhotosError, match="302"):
            api.request("GET", "/redirect")
        assert len(events) == 1 and events[0][1] == "/redirect"


def test_cli_backups_are_explicit_and_non_overwriting(monkeypatch, tmp_path):
    monkeypatch.setenv("PHOTOS_ACCESS_TOKEN", "not-needed-for-offline")
    output = tmp_path / "a.tar"
    monkeypatch.setattr(cli.offline, "backup", lambda src, dst: {"archive": str(dst)})
    result = cli.run(cli.parse_args(["backup", "--data-dir", "/no/private/data", "--output", str(output)]))
    assert result["archive"] == str(output)


def test_cli_entrypoint_declares_version(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.parse_args(["--version"])
    assert exc.value.code == 0
    assert "GoreeCloud Photos" in capsys.readouterr().out


def test_cli_offline_archive_verify_and_isolated_restore(tmp_path, capsys, monkeypatch):
    from test_backup import seed_library

    monkeypatch.delenv("PHOTOS_ACCESS_TOKEN", raising=False)
    home = tmp_path / "library"
    seed_library(home)
    archive = tmp_path / "backup.tar"
    dest = tmp_path / "restored"
    assert cli.main(["backup", "--data-dir", str(home), "--output", str(archive)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["assets"] == 1
    assert cli.main(["verify-backup", "--input", str(archive)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["verified"] is True
    assert report["assets"] == 1
    assert not dest.exists()
    assert cli.main(
        ["restore-backup", "--input", str(archive), "--data-dir", str(dest)]
    ) == 0
    assert json.loads(capsys.readouterr().out)["assets"] == 1
    assert (dest / "photos.sqlite3").is_file()
    assert cli.main(
        ["restore-backup", "--input", str(archive), "--data-dir", str(dest)]
    ) == 2
    assert "nonexistent data directory" in capsys.readouterr().err.lower()



def test_cli_change_password_prompts_and_clears_ephemeral_session(monkeypatch, capsys):
    old = "private-old-password-2026"
    new = "private-new-password-2026"
    answers = iter([old, new, new])
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt: next(answers))
    monkeypatch.delenv("PHOTOS_ACCESS_TOKEN", raising=False)
    with fake_server() as (server, events):
        assert cli.main(["--server", server, "change-password"]) == 0
        report = capsys.readouterr()
        assert json.loads(report.out) == {"changed": True, "sessions_revoked": True}
        for secret in [old, new, "session-from-test-only"]:
            assert secret not in report.out + report.err
        assert [event[1] for event in events] == [
            "/v1/session", "/v1/settings/password", "/v1/session"
        ]
        payload = json.loads(events[1][3])
        assert payload == {"current_password": old, "new_password": new}
        assert events[2][0] == "DELETE"


def test_cli_change_password_rejects_mismatch_without_network_access(monkeypatch, capsys):
    responses = iter(["old-passphrase-2026", "fresh-passphrase-2026", "different-passphrase"])
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt: next(responses))
    monkeypatch.delenv("PHOTOS_ACCESS_TOKEN", raising=False)
    with fake_server() as (server, events):
        assert cli.main(["--server", server, "change-password"]) == 2
        assert events == []
        assert "confirmation" in capsys.readouterr().err.lower()


def test_cli_change_password_accepts_explicit_token_without_login(monkeypatch, capsys):
    old, new = "old-passphrase-2026", "new-passphrase-2026"
    monkeypatch.setenv("PHOTOS_ACCESS_TOKEN", "preexisting-private-token")
    values = iter([old, new, new])
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt: next(values))
    with fake_server() as (server, events):
        assert cli.main(["--server", server, "change-password"]) == 0
        assert len(events) == 1
        assert events[0][1] == "/v1/settings/password"
        assert events[0][2] == "Bearer preexisting-private-token"
        output = capsys.readouterr()
        assert "preexisting-private-token" not in output.out + output.err
