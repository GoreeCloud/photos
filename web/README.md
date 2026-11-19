# Web library navigation

The React app pages the main library through the authenticated API at 36 items per page. Filters and filename search reset pagination, and stale requests are ignored so rapid navigation cannot replace newer results.

Album listing now uses server-side filtering and paging through `/v1/albums/{id}/assets?limit=36&offset=...&search=...`. Omitting those parameters retains the original complete-list API contract for older clients. Album owners can rename or delete an album, and remove individual members without deleting original media. Album deletion requires an explicit confirmation in the web UI.

The photo preview uses dialog focus management: it moves focus to Close, cycles keyboard Tab within the dialog, closes with Escape and returns focus to the originating photo button when still available. The filename-search container also displays a visible keyboard focus ring. Trashed photo originals cannot be opened until restored and are no longer presented as active preview controls.

## Local acceptance

Run `npm ci && npm run build`. Test a private library with more than 36 assets, navigate forward/backward, filter by favorites and trash, search while on later pages, and check that locking ends the in-memory session. Synthetic headless Chromium security-flow automation is available below; human keyboard, Firefox and assistive-technology testing remains necessary.


Authenticated library statistics use `GET /v1/library/stats` to show active, favorite and trashed counts and bytes of stored originals. They never reveal filenames or hashes, and the stats state is cleared on Lock. Storage totals include originals in trash; this does not imply permanent deletion or storage reclamation.


If an administrator explicitly sets `PHOTOS_MAX_LIBRARY_BYTES`, the private storage summary reports quota usage and remaining original-media bytes. It tolerates older API responses without quota fields. Trashed originals count toward the configured allowance; this is not a physical disk-free-space estimate or an automatic purge.

## Browser password rotation

In an unlocked library, open **Security** to change its single-library password. The accessible, labelled password form requires the current password, a different 12–1024-character new password, and confirmation; it uses a bearer-authenticated `POST /v1/settings/password` without storing credentials or tokens in local storage. A successful response revokes all server sessions and immediately clears the browser's token, loaded media, previews, metrics, albums and password fields before showing the unlock view. The form focuses the first field on opening and supports Escape/Cancel to clear it. Failures retain the current session but clear the attempted current secret. This feature is **not** identity federation or multi-user access. Testing in a real browser and with assistive technology is a separate acceptance gate.

## Browser memory limits for private media

Private API JSON responses are stream-limited to **4 MiB**; thumbnails to **6 MiB** compressed; and original-image/video browser previews to **64 MiB**. Responses with dishonest or excessive `Content-Length` are rejected, chunked streams are counted, and preview/thumbnail network fetches are cancelled on view changes or Lock. On failure, the preview shows an error instead of allocating an unbounded Blob. For originals exceeding the browser preview limit, save through the Linux/Android native client or `photosctl download` rather than trying to preview a large file in browser memory. No media leaves the owner's selected API. Tests: `node --experimental-strip-types --test tests/network.test.mjs` (Node.js 22+), plus `npm run build`. This is not a substitute for media decoder isolation and accessibility verification.

## Sign out all devices without rotating the password

The unlocked web **Security** view provides a separate **Sign out all devices without changing password** button. It requires the current masked library password and calls the authenticated `POST /v1/settings/revoke-sessions` endpoint. On confirmed server revocation, the browser immediately clears its session and private library state; failed requests preserve the user's current session but clear the attempted current password field. This does not change the account password, recover access to a lost library, or implement multi-user identity. If a password may be compromised, use password rotation instead. Test the actual browser interaction and assistive technology before production.

## Reproducible real-browser security acceptance

From the repository root, with Node.js 22+, Python 3.12+, `uv` and a **trusted installed Chromium headless binary**:

```sh
npm --prefix web ci
npm --prefix web run build
cd api
uv sync --frozen --group dev
uv run --frozen python ../scripts/browser_acceptance.py --chromium /absolute/path/to/chrome-headless-shell
```

If the local Linux sandbox prevents a disposable browser from starting, add `--unsafe-no-sandbox` **only on a trusted development machine**, not for general browsing. The harness starts an isolated **127.0.0.1-only** API and Chromium instance with a private temporary directory, creates one synthetic image and password, exercises the actual React UI through the Chrome DevTools Protocol, then terminates its owned processes and deletes the test profile/media even after failed assertions. It checks login and synthetic gallery, masked fields and autofocus, invalid current-password error semantics, password rotation and private-state erasure, global session revocation, relogin and Escape/field-clearing behavior. It never needs a real library, device gallery, network tunnel, or personal password, and does not modify production data.

This is automated Chromium UI acceptance, **not** a substitute for human keyboard/visual checks, Firefox/WebKit compatibility, NVDA/Orca screen readers, production ingress, signed releases, or genuine recovery tests. The Chromium binary is not distributed by this repository; review its publisher/source before executing.
