"""Exercise CLI session revocation over a loopback fixture."""
import json

from test_cli import fake_server

from app import cli


def test_revoke_all_interactively(monkeypatch, capsys):
    monkeypatch.delenv("PHOTOS_ACCESS_TOKEN", raising=False)
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt: "synthetic-password")
    with fake_server() as (server, calls):
        assert cli.main(["--server", server, "revoke-sessions"]) == 0
        assert json.loads(capsys.readouterr().out)["sessions_revoked"] is True
        assert [call[1] for call in calls] == [
            "/v1/session", "/v1/settings/revoke-sessions", "/v1/session"
        ]


def test_revoke_requires_password_before_network(monkeypatch, capsys):
    monkeypatch.delenv("PHOTOS_ACCESS_TOKEN", raising=False)
    monkeypatch.setattr(cli.getpass, "getpass", lambda prompt: "")
    with fake_server() as (server, calls):
        assert cli.main(["--server", server, "revoke-sessions"]) == 2
        assert calls == []
        assert "required" in capsys.readouterr().err.lower()
