# Offline archive verification

From `api/`, stop all Photos API writers before making a backup:

```sh
uv run --frozen python -m app.backup backup --data-dir /absolute/private/photos-data --output /encrypted-disk/photos.tar
uv run --frozen python -m app.backup verify --input /encrypted-disk/photos.tar
uv run --frozen python -m app.backup restore --input /encrypted-disk/photos.tar --data-dir /new/nonexistent/photos-restored
```

**Security model:** These local tar archives are *unencrypted*. The output is created with mode `0600` and is never overwritten. Archive creation rejects symlinks escaping the library and refuses destinations resolving inside it. The `verify` command does not restore any files: it streams each member through SHA-256 and temporarily copies only SQLite into a private scratch directory so the index can be inspected. It rejects traversal, non-regular entries, duplicate names, absent manifest members, unsupported manifest formats, extra unindexed objects, missing objects, media hash mismatches and invalid databases. Restore performs its own safe checks, rejects even dangling symlink destinations, checks again before promotion, and on POSIX reserves the new destination with an exclusive private directory before atomically moving the verified library into it. Archives are rejected at creation if their file count, individual member sizes or total member bytes would exceed the verifier/restore bounds; the tool must never create a backup it cannot read itself. On Windows, use a trusted private directory and prevent competing writers during restoration; this is not a hostile-local-process or multi-writer recovery service.

**Limitations:** Local verification does **not** establish that the source library was offline when copied, that the tar is confidential, that an off-site copy exists, that encryption keys are recoverable, that the host hardware is healthy or that a full-size disaster recovery drill has succeeded. Backups are still intentionally manual. Keep an independent encrypted copy on another device/medium, practice isolated restoration, and verify recoverability before production. Do not add unattended schedules or external uploads without explicit user configuration and secure consent.


## Read-only live library audit

While the API and all clients are **stopped**, use `python -m app.backup verify-library --data-dir /private/photos-data` or `photosctl verify-library --data-dir /private/photos-data`. This verifies SQLite integrity, indexed original SHA-256 checksums, missing originals, unexpected original files, unsafe symlinks and orphaned previews. Missing thumbnails are reported as reconstructible omissions. The audit makes no modifications, must not be run against a changing library for reliable results, and is not a substitute for an encrypted backup with tested off-host restoration.
