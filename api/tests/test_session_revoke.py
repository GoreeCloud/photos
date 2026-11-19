"""Explicit all-session revocation without changing the library credential."""
from fastapi.testclient import TestClient

from app.main import Settings, create_app


def login(client, value):
    response = client.post("/v1/session", json={"password": value})
    assert response.status_code == 200
    return response.json()["access_token"]


def as_user(value):
    return {"Authorization": "Bearer " + value}


def test_revocation_requires_bearer_and_current_credential(tmp_path):
    password = "only-for-synthetic-tests-2026"
    with TestClient(create_app(Settings(tmp_path / "library", password))) as client:
        first = login(client, password)
        second = login(client, password)
        uri = "/v1/settings/revoke-sessions"
        assert client.post(uri, json={"password": password}).status_code == 401
        rejected = client.post(
            uri, headers=as_user(first), json={"password": "wrong"}
        )
        assert rejected.status_code == 401
        assert "password" not in rejected.text.lower().replace("invalid current password", "")
        for token in (first, second):
            assert client.get("/v1/library/stats", headers=as_user(token)).status_code == 200
        accepted = client.post(
            uri, headers=as_user(first), json={"password": password}
        )
        assert accepted.status_code == 200
        assert accepted.json() == {"sessions_revoked": True}
        for token in (first, second):
            assert client.get("/v1/library/stats", headers=as_user(token)).status_code == 401
        assert client.post(uri, headers=as_user(first),
                           json={"password": password}).status_code == 401
        next_token = login(client, password)
        assert client.get("/v1/library/stats", headers=as_user(next_token)).status_code == 200


def test_revocation_persists_and_does_not_rotate_library_secret(tmp_path):
    password = "unchanged-strong-private-test-password"
    path = tmp_path / "data"
    with TestClient(create_app(Settings(path, password))) as client:
        token = login(client, password)
        outcome = client.post(
            "/v1/settings/revoke-sessions", headers=as_user(token),
            json={"password": password}
        )
        assert outcome.status_code == 200
    with TestClient(create_app(Settings(path, None))) as restarted:
        assert restarted.get(
            "/v1/assets", headers=as_user(token)
        ).status_code == 401
        assert login(restarted, password)
