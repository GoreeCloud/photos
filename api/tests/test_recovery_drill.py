"""Synthetic offline disaster-recovery rehearsal never touches the source library."""
import hashlib
import os
import tarfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from test_backup import seed_library

from app.backup import backup, drill, verify
from app.cli import main as cli_main
from app.main import Settings, create_app

PASSWORD = "a-long-private-test-password"


def test_temporary_recovery_drill_verifies_and_cleans_up_without_mutating_source(
    tmp_path: Path, capsys
):
    library = tmp_path / "live"
    asset_id, payload = seed_library(library)
    with TestClient(create_app(Settings(library, None))) as client:
        token = client.post("/v1/session", json={"password": PASSWORD}).json()["access_token"]
    archive = tmp_path / "test-archive.tar"
    backup(library, archive)
    previous = hashlib.sha256(archive.read_bytes()).hexdigest()
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    report = drill(archive, scratch)
    assert report["verified"] is True
    assert report["restored"] is True
    assert report["assets"] == 1
    assert report["original_bytes"] == len(payload)
    assert report["scratch_deleted_on_completion"] is True
    assert list(scratch.iterdir()) == []
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == previous
    assert verify(archive)["verified"] is True
    # A rehearsal must not revoke sessions or modify live originals.
    with TestClient(create_app(Settings(library, None))) as client:
        original = client.get(
            f"/v1/assets/{asset_id}/original",
            headers={"Authorization": "Bearer " + token},
        )
        assert original.status_code == 200
        assert original.content == payload
    assert cli_main(["drill-backup", "--input", str(archive),
                     "--scratch-parent", str(scratch)]) == 0
    assert '"verified": true' in capsys.readouterr().out.lower()
    assert list(scratch.iterdir()) == []


def test_bad_archive_rejected_without_leaving_scratch_artifacts(tmp_path):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    invalid = tmp_path / "broken.tar"
    invalid.write_bytes(b"untrusted, not an archive")
    with pytest.raises((tarfile.TarError, ValueError)):
        drill(invalid, scratch)
    assert list(scratch.iterdir()) == []


def test_drill_rejects_symlinked_archive_and_scratch_parent(tmp_path):
    library = tmp_path / "library"
    seed_library(library)
    archive = tmp_path / "snapshot.tar"
    backup(library, archive)
    symlink = tmp_path / "linked.tar"
    symlink.symlink_to(archive)
    with pytest.raises(ValueError, match="non-symlink"):
        drill(symlink)
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    shadow = tmp_path / "shadow"
    shadow.symlink_to(scratch, target_is_directory=True)
    with pytest.raises(ValueError, match="Scratch parent"):
        drill(archive, shadow)


def test_drill_reports_insufficient_scratch_capacity(tmp_path, monkeypatch):
    library = tmp_path / "library"
    seed_library(library)
    archive = tmp_path / "backup.tar"
    backup(library, archive)
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    info = os.statvfs(scratch)

    class NotEnoughSpace:
        free = 0

    from app import backup as backup_module
    monkeypatch.setattr(backup_module.shutil, "disk_usage", lambda parent: NotEnoughSpace())
    with pytest.raises(OSError, match="Insufficient"):
        drill(archive, scratch)
    assert list(scratch.iterdir()) == []
    assert info.f_bavail >= 0
