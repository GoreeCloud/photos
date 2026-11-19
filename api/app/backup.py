"""Offline, local-only backup/restore for a single GoreeCloud Photos library.

Archives are NOT encrypted. Stop the API and all writers before running backup.
Restore creates a NEW empty directory and refuses untrusted archive members.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sqlite3
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

EXT = {
    "image/jpeg": ".jpg", "image/png": ".png",
    "image/webp": ".webp", "image/gif": ".gif", "video/mp4": ".mp4",
}
MAX_ARCHIVE_MEMBER_BYTES = 4 * 1024**4
MAX_MANIFEST_BYTES = 64 * 1024 * 1024
CHUNK = 1024 * 1024
SHA256 = re.compile(r"[0-9a-f]{64}")


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(CHUNK):
            h.update(chunk)
    return h.hexdigest()


def sqlite_integrity(path: Path) -> None:
    with sqlite3.connect(f"file:{path.as_uri()[7:]}?mode=ro", uri=True) as db:
        result = db.execute("PRAGMA quick_check").fetchone()
        if result != ("ok",):
            raise ValueError("Database integrity check failed")


def expected_objects(db_path: Path) -> tuple[list[str], list[str]]:
    originals: list[str] = []
    previews: list[str] = []
    with sqlite3.connect(f"file:{db_path.as_uri()[7:]}?mode=ro", uri=True) as db:
        for asset_id, sha, media in db.execute(
            "SELECT id, sha256, media_type FROM assets ORDER BY sha256"
        ):
            if not SHA256.fullmatch(sha) or media not in EXT:
                raise ValueError("Invalid asset metadata")
            originals.append(f"objects/{sha[:2]}/{sha}{EXT[media]}")
            if media.startswith("image/"):
                if not re.fullmatch(r"[0-9a-f-]{36}", asset_id):
                    raise ValueError("Invalid asset identifier")
                previews.append(f"previews/{asset_id}.jpg")
    return originals, previews


def safe_file(root: Path, rel: str) -> Path:
    if not acceptable_name(rel):
        raise ValueError("Invalid backup file path")
    path = root / rel
    if any(part.is_symlink() for part in [path, *path.parents] if part != root and root in part.parents):
        raise ValueError("Symlinks in library are not allowed")
    if not path.resolve(strict=True).is_relative_to(root.resolve()):
        raise ValueError("Library path escapes root")
    if not path.is_file():
        raise ValueError("Library member is not a file")
    return path


def acceptable_name(name: str) -> bool:
    parts = PurePosixPath(name).parts
    if name in {"photos.sqlite3", "manifest.json"}:
        return True
    if len(parts) == 3 and parts[0] == "objects":
        prefix, file = parts[1:]
        match = re.fullmatch(r"([0-9a-f]{64})(\.jpg|\.png|\.gif|\.webp|\.mp4)", file)
        return bool(match and prefix == match.group(1)[:2])
    if len(parts) == 2 and parts[0] == "previews":
        return bool(re.fullmatch(r"[0-9a-f-]{36}\.jpg", parts[1]))
    return False


def add_file(tar: tarfile.TarFile, path: Path, member_name: str) -> None:
    with path.open("rb") as handle:
        meta = tarfile.TarInfo(member_name)
        meta.size = path.stat().st_size
        meta.mode = 0o600
        meta.mtime = 0
        tar.addfile(meta, handle)


def verify_library(data_dir: Path) -> dict:
    """Read-only offline check of indexed originals and private library structure.

    Stop API writers first. A single SQLite read-only scan cannot guarantee a
    cross-file snapshot while uploads or deletes are concurrently in progress.
    Do not mutate, delete or silently recover any library file.
    """
    root = data_dir.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Library path is not a directory")
    db_file = safe_file(root, "photos.sqlite3")
    sqlite_integrity(db_file)
    originals, previews = expected_objects(db_file)
    if len(originals) > MAX_ARCHIVE_FILES:
        raise ValueError("Library contains too many indexed originals")
    total_bytes = 0
    expected = set(originals)
    for rel in originals:
        try:
            media = safe_file(root, rel)
        except (OSError, ValueError) as error:
            raise ValueError("Indexed original is missing or unsafe") from error
        if digest_file(media) != PurePosixPath(rel).name[:64]:
            raise ValueError("Indexed original checksum mismatch")
        total_bytes += media.stat().st_size
    # Leftover unindexed content may indicate interrupted uploads, storage drift,
    # or deletion outside the API. Report without deleting or exposing filenames.
    objects_dir = root / "objects"
    if objects_dir.is_symlink() or not objects_dir.is_dir():
        raise ValueError("Original media directory is unsafe or missing")
    count = 0
    for entry in objects_dir.rglob("*"):
        if entry.is_symlink():
            raise ValueError("Library contains unsafe media symlinks")
        if entry.is_file():
            count += 1
            if count > MAX_ARCHIVE_FILES:
                raise ValueError("Library contains too many original objects")
            if entry.relative_to(root).as_posix() not in expected:
                raise ValueError("Library contains unindexed original files")
    if count != len(expected):
        raise ValueError("Library media index and objects do not match")
    previews_dir = root / "previews"
    if previews_dir.is_symlink() or not previews_dir.is_dir():
        raise ValueError("Thumbnail directory is unsafe or missing")
    preview_count = 0
    expected_previews = set(previews)
    for entry in previews_dir.rglob("*"):
        if entry.is_symlink():
            raise ValueError("Library contains unsafe thumbnail symlinks")
        if entry.is_file() and entry.relative_to(root).as_posix() not in expected_previews:
            raise ValueError("Library contains unindexed thumbnails")
    for rel in previews:
        thumbnail = root / rel
        if thumbnail.is_symlink():
            raise ValueError("Library contains unsafe thumbnail symlinks")
        if thumbnail.exists():
            safe_file(root, rel)
            preview_count += 1
    return {
        "verified": True,
        "assets": len(originals),
        "original_bytes": total_bytes,
        "previews": preview_count,
        "missing_previews": len(previews) - preview_count,
    }


def backup(data_dir: Path, output: Path) -> dict:
    root = data_dir.resolve(strict=True)
    target = output.absolute()
    if not target.parent.is_dir():
        raise FileNotFoundError("Backup destination parent does not exist")
    # Canonicalize a symlinked destination parent before comparing with the library.
    # Never permit the supposed off-library archive to resolve into live media.
    target = target.parent.resolve(strict=True) / target.name
    if target.exists() or target.is_symlink():
        raise FileExistsError("Backup destination already exists")
    if target.is_relative_to(root):
        raise ValueError("Save backups outside the live photo library")
    db_path = safe_file(root, "photos.sqlite3")

    # Do not claim a live cross-file snapshot; the caller must stop API writers.
    with tempfile.TemporaryDirectory(prefix=".photos-snapshot-", dir=target.parent) as temp:
        snap = Path(temp) / "photos.sqlite3"
        with sqlite3.connect(db_path) as source, sqlite3.connect(snap) as destination:
            source.backup(destination)
        sqlite_integrity(snap)
        originals, previews = expected_objects(snap)
        files = {"photos.sqlite3": snap}
        for rel in originals:
            path = safe_file(root, rel)
            actual = digest_file(path)
            if actual != PurePosixPath(rel).name[:64]:
                raise ValueError(f"Corrupted original: {rel}")
            files[rel] = path
        for rel in previews:
            path = root / rel
            if path.exists():
                files[rel] = safe_file(root, rel)
        checksums = {rel: digest_file(path) for rel, path in files.items()}
        manifest = json.dumps(
            {"format_version": 1, "sha256": checksums},
            sort_keys=True, separators=(",", ":")
        ).encode()
        if len(manifest) > MAX_MANIFEST_BYTES:
            raise ValueError("Backup manifest exceeds supported size")
        temp_archive: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w+b", prefix=".photos-archive-", dir=target.parent, delete=False
            ) as handle:
                temp_archive = Path(handle.name)
                os.fchmod(handle.fileno(), 0o600)
                with tarfile.open(fileobj=handle, mode="w") as tar:
                    for rel, file in sorted(files.items()):
                        add_file(tar, file, rel)
                    meta = tarfile.TarInfo("manifest.json")
                    meta.size = len(manifest)
                    meta.mode = 0o600
                    tar.addfile(meta, io.BytesIO(manifest))
                handle.flush()
                os.fsync(handle.fileno())
            # Link instead of replace: never overwrite an existing backup.
            os.link(temp_archive, target)
        finally:
            if temp_archive:
                temp_archive.unlink(missing_ok=True)
        return {"files": len(files), "assets": len(originals), "archive": str(target)}


MAX_ARCHIVE_FILES = 200_000
MAX_ARCHIVE_TOTAL_BYTES = 16 * 1024**4


def verify(archive: Path) -> dict:
    """Read-only manifest, database and media verification. No restore is performed.

    Archive input is untrusted. This checks path confinement, unique names, file
    types, byte bounds, SHA-256, SQLite integrity, and indexed-original coverage.
    The only local write is a temporary private copy of the archived SQLite DB.
    """
    with tarfile.open(archive, mode="r:") as tar:
        members = tar.getmembers()
        if len(members) > MAX_ARCHIVE_FILES:
            raise ValueError("Archive contains too many files")
        names = [m.name for m in members]
        if (len(set(names)) != len(names)
                or "manifest.json" not in names or "photos.sqlite3" not in names):
            raise ValueError("Missing or duplicate required archive members")
        if sum(m.size for m in members) > MAX_ARCHIVE_TOTAL_BYTES:
            raise ValueError("Archive exceeds total size limit")
        for member in members:
            if not member.isfile() or not acceptable_name(member.name):
                raise ValueError("Unsafe backup archive member")
            if member.size < 0 or member.size > MAX_ARCHIVE_MEMBER_BYTES:
                raise ValueError("Backup member exceeds file size limit")
        manifest_member = tar.getmember("manifest.json")
        if manifest_member.size > MAX_MANIFEST_BYTES:
            raise ValueError("Manifest exceeds size limit")
        manifest_stream = tar.extractfile(manifest_member)
        if manifest_stream is None:
            raise ValueError("Missing manifest content")
        with manifest_stream:
            manifest = json.load(manifest_stream)
        if not isinstance(manifest, dict) or manifest.get("format_version") != 1:
            raise ValueError("Unsupported backup format")
        checksums = manifest.get("sha256")
        if not isinstance(checksums, dict) or set(checksums) != set(names) - {"manifest.json"}:
            raise ValueError("Manifest does not match archive contents")
        if any(not isinstance(digest, str) or not SHA256.fullmatch(digest)
               for digest in checksums.values()):
            raise ValueError("Invalid manifest SHA-256")
        with tempfile.TemporaryDirectory(prefix=".photos-verify-") as temp:
            snapshot = Path(temp) / "photos.sqlite3"
            for member in members:
                if member.name == "manifest.json":
                    continue
                stream = tar.extractfile(member)
                if stream is None:
                    raise ValueError("Unreadable archive member")
                digest = hashlib.sha256()
                with stream:
                    if member.name == "photos.sqlite3":
                        with snapshot.open("xb") as destination:
                            os.chmod(snapshot, 0o600)
                            while chunk := stream.read(CHUNK):
                                digest.update(chunk)
                                destination.write(chunk)
                    else:
                        while chunk := stream.read(CHUNK):
                            digest.update(chunk)
                if digest.hexdigest() != checksums[member.name]:
                    raise ValueError(f"Archive checksum mismatch: {member.name}")
                if member.name.startswith("objects/") and (
                    digest.hexdigest() != PurePosixPath(member.name).name[:64]
                ):
                    raise ValueError(f"Indexed original content mismatch: {member.name}")
            sqlite_integrity(snapshot)
            originals, previews = expected_objects(snapshot)
            required = {"photos.sqlite3", *originals}
            actual = set(checksums)
            if not required.issubset(actual):
                raise ValueError("Archive missing indexed media originals")
            if actual - required - set(previews):
                raise ValueError("Archive contains media not indexed by SQLite")
        return {
            "verified": True, "assets": len(originals),
            "files": len(checksums), "archive": str(archive),
        }


def restore(archive: Path, data_dir: Path) -> dict:
    target = data_dir.absolute()
    if target.exists():
        raise FileExistsError("Restore requires a new, nonexistent data directory")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, mode="r:") as tar:
        members = tar.getmembers()
        if len(members) > MAX_ARCHIVE_FILES or sum(m.size for m in members) > MAX_ARCHIVE_TOTAL_BYTES:
            raise ValueError("Archive exceeds file count or total size limit")
        names = [m.name for m in members]
        if len(set(names)) != len(names) or "manifest.json" not in names or "photos.sqlite3" not in names:
            raise ValueError("Incomplete or duplicate archive members")
        for m in members:
            if not m.isfile() or not acceptable_name(m.name) or m.size > MAX_ARCHIVE_MEMBER_BYTES:
                raise ValueError("Unsafe backup archive member")
        manifest_member = tar.getmember("manifest.json")
        if manifest_member.size > MAX_MANIFEST_BYTES:
            raise ValueError("Manifest exceeds limit")
        manifest_file = tar.extractfile(manifest_member)
        if manifest_file is None:
            raise ValueError("Missing manifest")
        manifest = json.load(manifest_file)
        checksums = manifest.get("sha256") if isinstance(manifest, dict) else None
        if not isinstance(manifest, dict) or manifest.get("format_version") != 1 or not isinstance(checksums, dict):
            raise ValueError("Unsupported backup manifest")
        if set(checksums) != set(names) - {"manifest.json"}:
            raise ValueError("Manifest does not cover every archive file")
        for checksum in checksums.values():
            if not isinstance(checksum, str) or not SHA256.fullmatch(checksum):
                raise ValueError("Invalid archive checksum")

        with tempfile.TemporaryDirectory(prefix=".photos-restore-", dir=target.parent) as temp:
            stage = Path(temp) / "library"
            stage.mkdir(mode=0o700)
            for m in members:
                if m.name == "manifest.json":
                    continue
                dest = stage / m.name
                dest.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                source = tar.extractfile(m)
                if source is None:
                    raise ValueError("Unreadable archive member")
                h = hashlib.sha256()
                with dest.open("xb") as out, source:
                    while block := source.read(CHUNK):
                        h.update(block)
                        out.write(block)
                    out.flush()
                    os.fsync(out.fileno())
                dest.chmod(0o600)
                if h.hexdigest() != checksums[m.name]:
                    raise ValueError(f"Backup checksum mismatch: {m.name}")
            sqlite_integrity(stage / "photos.sqlite3")
            originals, previews = expected_objects(stage / "photos.sqlite3")
            if any(rel not in checksums for rel in originals):
                raise ValueError("Backup missing indexed originals")
            allowed = {"photos.sqlite3", *originals, *previews}
            if set(checksums) - allowed:
                raise ValueError("Archive contains unindexed media")
            for rel in originals:
                if digest_file(stage / rel) != PurePosixPath(rel).name[:64]:
                    raise ValueError("Restored original hash mismatch")
            os.rename(stage, target)
            return {"files": len(checksums), "assets": len(originals), "restored_to": str(target)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline private GoreeCloud Photos backup utility")
    sub = parser.add_subparsers(dest="command", required=True)
    archive = sub.add_parser("backup", help="Stop the API first; export local unencrypted tar")
    archive.add_argument("--data-dir", type=Path, required=True)
    archive.add_argument("--output", type=Path, required=True)
    live_check = sub.add_parser("verify-library", help="Check a stopped local library, read-only")
    live_check.add_argument("--data-dir", type=Path, required=True)
    check = sub.add_parser("verify", help="Verify checksums, SQLite index and media without restoring")
    check.add_argument("--input", type=Path, required=True)
    recover = sub.add_parser("restore", help="Restore to a new empty directory")
    recover.add_argument("--input", type=Path, required=True)
    recover.add_argument("--data-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "backup":
        result = backup(args.data_dir, args.output)
    elif args.command == "verify-library":
        result = verify_library(args.data_dir)
    elif args.command == "verify":
        result = verify(args.input)
    else:
        result = restore(args.input, args.data_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
