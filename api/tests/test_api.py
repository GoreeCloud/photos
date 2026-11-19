import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import Settings, create_app

PASS = "this-is-a-long-local-test-password"


def png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), color=(10, 20, 30)).save(buffer, format="PNG")
    return buffer.getvalue()


def client(tmp_path):
    return TestClient(create_app(Settings(tmp_path / "library", PASS)))


def token(client):
    response = client.post("/v1/session", json={"password": PASS})
    assert response.status_code == 200, response.text
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def test_first_launch_requires_secret(tmp_path):
    import pytest
    with pytest.raises(RuntimeError):
        create_app(Settings(tmp_path / "unset", None))


def test_auth_lifecycle_and_storage(tmp_path):
    c = client(tmp_path)
    assert c.get("/health").json()["status"] == "ok"
    assert c.get("/v1/assets").status_code == 401
    assert c.post("/v1/session", json={"password": "wrong"}).status_code == 401
    headers = token(c)
    payload = png()
    uploaded = c.post("/v1/assets", headers=headers,
                      files={"file": ("../../family.png", payload, "application/octet-stream")})
    assert uploaded.status_code == 201, uploaded.text
    asset_id = uploaded.json()["id"]
    assert c.post("/v1/assets", headers=headers,
                  files={"file": ("duplicate.png", payload, "image/png")}).status_code == 409
    records = c.get("/v1/assets", headers=headers).json()
    assert records["total"] == 1
    assert records["items"][0]["filename"] == "family.png"
    assert c.get(f"/v1/assets/{asset_id}/thumbnail", headers=headers).status_code == 200
    got = c.get(f"/v1/assets/{asset_id}/original", headers={**headers, "Range": "bytes=0-7"})
    assert got.status_code == 206
    assert got.content == payload[:8]
    assert c.patch(f"/v1/assets/{asset_id}/favorite", headers=headers,
                   json={"favorite": True}).json()["favorite"] is True
    assert c.get("/v1/assets?favorite=true", headers=headers).json()["total"] == 1
    album_id = c.post("/v1/albums", headers=headers, json={"name": "Family"}).json()["id"]
    assert c.post(f"/v1/albums/{album_id}/assets/{asset_id}", headers=headers).status_code == 200
    assert c.get(f"/v1/albums/{album_id}/assets", headers=headers).json()["total"] == 1
    assert c.delete(f"/v1/assets/{asset_id}", headers=headers).status_code == 204
    assert c.get("/v1/assets", headers=headers).json()["total"] == 0
    assert c.get("/v1/assets?trashed=true", headers=headers).json()["total"] == 1
    assert c.get(f"/v1/assets/{asset_id}/original", headers=headers).status_code == 404
    assert c.post(f"/v1/assets/{asset_id}/restore", headers=headers).status_code == 200
    assert c.get("/v1/assets", headers=headers).json()["total"] == 1
    assert c.delete("/v1/session", headers=headers).status_code == 204
    assert c.get("/v1/assets", headers=headers).status_code == 401


def test_invalid_file_and_ranges(tmp_path):
    c = client(tmp_path)
    headers = token(c)
    assert c.post("/v1/assets", headers=headers,
                  files={"file": ("bad.jpg", b"not a JPEG", "image/jpeg")}).status_code == 415
    aid = c.post("/v1/assets", headers=headers,
                 files={"file": ("ok.png", png(), "image/png")}).json()["id"]
    r = c.get(f"/v1/assets/{aid}/original", headers={**headers, "Range": "bytes=9999-"})
    assert r.status_code == 416
    assert c.get("/v1/assets?search=%25", headers=headers).json()["total"] == 0


def test_password_survives_restart(tmp_path):
    settings = Settings(tmp_path / "library", PASS)
    with TestClient(create_app(settings)) as first:
        assert first.post("/v1/session", json={"password": PASS}).status_code == 200
    with TestClient(create_app(Settings(settings.data_dir, None))) as restarted:
        assert restarted.post("/v1/session", json={"password": PASS}).status_code == 200
