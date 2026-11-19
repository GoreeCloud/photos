"""Duplicate preflight never bypasses private access or file validation."""
import hashlib
import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import Settings, create_app


def test_authenticated_preflight_and_trash(tmp_path):
    buffer = io.BytesIO()
    Image.new("RGB", (12, 10), color=(10, 20, 30)).save(buffer, "PNG")
    payload = buffer.getvalue()
    digest = hashlib.sha256(payload).hexdigest()
    other = "0" * 64
    with TestClient(create_app(Settings(tmp_path / "photos", "super-long-testing-password"))) as client:
        uri = "/v1/assets/lookup"
        assert client.post(uri, json={"hashes": [digest]}).status_code == 401
        token = client.post("/v1/session", json={"password": "super-long-testing-password"}).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        assert client.post(uri, headers=headers, json={"hashes": [digest]}).json() == {"existing": []}
        created = client.post(
            "/v1/assets", files={"file": ("test.png", payload, "image/png")}, headers=headers
        )
        assert created.status_code == 201
        item_id = created.json()["id"]
        records = client.post(uri, headers=headers, json={"hashes": [digest, other, digest]})
        assert records.status_code == 200
        assert records.json() == {
            "existing": [{"sha256": digest, "id": item_id, "trashed": False}]
        }
        assert client.post(uri, headers=headers, json={"hashes": [digest.upper()]}).status_code == 422
        assert client.post(uri, headers=headers, json={"hashes": []}).status_code == 422
        assert client.post(uri, headers=headers, json={"hashes": [other] * 101}).status_code == 422
        assert client.post(uri, headers=headers, json={"hashes": ["../../etc/passwd"]}).status_code == 422
        assert client.delete(f"/v1/assets/{item_id}", headers=headers).status_code == 204
        trashed = client.post(uri, headers=headers, json={"hashes": [digest]}).json()
        assert trashed["existing"][0]["trashed"] is True
        assert client.get(f"/v1/assets/{item_id}/original", headers=headers).status_code == 404
        assert client.post("/v1/session", json={"password": "wrong"}).status_code == 401
