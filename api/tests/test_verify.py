"""Read-only backup integrity verification, including adversarial archive contents."""
import hashlib
import io
import json
import sys
import tarfile

import pytest
from test_backup import seed_library

from app.backup import backup, main, restore, verify


def rewritten(src, dest, replacements=None, extras=None):
    replacements = replacements or {}
    extras = extras or {}
    with tarfile.open(src, "r:") as old, tarfile.open(dest, "w") as new:
        for member in old.getmembers():
            data = replacements.get(member.name)
            if data is None:
                stream = old.extractfile(member)
                assert stream is not None
                data = stream.read()
            info = tarfile.TarInfo(member.name)
            info.size = len(data)
            info.mode = 0o600
            new.addfile(info, io.BytesIO(data))
        for name, payload in extras.items():
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            new.addfile(info, io.BytesIO(payload))


def test_verification_success_and_cli_no_restore(tmp_path, monkeypatch, capsys):
    source = tmp_path / "lib"
    seed_library(source)
    archive = tmp_path / "backup.tar"
    backup(source, archive)
    expected = verify(archive)
    assert expected["verified"] is True
    assert expected["assets"] == 1
    assert expected["files"] == 3
    monkeypatch.setattr(sys, "argv", ["backup", "verify", "--input", str(archive)])
    main()
    assert json.loads(capsys.readouterr().out)["verified"] is True
    assert not (tmp_path / "restore").exists()


def test_verification_detects_tampered_media_without_writes(tmp_path):
    source = tmp_path / "lib"
    seed_library(source)
    archive = tmp_path / "backup.tar"
    backup(source, archive)
    with tarfile.open(archive) as inp:
        original = next(m.name for m in inp.getmembers() if m.name.startswith("objects/"))
    rewritten(archive, tmp_path / "bad.tar", {original: b"malicious media"})
    with pytest.raises(ValueError, match="Archive checksum mismatch"):
        verify(tmp_path / "bad.tar")
    assert not (tmp_path / "restore").exists()


def test_verification_rejects_orphan_indexed_archive_files(tmp_path):
    source = tmp_path / "lib"
    seed_library(source)
    archive = tmp_path / "backup.tar"
    backup(source, archive)
    extra = b"orphan, not indexed by SQLite"
    checksum = hashlib.sha256(extra).hexdigest()
    member = f"objects/{checksum[:2]}/{checksum}.png"
    with tarfile.open(archive) as inp:
        manifest = json.load(inp.extractfile("manifest.json"))
    manifest["sha256"][member] = checksum
    rewritten(
        archive, tmp_path / "bad-orphan.tar",
        {"manifest.json": json.dumps(manifest).encode()},
        {member: extra},
    )
    with pytest.raises(ValueError, match="not indexed"):
        verify(tmp_path / "bad-orphan.tar")


def test_verification_rejects_archive_traversal(tmp_path):
    evil = tmp_path / "evil.tar"
    with tarfile.open(evil, "w") as tar:
        payload = b"secret"
        info = tarfile.TarInfo("../escape")
        info.size = len(payload)
        tar.addfile(info, io.BytesIO(payload))
    with pytest.raises(ValueError):
        verify(evil)


def test_backup_cannot_write_through_symlink_parent_into_library(tmp_path):
    source = tmp_path / "lib"
    seed_library(source)
    link = tmp_path / "outside-looking-link"
    link.symlink_to(source, target_is_directory=True)
    with pytest.raises(ValueError, match="outside"):
        backup(source, link / "should-not-be-inside.tar")
    assert not (source / "should-not-be-inside.tar").exists()


def test_restore_rejects_unindexed_object_even_with_matching_manifest(tmp_path):
    source = tmp_path / "lib"
    seed_library(source)
    archive = tmp_path / "backup.tar"
    backup(source, archive)
    payload = b"orphan-file-that-does-not-belong-to-the-db"
    digest = hashlib.sha256(payload).hexdigest()
    name = f"objects/{digest[:2]}/{digest}.png"
    with tarfile.open(archive) as original:
        manifest = json.load(original.extractfile("manifest.json"))
    manifest["sha256"][name] = digest
    bad = tmp_path / "archive-with-orphan.tar"
    rewritten(archive, bad, {"manifest.json": json.dumps(manifest).encode()}, {name: payload})
    restored = tmp_path / "restored"
    with pytest.raises(ValueError, match="unindexed"):
        restore(bad, restored)
    assert not restored.exists()


def test_backup_refuses_symlinked_destination_parent_inside_library(tmp_path):
    source = tmp_path / "lib"
    seed_library(source)
    link = tmp_path / "private-link"
    link.symlink_to(source, target_is_directory=True)
    with pytest.raises(ValueError, match="outside"):
        backup(source, link / "oops.tar")
    assert not (source / "oops.tar").exists()


def test_verification_rejects_duplicate_members(tmp_path):
    archive = tmp_path / "repeated.tar"
    with tarfile.open(archive, "w") as out:
        for _ in range(2):
            payload = b"{}"
            info = tarfile.TarInfo("manifest.json")
            info.size = len(payload)
            out.addfile(info, io.BytesIO(payload))
    with pytest.raises(ValueError, match="duplicate"):
        verify(archive)
