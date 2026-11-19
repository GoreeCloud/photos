"""Unicode inputs to password rotation remain supported without comparison errors."""
from fastapi.testclient import TestClient

from app.main import Settings, create_app


def test_password_rotation_unicode_passphrases(tmp_path):
    old = b"private-\\u00e9l\\u00e9phant-2026".decode("unicode_escape")
    new = b"second-\\u00e9l\\u00e9phant-2026".decode("unicode_escape")
    with TestClient(create_app(Settings(tmp_path / "library", old))) as client:
        login = client.post("/v1/session", json={"password": old})
        assert login.status_code == 200, login.text
        headers = {"Authorization": "Bearer " + login.json()["access_token"]}
        changed = client.post(
            "/v1/settings/password",
            headers=headers,
            json={"current_password": old, "new_password": new},
        )
        assert changed.status_code == 200, changed.text
        assert client.get("/v1/assets", headers=headers).status_code == 401
        assert client.post("/v1/session", json={"password": new}).status_code == 200
