# GoreeCloud Photos

**GoreeCloud Photos** is an independently implemented, self-hosted, open-source photo and video library with a React web app, a native Qt Quick Linux app, and a native Kotlin/Jetpack Compose Android app.

**Status: 0.1 development foundation — not production-ready.** This repository is the canonical source for the service, all three first-party clients, deployment files, tests, and workflows. GoreeCloud Photos is neither Google Photos, Ente, nor Immich, and is not affiliated with them.

## What is implemented

| Capability | Server | Web | Linux | Android |
| --- | --- | --- | --- | --- |
| Local single-library password and temporary access token | Yes | Yes | Yes | Yes |
| Authenticated photo/video uploads | Yes | Yes | Yes | Yes |
| Private library listing | Yes | Yes | Yes | Yes |
| Image previews | Yes | Yes | Yes | Yes |
| Favorites | Yes | Yes | Yes | Yes |
| Reversible trash | Yes | Yes | Yes | Yes |
| Albums and membership | Yes | Yes | Planned | Planned |
| Filename search | Yes | Yes | Yes | Yes |
| Original download / viewing | Yes | Yes | Planned | Planned |
| Foreground, explicitly selected folder import with duplicate checks | Yes | N/A | N/A | Yes |
| Background camera roll backup | No | N/A | N/A | Planned with consent |
| E2EE / multi-user sharing / face recognition | No | No | No | No |

The server stores media as content-addressed objects, generating EXIF-stripped JPEG thumbnails for valid images. Authenticated clients can batch-check up to 100 SHA-256 digests with `POST /v1/assets/lookup` before explicit uploads; matches include trashed records and do not restore or upload anything. Uploads use streaming SHA-256 checks and size limits. Originals retain their metadata; previews do not. The API restricts all media endpoints with bearer authentication and accepts only recognized JPEG, PNG, WebP, GIF, and basic MP4 signatures. MP4 is **not** yet fully validated by a media decoder; treat imported media as untrusted. There is no automatic public sharing or telemetry.

## Quick start (private development)

1. Install Python 3.12+, [uv](https://docs.astral.sh/uv/) and Node.js 22+.
2. In `api/`, run `uv sync --group dev`.
3. Set a **unique** `PHOTOS_ADMIN_PASSWORD` of at least 12 characters in a local private shell environment. This value initializes the password hash on first run; on later launches the database's stored password hash is authoritative.
4. From `api/` run `uv run uvicorn app.main:app --factory --host 127.0.0.1 --port 8787`.
5. In `web/`, run `npm ci && npm run dev`. Browse to `http://127.0.0.1:5173`.

The React Vite development proxy forwards the media API to localhost:8787. For a production reverse proxy, serve the web bundle and forward `/v1` to the API under the same HTTPS origin. Set `VITE_PHOTOS_API_URL` at build time if using separate domains, and configure explicit `PHOTOS_CORS_ORIGINS` accordingly.

For a single-host container trial, run `docker compose up --build` with `PHOTOS_ADMIN_PASSWORD` set privately. Compose binds the API on **127.0.0.1:8787 only**; it does not expose a public web server or TLS. Do not publish the port without HTTPS and an access-controlled gateway.

### Linux app

From `linux/`, create a Python virtual environment, install `requirements.txt`, and run `python main.py --server http://127.0.0.1:8787`. Uses **Qt Quick 6.12** through PySide6; a remote server must use HTTPS. The source is native Qt Quick rather than an embedded browser or Electron wrapper.

### Android app

Open `android/` in Android Studio with JDK 17 and Android SDK 35, and build `app`. The app has **no** blanket storage permission: images and videos are selected explicitly through the Android document picker. For loopback development, use `adb reverse tcp:8787 tcp:8787` and its preconfigured loopback URL. Remote servers require valid HTTPS. No camera-roll background service runs without consent.

## Verification

```bash
cd api && uv sync --group dev && uv run pytest -q && uv run ruff check .
cd ../web && npm ci && npm run build
cd ../android && ./gradlew :app:assembleDebug
```

### Local backup and recovery

**Stop the Photos API and any uploading clients first.** From `api/`, run:

```bash
uv run --frozen python -m app.backup backup --data-dir /absolute/path/to/data --output /private/backups/photos.tar
uv run --frozen python -m app.backup verify --input /private/backups/photos.tar
uv run --frozen python -m app.backup restore --input /private/backups/photos.tar --data-dir /new/empty/photos-data
```

The backup includes a consistent SQLite snapshot, originals, thumbnails, and SHA-256 manifest. The separate read-only `verify` command checks media and the index without restoring. See [offline archive verification](api/BACKUP.md). Restore verifies archive member safety, checksums, database integrity and media hashes, and refuses an existing destination. The output tar is **unencrypted** and must be protected with disk encryption and restricted access; archive mode is 0600. This is a **manual offline tool**, not automatic backup scheduling, remote replication, a tested disaster-recovery strategy, or E2EE. See [security and operations](docs/SECURITY.md).

Refer to [security and operations](docs/SECURITY.md), [architecture](docs/ARCHITECTURE.md), [integration boundaries](docs/INTEGRATIONS.md), [third-party licenses](docs/THIRD_PARTY.md), [features](docs/FEATURES.md), [roadmap](docs/ROADMAP.md), and [objectives](docs/OBJECTIVES.md).

## Safety / known gaps

Not production-hardened: no end-to-end encryption, full MP4 decoding validation, automatic retention cleanup, remote backups, multi-user ACLs, full-text/image-content search, HEIC/RAW handling, advanced face recognition, background Android sync, or signed app distribution. Password rate limits persist in the single-library SQLite database across local workers and service restarts; still deploy a separate ingress limiter for public or shared reverse-proxy networks. A bearer token is not E2EE. SQLite targets one writable host; multiple replicas require a different persistence architecture. The first-run password and data volume must be backed up separately, with recovery validated.

## Roadmap

1. Preserve passing protected CI; complete real-device Android and Linux acceptance, encrypted restore drills, threat modeling and a supply-chain audit.
2. Privacy-first optional background backup (Android user consent, charging/Wi-Fi policy, resumable ingestion).
3. Database migrations, PostgreSQL and S3-compatible adapters, video transcoding and metadata indexing.
4. Multi-user family ACLs, encrypted-at-rest keys and optional client-side E2EE mode designed without misrepresenting server visibility.
5. Face/object search only as **opt-in**, local-only ML with clear consent, retention, provenance and deletion controls.

Contributions are welcome under the repository's MIT license; all reused third-party works retain their original license terms.
