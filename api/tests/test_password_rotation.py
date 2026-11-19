"""Credential rotation persists, requires current secret, and revokes all sessions."""
from fastapi.testclient import TestClient

from app.main import Settings, create_app

INITIAL = "initial-private-password-2026"
REPLACEMENT = "second-unique-private-password-2026"


def token(client, password):
    response = client.post("/v1/session", json={"password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def headers(value):
    return {"Authorization": f"Bearer {value}"}


def test_rotation_requires_auth_current_password_and_eligible_new_secret(tmp_path):
    path = tmp_path / "data"
    with TestClient(create_app(Settings(path, INITIAL))) as client:
        uri = "/v1/settings/password"
        body = {"current_password": INITIAL, "new_password": REPLACEMENT}
        assert client.post(uri, json=body).status_code == 401
        first = token(client, INITIAL)
        second = token(client, INITIAL)
        assert client.post(
            uri, headers=headers(first),
            json={"current_password": "incorrect", "new_password": REPLACEMENT}
        ).status_code == 401
        assert client.post(
            uri, headers=headers(first),
            json={"current_password": INITIAL, "new_password": "short"}
        ).status_code == 422
        assert client.post(
            uri, headers=headers(first),
            json={"current_password": INITIAL, "new_password": INITIAL}
        ).status_code == 422
        # Validation failures must not log out a legitimate session.
        assert client.get("/v1/library/stats", headers=headers(second)).status_code == 200
        changed = client.post(uri, headers=headers(first), json=body)
        assert changed.status_code == 200, changed.text
        assert changed.json() == {"changed": True, "sessions_revoked": True}
        for prior in (first, second):
            assert client.get("/v1/assets", headers=headers(prior)).status_code == 401
        assert client.post("/v1/session", json={"password": INITIAL}).status_code == 401
        current = token(client, REPLACEMENT)
        assert client.get("/v1/library/stats", headers=headers(current)).status_code == 200

    with TestClient(create_app(Settings(path, None))) as restarted:
        assert restarted.post("/v1/session", json={"password": INITIAL}).status_code == 401
        another = token(restarted, REPLACEMENT)
        assert restarted.get("/v1/library/stats", headers=headers(another)).status_code == 200


def test_rotate_failure_cannot_change_credential_or_revoke_session(tmp_path):
    settings = Settings(tmp_path / "private", INITIAL)
    with TestClient(create_app(settings)) as client:
        existing = token(client, INITIAL)
        invalid = client.post(
            "/v1/settings/password", headers=headers(existing),
            json={"current_password": "wrong", "new_password": REPLACEMENT},
        )
        assert invalid.status_code == 401
        assert client.get("/v1/assets", headers=headers(existing)).status_code == 200
        assert token(client, INITIAL)
        assert client.post(
            "/v1/settings/password", headers=headers(existing),
            json={"current_password": INITIAL, "new_password": "x" * 1025},
        ).status_code == 422
