"""Read-only offline integrity checks for the actual private media library."""
import json

import pytest
from test_backup import seed_library

from app import cli
from app.backup import verify_library


def test_live_library_verification_reports_counts_without_metadata(tmp_path, capsys):
    root = tmp_path / "photos"
    asset_id, payload = seed_library(root)
    database = root / "photos.sqlite3"
    original = next((root / "objects").rglob("*.png"))
    before = (database.stat().st_mtime_ns, original.stat().st_mtime_ns)
    result = verify_library(root)
    assert result == {
        "verified": True, "assets": 1, "original_bytes": len(payload),
        "previews": 1, "missing_previews": 0,
    }
    assert (database.stat().st_mtime_ns, original.stat().st_mtime_ns) == before
    assert asset_id not in str(result)
    assert "day.png" not in str(result)
    assert cli.main(["verify-library", "--data-dir", str(root)]) == 0
    assert json.loads(capsys.readouterr().out)["verified"] is True


def test_live_library_rejects_original_corruption(tmp_path):
    root = tmp_path / "photos"
    seed_library(root)
    original = next((root / "objects").rglob("*.png"))
    original.write_bytes(b"not-the-indexed-media")
    with pytest.raises(ValueError, match="checksum mismatch"):
        verify_library(root)


def test_live_library_rejects_missing_and_orphaned_originals(tmp_path):
    root = tmp_path / "photos"
    seed_library(root)
    original = next((root / "objects").rglob("*.png"))
    original.unlink()
    with pytest.raises(ValueError, match="missing or unsafe"):
        verify_library(root)
    original.write_bytes(b"not-the-indexed-media")
    with pytest.raises(ValueError, match="checksum"):
        verify_library(root)
    # Restore valid data via a second sample and check unindexed extra files.
    _, payload = seed_library(tmp_path / "other")
    original.write_bytes(payload)
    stray = original.parent / "leftover.tmp"
    stray.write_bytes(b"unexpected")
    with pytest.raises(ValueError, match="unindexed"):
        verify_library(root)


def test_live_library_reports_missing_reconstructible_previews(tmp_path):
    root = tmp_path / "photos"
    seed_library(root)
    thumbnail = next((root / "previews").glob("*.jpg"))
    thumbnail.unlink()
    result = verify_library(root)
    assert result["verified"] is True
    assert result["missing_previews"] == 1
    assert result["previews"] == 0


def test_live_library_rejects_symlinked_original(tmp_path):
    root = tmp_path / "photos"
    seed_library(root)
    original = next((root / "objects").rglob("*.png"))
    target = tmp_path / "outside.png"
    target.write_bytes(original.read_bytes())
    original.unlink()
    original.symlink_to(target)
    with pytest.raises(ValueError, match="missing or unsafe"):
        verify_library(root)
    assert target.is_file()


def test_live_library_nonexistent_or_missing_db(tmp_path):
    with pytest.raises(FileNotFoundError):
        verify_library(tmp_path / "not-here")
    (tmp_path / "empty").mkdir()
    with pytest.raises((FileNotFoundError, ValueError)):
        verify_library(tmp_path / "empty")



def test_live_library_rejects_unindexed_private_thumbnail(tmp_path):
    root = tmp_path / "photos"
    seed_library(root)
    orphan = root / "previews" / "extra.jpg"
    orphan.write_bytes(b"private stale thumbnail")
    with pytest.raises(ValueError, match="unindexed thumbnails"):
        verify_library(root)
    assert orphan.read_bytes() == b"private stale thumbnail"
