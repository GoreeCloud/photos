# Security and operations

## Trust boundaries
- **GoreeShield (privacy):** no telemetry, no automatic photo access, no consent-free face analysis, private thumbnails, metadata preservation only in authenticated originals.
- **Wardveil (cybersecurity):** strict file limits, signature checks for limited formats, secure session tokens, HTTP-only loopback, TLS for remote clients, no world-readable objects.
- **GoreeCloud Identity:** future integration contract. This first version has **one library credential**, not an implemented GoreeCloud Identity SSO integration or family RBAC.
- **GoreeCloud Mesh:** future opt-in events and sync; no implicit network sharing.
- **GoreeCloud UI:** uses a pinned canonical token CSS snapshot from `gc-ui` for web. Native clients require independent visual/accessibility QA.

## Data model and backup
Persistent state is `PHOTOS_DATA_DIR/photos.sqlite3`, `objects/` and `previews/`. Store the entire directory on a private encrypted host volume when possible. Stop writes, take a consistent SQLite backup using `sqlite3.Connection.backup`, then back up objects and previews with checksums. Test restores on an isolated host, including auth, albums and original SHA-256 integrity before depending on backups. **No backup job is installed.**

The password hash is scrypt with a random per-library 16-byte salt. Session tokens are random 256-bit URL-safe tokens stored in SQLite as SHA-256 digests, expiring after 24 hours; revocation applies on lock. Passwords and tokens should never be stored in logs or shell history. Browser token resides in React component memory, Android in process memory, Linux in process memory; all expire on process exit or API time.

## Deployment guards
- No public cloud storage or untrusted third-party AI calls.
- Compose binds only to loopback, drops Linux capabilities, and uses a non-root user.
- Serve behind TLS with strict network egress, size/time limits, and IP throttling.
- Prefer one API instance against a single SQLite volume; multi-worker login-limiting is **not** shared.
- Keep database and media directories mode 0700. Apply private volume backups and storage quotas.
- Do not execute uploaded content; previews are decoded by Pillow, an untrusted media parser that requires timely updates.
- The MP4 signature check is not a full decoder validation. An uploaded MP4 should not be processed by ffmpeg before an isolated media-processing sandbox exists.
- Browser fetches authenticated originals to blob URLs for display; avoid opening very large videos on memory-constrained clients.
- No hard delete or automatic trash purge exists yet; trash hides assets rather than freeing storage.
- No server-side token rotation or password-change endpoint exists yet. Recover using isolated DB administrative procedures, not public endpoints.
- Browser build output must be independently served by a secure HTTPS web server; Dockerfile only runs the API.
- CORS does not replace authentication; do not add wildcard allowed origins.

## Response to incidents
1. Restrict ingress, capture forensic logs without tokens or photos, and preserve encrypted backups.
2. Revoke sessions via the local SQLite `sessions` table while stopped; do not expose emergency administration routes.
3. Update affected dependencies and validate images in quarantine. Restore only from verified clean backups.
4. Follow Wardveil incident procedures and GoreeShield notice/minimization guidance once their actual service contracts are available.

## Pre-release gates
Run Python tests, static lint, web build, Qt QML runtime check, Android emulator/device test, authorization and file-handling fuzzing, vulnerability scans, license scan, backup/restore drill, and HTTPS ingress verification before production use.
