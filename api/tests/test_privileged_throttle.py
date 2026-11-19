"""Privileged settings actions share durable login failure throttling."""
import sqlite3
import time

from fastapi.testclient import TestClient

from app.main import Settings, create_app

PASSWORD = "private-synthetic-password-2026"
NEW_PASSWORD = "rotated-synthetic-password-2026"


def authenticate(client):
    result = client.post("/v1/session", json={"password": PASSWORD})
    assert result.status_code == 200
    return {"Authorization": "Bearer " + result.json()["access_token"]}


def test_repeated_failed_rotation_blocks_other_privileged_routes(tmp_path):
    storage = tmp_path / "library"
    with TestClient(create_app(Settings(storage, PASSWORD))) as client:
        headers = authenticate(client)
        for _ in range(5):
            rejected = client.post(
                "/v1/settings/password", headers=headers,
                json={"current_password": "wrong", "new_password": NEW_PASSWORD},
            )
            assert rejected.status_code == 401
        assert client.post(
            "/v1/settings/password", headers=headers,
            json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        ).status_code == 429
        assert client.post(
            "/v1/settings/revoke-sessions", headers=headers,
            json={"password": PASSWORD},
        ).status_code == 429
        with sqlite3.connect(storage / "photos.sqlite3") as db:
            entries = db.execute(
                "SELECT peer_digest, failed_count FROM auth_failures"
            ).fetchall()
            assert len(entries) == 1
            assert entries[0][1] == 5
            assert "testclient" not in entries[0][0]
            db.execute(
                "UPDATE auth_failures SET window_start=?", (int(time.time()) - 901,)
            )
        assert client.post(
            "/v1/settings/revoke-sessions", headers=headers,
            json={"password": PASSWORD},
        ).status_code == 200
        assert client.get("/v1/assets", headers=headers).status_code == 401
        assert authenticate(client)


def test_revoke_failures_throttle_login_and_allow_rotation_after_expiry(tmp_path):
    storage = tmp_path / "photos"
    with TestClient(create_app(Settings(storage, PASSWORD))) as client:
        headers = authenticate(client)
        for _ in range(5):
            assert client.post(
                "/v1/settings/revoke-sessions", headers=headers,
                json={"password": "incorrect"},
            ).status_code == 401
        assert client.post("/v1/session", json={"password": PASSWORD}).status_code == 429
        with sqlite3.connect(storage / "photos.sqlite3") as db:
            db.execute(
                "UPDATE auth_failures SET window_start=?", (int(time.time()) - 901,)
            )
        assert client.post(
            "/v1/settings/password", headers=headers,
            json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        ).status_code == 200
        assert client.get("/v1/assets", headers=headers).status_code == 401
        assert client.post(
            "/v1/session", json={"password": NEW_PASSWORD}
        ).status_code == 200
