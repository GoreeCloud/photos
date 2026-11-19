# Web library navigation

The React app pages the main library through the authenticated API at 36 items per page. Filters and filename search reset pagination, and stale requests are ignored so rapid navigation cannot replace newer results.

Album listing now uses server-side filtering and paging through `/v1/albums/{id}/assets?limit=36&offset=...&search=...`. Omitting those parameters retains the original complete-list API contract for older clients. Album owners can rename or delete an album, and remove individual members without deleting original media. Album deletion requires an explicit confirmation in the web UI.

## Local acceptance

Run `npm ci && npm run build`. Test a private library with more than 36 assets, navigate forward/backward, filter by favorites and trash, search while on later pages, and check that locking ends the in-memory session. Physical browser accessibility/keyboard testing is still required.
