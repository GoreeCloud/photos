"""Adversarial but synthetic offline archive boundary and no-overwrite checks."""
import tarfile

import pytest
from test_backup import seed_library

from app import backup as offline


@pytest.fixture
def source(tmp_path):
    original = tmp_path / "private-library"
    seed_library(original)
    return original


def test_backup_refuses_member_count_unrestorable_by_verifier(source, tmp_path, monkeypatch):
    # Existing synthetic library: DB, original, thumbnail and manifest = 4.
    monkeypatch.setattr(offline, "MAX_ARCHIVE_FILES", 3)
    dest = tmp_path / "too-many-files.tar"
    with pytest.raises(ValueError, match="archive file count"):
        offline.backup(source, dest)
    assert not dest.exists()


def test_backup_refuses_member_and_total_sizes_above_restore_limits(
    source, tmp_path, monkeypatch
):
    too_big_member = tmp_path / "too-big-member.tar"
    monkeypatch.setattr(offline, "MAX_ARCHIVE_MEMBER_BYTES", 1024)
    with pytest.raises(ValueError, match="member size"):
        offline.backup(source, too_big_member)
    assert not too_big_member.exists()

    monkeypatch.setattr(offline, "MAX_ARCHIVE_MEMBER_BYTES", 4 * 1024**4)
    monkeypatch.setattr(offline, "MAX_ARCHIVE_TOTAL_BYTES", 1024)
    too_big_archive = tmp_path / "too-big-archive.tar"
    with pytest.raises(ValueError, match="archive total size"):
        offline.backup(source, too_big_archive)
    assert not too_big_archive.exists()


def test_restore_rejects_dangling_destination_symlink_without_replacing_it(
    source, tmp_path
):
    archive = tmp_path / "valid.tar"
    offline.backup(source, archive)
    destination = tmp_path / "dangling-restore"
    missing_target = tmp_path / "uncreated-place"
    destination.symlink_to(missing_target, target_is_directory=True)
    assert destination.is_symlink() and not destination.exists()
    with pytest.raises(FileExistsError, match="nonexistent"):
        offline.restore(archive, destination)
    assert destination.is_symlink()
    assert destination.readlink() == missing_target
    assert not missing_target.exists()


def test_restore_does_not_replace_destination_created_during_extraction(
    source, tmp_path, monkeypatch
):
    archive = tmp_path / "valid.tar"
    offline.backup(source, archive)
    destination = tmp_path / "late-created-directory"
    actual_integrity = offline.sqlite_integrity
    calls = 0

    def simulate_late_creation(path):
        nonlocal calls
        actual_integrity(path)
        calls += 1
        if calls == 2:
            destination.mkdir()

    monkeypatch.setattr(offline, "sqlite_integrity", simulate_late_creation)
    with pytest.raises(FileExistsError, match="appeared during extraction"):
        offline.restore(archive, destination)
    assert calls == 2
    assert destination.is_dir()
    assert list(destination.iterdir()) == []


def test_restore_rejects_negative_tar_member_size_before_extraction(
    source, tmp_path, monkeypatch
):
    archive = tmp_path / "valid.tar"
    offline.backup(source, archive)
    original_members = tarfile.TarFile.getmembers

    def tamper_metadata(tar):
        members = original_members(tar)
        for member in members:
            if member.name == "photos.sqlite3":
                member.size = -1
        return members

    monkeypatch.setattr(tarfile.TarFile, "getmembers", tamper_metadata)
    target = tmp_path / "must-not-restore"
    with pytest.raises(ValueError, match="Unsafe backup archive member"):
        offline.restore(archive, target)
    assert not target.exists()


@pytest.mark.skipif(offline.os.name != "posix", reason="POSIX directory promotion")
def test_restore_reserves_empty_directory_before_atomic_promotion(
    source, tmp_path, monkeypatch
):
    archive = tmp_path / "valid.tar"
    offline.backup(source, archive)
    destination = tmp_path / "restored"
    rename = offline.os.rename
    observed = []

    def check_reserved_directory(stage, target):
        if target == destination:
            assert destination.is_dir()
            assert not list(destination.iterdir())
            observed.append(destination)
        return rename(stage, target)

    monkeypatch.setattr(offline.os, "rename", check_reserved_directory)
    result = offline.restore(archive, destination)
    assert observed == [destination]
    assert result["assets"] == 1
    assert (destination / "photos.sqlite3").is_file()


@pytest.mark.skipif(offline.os.name != "posix", reason="POSIX directory promotion")
def test_failed_final_promotion_removes_only_our_empty_reservation(
    source, tmp_path, monkeypatch
):
    archive = tmp_path / "valid.tar"
    offline.backup(source, archive)
    destination = tmp_path / "not-restored"
    real_rename = offline.os.rename

    def fail_promotion(stage, target):
        if target == destination:
            assert destination.is_dir()
            raise OSError("injected promotion failure")
        return real_rename(stage, target)

    monkeypatch.setattr(offline.os, "rename", fail_promotion)
    with pytest.raises(OSError, match="injected promotion failure"):
        offline.restore(archive, destination)
    assert not destination.exists()


@pytest.mark.skipif(offline.os.name != "posix", reason="POSIX directory promotion")
def test_competing_writer_cannot_have_new_data_replaced_during_promotion(
    source, tmp_path, monkeypatch
):
    archive = tmp_path / "valid.tar"
    offline.backup(source, archive)
    destination = tmp_path / "occupied-after-reservation"
    actual_rename = offline.os.rename

    def race_with_writer(stage, target):
        if target == destination:
            (destination / "other-writer.txt").write_text("preserve me")
        return actual_rename(stage, target)

    monkeypatch.setattr(offline.os, "rename", race_with_writer)
    with pytest.raises(OSError):
        offline.restore(archive, destination)
    assert (destination / "other-writer.txt").read_text() == "preserve me"
    assert not (destination / "photos.sqlite3").exists()
