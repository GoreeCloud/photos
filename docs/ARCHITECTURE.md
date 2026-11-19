# Architecture

```text
React web app ─┐
Qt Quick Linux ├── HTTPS /v1 ── FastAPI ── SQLite metadata/sessions
Compose Android┘                 ├── /data/objects/xx/<sha256>.<ext>
                                └── /data/previews/<asset-id>.jpg
```

## Implemented
- **Web**: React 19, TypeScript, Vite 7; responsive gallery, in-memory bearer token, multipart uploads, authenticated thumbnail fetch and object-URL cleanup.
- **Linux**: PySide6 6.12 / Qt Quick with asynchronous QNetworkAccessManager, photo picker, password session, grid preview provider, favorites and trash.
- **Android**: Kotlin, Jetpack Compose and Android document picker; explicit foreground uploads; HTTP(S) library API; image decode only after authenticated thumbnail download.
- **Service**: FastAPI, scrypt credential bootstrap, short-lived bearer sessions, per-process login limiter, media magic-byte checks, Pillow preview generation, SQLite WAL-ready single-writer metadata.
- **Storage**: content-addressable SHA-256 media objects; image previews stored separately with EXIF stripped; soft deletion and album joins. The offline manual backup CLI uses SQLite's consistent backup interface plus verified originals, checksums, and safe archive restore to a new data directory.
- **Data scope**: a single library; the first user is a local bootstrap credential, not an IdP with groups, RBAC, or delegated access.

## Explicitly deferred
- PostgreSQL+S3 abstractions and object-store verification.
- Resumable, chunked, background and offline sync.
- Advanced video validation/transcoding and thumbnail worker queue.
- Robust EXIF capture-time indexing, geolocation and maps.
- Client-side E2EE / family sharing / user-level access controls.
- Search over visually inferred content, face groups and duplicate ranking.
- Application signing, release distribution, OCI image SBOM, and automatic backup/restore.

**Compatibility direction:** use the stable JSON over HTTPS API for clients. Changes to object metadata require migrations; do not unilaterally reinterpret existing hashes. Test encrypted vault migration separately before marketing E2EE.

## API summary
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Health status, no sensitive details |
| POST/DELETE | `/v1/session` | Log in and revoke |
| GET/POST | `/v1/assets` | List/upload |
| POST | `/v1/assets/lookup` | Authenticated SHA-256 duplicate preflight (max 100 hashes; reports trashed matches without restoring) |
| GET | `/v1/assets/{id}/thumbnail` | Private image preview |
| GET | `/v1/assets/{id}/original` | Private media stream with byte ranges |
| PATCH/POST | `/v1/assets/{id}/favorite` | Set favorite |
| DELETE | `/v1/assets/{id}` | Soft delete |
| POST | `/v1/assets/{id}/restore` | Restore |
| GET/POST | `/v1/albums` | List/create |
| GET | `/v1/albums/{id}/assets` | List album items |
| POST | `/v1/albums/{id}/assets/{assetId}` | Add item |
