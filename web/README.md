# Web library navigation

The React app pages the main library through the authenticated API at 36 items per page. Filters and filename search reset pagination, and stale requests are ignored so rapid navigation cannot replace newer results.

Album listing currently uses the original all-members API and applies client-side filtering/pagination; this is a compatibility bridge, **not** a scalable server-side album paginator. Future work should paginate album membership in the API without breaking existing clients.

## Local acceptance

Run `npm ci && npm run build`. Test a private library with more than 36 assets, navigate forward/backward, filter by favorites and trash, search while on later pages, and check that locking ends the in-memory session. Physical browser accessibility/keyboard testing is still required.
