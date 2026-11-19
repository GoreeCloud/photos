"""Opt-in private library storage bounds are transactional and non-destructive."""
import io
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import Settings, create_app, from_env

PASSWORD = "quota-test-password-2026"


def png(color: tuple[int, int, int]) -> bytes:
    result = io.BytesIO()
    Image.new("RGB", (15, 13), color).save(result, "PNG")
    return result.getvalue()


def auth(client):
    response = client.post("/v1/session", json={"password": PASSWORD})
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def upload(client, headers, data, filename):
    return client.post(
        "/v1/assets", headers=headers, files={"file": (filename, data, "image/png")},
    )


def test_quota_rejects_new_originals_without_deleting_existing_or_trashed(tmp_path):
    first = png((12, 32, 64))
    second = png((255, 30, 0))
    settings = Settings(tmp_path / "photos", PASSWORD, max_library_bytes=len(first) + len(second) - 1)
    with TestClient(create_app(settings)) as client:
        headers = auth(client)
        success = upload(client, headers, first, "first.png")
        assert success.status_code == 201, success.text
        asset_id = success.json()["id"]
        denied = upload(client, headers, second, "second.png")
        assert denied.status_code == 413
        assert "quota" in denied.text.lower()
        assert client.get("/v1/assets", headers=headers).json()["total"] == 1
        assert client.get(f"/v1/assets/{asset_id}/original", headers=headers).content == first
        assert client.delete(f"/v1/assets/{asset_id}", headers=headers).status_code == 204
        assert upload(client, headers, second, "second.png").status_code == 413
        assert client.post(f"/v1/assets/{asset_id}/restore", headers=headers).status_code == 200
        assert upload(client, headers, first, "first.png").status_code == 409
        stats = client.get("/v1/library/stats", headers=headers).json()
        assert stats["quota_bytes"] == len(first) + len(second) - 1
        assert stats["original_bytes"] == len(first)
        assert stats["remaining_bytes"] == len(second) - 1
        assert not list((settings.data_dir / "tmp").iterdir())
        assert len(list((settings.data_dir / "objects").rglob("*.png"))) == 1


def test_quota_cannot_be_bypassed_by_concurrent_distinct_uploads(tmp_path):
    first = png((10, 120, 20))
    second = png((20, 121, 40))
    settings = Settings(tmp_path / "photos", PASSWORD, max_library_bytes=max(len(first), len(second)))
    app = create_app(settings)
    with TestClient(app) as client:
        headers = auth(client)
    gate = Barrier(2)

    def attempt(item):
        with TestClient(app) as client:
            gate.wait(timeout=10)
            return upload(client, headers, item[0], item[1]).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = sorted(pool.map(attempt, [(first, "a.png"), (second, "b.png")]))
    assert outcomes == [201, 413]
    with TestClient(app) as client:
        assert client.get("/v1/assets", headers=headers).json()["total"] == 1


def test_tight_quota_does_not_modify_preexisting_library(tmp_path):
    root = tmp_path / "photos"
    existing = png((42, 42, 42))
    with TestClient(create_app(Settings(root, PASSWORD))) as client:
        headers = auth(client)
        created = upload(client, headers, existing, "original.png")
        assert created.status_code == 201
        asset_id = created.json()["id"]
    with TestClient(create_app(Settings(root, None, max_library_bytes=1))) as client:
        headers = auth(client)
        assert client.get(f"/v1/assets/{asset_id}/original", headers=headers).content == existing
        assert upload(client, headers, png((43, 43, 43)), "new.png").status_code == 413
        stats = client.get("/v1/library/stats", headers=headers).json()
        assert stats["remaining_bytes"] == 0
        assert stats["original_bytes"] == len(existing)


@pytest.mark.parametrize("value", ["bad", "-12", "0", "1.5"])
def test_invalid_quota_configuration_rejected(monkeypatch, value):
    monkeypatch.setenv("PHOTOS_MAX_LIBRARY_BYTES", value)
    with pytest.raises(RuntimeError, match="positive byte count"):
        from_env()


def test_settings_rejects_nonpositive_quota(tmp_path):
    with pytest.raises(ValueError, match="positive"):
        create_app(Settings(tmp_path / "data", PASSWORD, max_library_bytes=0))



def test_positive_quota_from_environment(monkeypatch):
    monkeypatch.setenv("PHOTOS_MAX_LIBRARY_BYTES", "123456")
    assert from_env().max_library_bytes == 123456
