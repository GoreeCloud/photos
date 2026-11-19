import io
import json
import tarfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.backup import backup, restore
from app.main import Settings, create_app


def sample_image() -> bytes:
    out = io.BytesIO()
    Image.new("RGB", (12, 10), (30, 80, 130)).save(out, format="PNG")
    return out.getvalue()


def seed_library(path: Path) -> tuple[str, bytes]:
    with TestClient(create_app(Settings(path, "a-long-private-test-password"))) as c:
        login = c.post("/v1/session", json={"password": "a-long-private-test-password"})
        auth = {"Authorization": "Bearer " + login.json()["access_token"]}
        payload = sample_image()
        uploaded = c.post(
            "/v1/assets", headers=auth, files={"file": ("day.png", payload, "image/png")}
        )
        assert uploaded.status_code == 201, uploaded.text
        asset_id = uploaded.json()["id"]
        album = c.post("/v1/albums", headers=auth, json={"name": "Vacation"}).json()["id"]
        c.post(f"/v1/albums/{album}/assets/{asset_id}", headers=auth)
        c.patch(f"/v1/assets/{asset_id}/favorite", headers=auth, json={"favorite": True})
        return asset_id, payload


def test_backup_restore_roundtrip(tmp_path):
    source = tmp_path / "photos-original"
    asset_id, payload = seed_library(source)
    archive = tmp_path / "photos-private.tar"
    data = backup(source, archive)
    assert data["assets"] == 1
    assert archive.stat().st_mode & 0o777 == 0o600
    with tarfile.open(archive) as tar:
        manifest = json.load(tar.extractfile("manifest.json"))
        assert manifest["format_version"] == 1
        assert len(manifest["sha256"]) == 3  # DB, original, preview
    new_home = tmp_path / "photos-restored"
    result = restore(archive, new_home)
    assert result["assets"] == 1
    assert new_home.stat().st_mode & 0o777 == 0o700
    with TestClient(create_app(Settings(new_home, None))) as c:
        login = c.post("/v1/session", json={"password": "a-long-private-test-password"})
        assert login.status_code == 200
        auth = {"Authorization": "Bearer " + login.json()["access_token"]}
        assert c.get("/v1/assets?favorite=true", headers=auth).json()["total"] == 1
        assert c.get("/v1/albums", headers=auth).json()["items"][0]["name"] == "Vacation"
        assert c.get(f"/v1/assets/{asset_id}/original", headers=auth).content == payload
    with pytest.raises(FileExistsError):
        restore(archive, new_home)


def test_corrupt_original_rejected(tmp_path):
    source = tmp_path / "photos"
    seed_library(source)
    media = next((source / "objects").rglob("*.png"))
    media.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="Corrupted original"):
        backup(source, tmp_path / "bad.tar")
    assert not (tmp_path / "bad.tar").exists()


def test_restore_rejects_traversal(tmp_path):
    archive = tmp_path / "evil.tar"
    with tarfile.open(archive, "w") as tar:
        payload = b"oops"
        info = tarfile.TarInfo("../escaped")
        info.size = len(payload)
        tar.addfile(info, io.BytesIO(payload))
    with pytest.raises(ValueError):
        restore(archive, tmp_path / "restored")
    assert not (tmp_path / "restored").exists()
    assert not (tmp_path / "escaped").exists()


def test_existing_archive_not_overwritten(tmp_path):
    source = tmp_path / "photos"
    seed_library(source)
    archive = tmp_path / "existing.tar"
    archive.write_bytes(b"keep")
    with pytest.raises(FileExistsError):
        backup(source, archive)
    assert archive.read_bytes() == b"keep"
