# GoreeCloud Photos — Release Gates

**Product:** GoreeCloud Photos, an attributed AGPL-3.0 Immich source derivative.
**Current maturity:** Source-development baseline, not deployed, not ready for private photos.
**Initial import source:** immich-app/immich main 87ef895041e160aef4f61f2d7af1ad3f8e38827d, verified November 7, 2026.

## Gate 0 — Source and repository hygiene (partial)

- [x] Public GoreeCloud/photos main contains an attributed Immich source snapshot with the original LICENSE and README.
- [x] Original 27 upstream GitHub workflows archived, not active.
- [x] Upstream Renovate configuration and GitHub issue/discussion/release/review routing archived to prevent accidental adoption.
- [x] Privacy-preserving GitHub commit identity, no personal media committed as part of this development work.
- [x] Local read-only Python integrity suite checks pinned license/README, upstream provenance, workflow quarantine, branding and gitlink.
- [x] [PR #1 source integrity CI](https://github.com/GoreeCloud/photos/actions/runs/42414650696) and [post-merge main CI](https://github.com/GoreeCloud/photos/actions/runs/42414719402) passed on November 7, 2026 for main commit [45860140](https://github.com/GoreeCloud/photos/commit/45860140fcdb6b6071495e5cdb86caa46130332d). This accepts only the narrowly scoped static checks.
- [ ] Dependency license, vulnerability, provenance, third-party asset, executable script and secrets review is accepted.

See the [static supply-chain preflight](GOREECLOUD-SUPPLY-CHAIN-PREFLIGHT.md) for inspected dependency and automation surfaces.

**Scope note:** Static tests do not establish source safety, licensing review of every dependency, or production readiness.

## Gate 1 — Visual identity and basic user experience (partial)

- [x] Central GoreeCloud Photos app icon adopted into web favicon, SVG icon and PWA icons; 180px Apple icon derived from an approved raster.
- [x] Web/PWA display name uses GoreeCloud Photos.
- [ ] Replace remaining inherited product logos and brand-specific copy in app web surfaces without altering compatibility contracts.
- [ ] Adopt the current GoreeCloud UI token semantics, components and theme behavior after inspecting concrete consumer integration points.
- [ ] Verify affected pages, empty/error/loading states and responsive layouts through actual browser rendering.
- [ ] Review Android/iOS identity, bundles, icons, permissions and platform packaging separately.

## Gate 2 — Privacy, access control and platform integration (open)

- [ ] GoreeShield: consent, private sharing defaults, retention and removal, location/face metadata privacy, external-services disclosure.
- [ ] Wardveil: dependency and container scan triage, TLS, session/auth, SSRF/file processing, upload size/type handling, isolation, audit logs and incident response.
- [ ] GoreeCloud Identity: authenticated-user mapping, least privilege, account recovery, logout/revocation and independent authorization tests.
- [ ] GoreeCloud Mesh: versioned, permission-checked contracts with explicit no-integration defaults and retry/error boundaries.
- [ ] Review upstream services and installation to establish safe, opt-in outbound connectivity and no surprise network exposure.

**Boundary:** Integration designs are proposals until code and tests demonstrate them. No service connections or user data sync are implied by source import.

## Gate 3 — Functional and recovery acceptance (open)

- [ ] Build web/server/mobile and service images in a disposable, dependency-reviewed environment.
- [ ] Test import, upload, metadata, albums, search, sharing, auth and media operations with synthetic images/videos only.
- [ ] Verify persistence, encrypted transport, storage isolation, backup, restore, migrations, upgrade and rollback.
- [ ] Observe resource use, health monitoring and failure behavior; establish reproducible accepted install.
- [ ] Review submodule e2e/test-assets before fetching or executing its contents.

## Gate 4 — Controlled release (open)

- [ ] Reviewed and scoped full CI with reproducible dependencies and supply-chain provenance.
- [ ] Software license/attribution source-offer and trademark/media-rights acceptance.
- [ ] Documented support matrix, operator runbook, safe default configuration, rollback and release artifacts.
- [ ] Verified staging acceptance and explicit founder-controlled release/deployment decision.

**Release rule:** Only demonstrated checks may be marked complete. No live installation, data migration, private-media test, production release or continuous unattended operation is currently claimed.
