# Web library navigation

The React app pages the main library through the authenticated API at 36 items per page. Filters and filename search reset pagination, and stale requests are ignored so rapid navigation cannot replace newer results.

Album listing now uses server-side filtering and paging through `/v1/albums/{id}/assets?limit=36&offset=...&search=...`. Omitting those parameters retains the original complete-list API contract for older clients. Album owners can rename or delete an album, and remove individual members without deleting original media. Album deletion requires an explicit confirmation in the web UI.

The photo preview uses dialog focus management: it moves focus to Close, cycles keyboard Tab within the dialog, closes with Escape and returns focus to the originating photo button when still available. The filename-search container also displays a visible keyboard focus ring. Trashed photo originals cannot be opened until restored and are no longer presented as active preview controls.

## Local acceptance

Run `npm ci && npm run build`. Test a private library with more than 36 assets, navigate forward/backward, filter by favorites and trash, search while on later pages, and check that locking ends the in-memory session. Physical browser accessibility/keyboard testing is still required.


Authenticated library statistics use `GET /v1/library/stats` to show active, favorite and trashed counts and bytes of stored originals. They never reveal filenames or hashes, and the stats state is cleared on Lock. Storage totals include originals in trash; this does not imply permanent deletion or storage reclamation.


If an administrator explicitly sets `PHOTOS_MAX_LIBRARY_BYTES`, the private storage summary reports quota usage and remaining original-media bytes. It tolerates older API responses without quota fields. Trashed originals count toward the configured allowance; this is not a physical disk-free-space estimate or an automatic purge.

## Browser password rotation

In an unlocked library, open **Security** to change its single-library password. The accessible, labelled password form requires the current password, a different 12–1024-character new password, and confirmation; it uses a bearer-authenticated `POST /v1/settings/password` without storing credentials or tokens in local storage. A successful response revokes all server sessions and immediately clears the browser's token, loaded media, previews, metrics, albums and password fields before showing the unlock view. The form focuses the first field on opening and supports Escape/Cancel to clear it. Failures retain the current session but clear the attempted current secret. This feature is **not** identity federation or multi-user access. Testing in a real browser and with assistive technology is a separate acceptance gate.
