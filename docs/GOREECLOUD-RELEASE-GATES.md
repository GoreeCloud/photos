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
- [x] [Scoped brace-expansion v1.1.20 security patch PR #20](https://github.com/GoreeCloud/photos/pull/20) passed exact-head source and frozen [docs](https://github.com/GoreeCloud/photos/actions/runs/42421461718), [web](https://github.com/GoreeCloud/photos/actions/runs/42421463662), [server](https://github.com/GoreeCloud/photos/actions/runs/42421465504) builds and merged as [main 4e253ed](https://github.com/GoreeCloud/photos/commit/4e253edb62eb882f77da7bcfa8379825c31ffba4), preserving 2.x/5.x dependencies. [pnpm advisory rerun](https://github.com/GoreeCloud/photos/actions/runs/42421467418) still failed: full 1 critical/28 high, prod 0 critical/20 high. This is build/source evidence only; overall Wardveil security remains blocked.
- [x] [DOMPurify 3.4.17 / shell-quote 1.11.0 patch PR #14](https://github.com/GoreeCloud/photos/pull/14) merged after clean frozen [web](https://github.com/GoreeCloud/photos/actions/runs/42420066911) and [server](https://github.com/GoreeCloud/photos/actions/runs/42420069123) builds. [Post-merge Docusaurus build #42420206414](https://github.com/GoreeCloud/photos/actions/runs/42420206414) passed. The [pnpm audit #42420071308](https://github.com/GoreeCloud/photos/actions/runs/42420071308) still failed, so **release security remains blocked**; imported docs remain unapproved for publication.
- [x] [Tinypool 2.2.0 docs-toolchain upgrade PR #17](https://github.com/GoreeCloud/photos/pull/17) passed hosted frozen [docs](https://github.com/GoreeCloud/photos/actions/runs/42420669299), [web](https://github.com/GoreeCloud/photos/actions/runs/42420671316), [server](https://github.com/GoreeCloud/photos/actions/runs/42420673174) and source-integrity checks, then merged as [main d7a908d](https://github.com/GoreeCloud/photos/commit/d7a908d606a977f4d466cbadd8b53d91aaccc24f). The [advisory scan](https://github.com/GoreeCloud/photos/actions/runs/42420675378) still failed with **one full-workspace critical, 33 high** and **zero pnpm production-scope critical, 25 high** advisory entries. Build-only acceptance; no Wardveil waiver or deployment.
- [ ] [pnpm advisory triage (November 7, 2026)](GOREECLOUD-DEPENDENCY-TRIAGE-2026-11-07.md): high/critical findings remain open. The manual full/production-scope scans failed as expected; source path tracing is preliminary, not remediation or a release waiver.
- [x] [Fast-uri v3.1.9 targeted patch](https://github.com/GoreeCloud/photos/pull/12) merged after frozen-lockfile web/server builds and source integrity passed. [Post-patch audit](https://github.com/GoreeCloud/photos/actions/runs/42419440996) still found 4 critical and 26 high advisory entries in pnpm's production-dependency scope; complete security acceptance remains **blocked**.

See the [static supply-chain preflight](GOREECLOUD-SUPPLY-CHAIN-PREFLIGHT.md) for inspected dependency and automation surfaces.

**Scope note:** Static tests do not establish source safety, licensing review of every dependency, or production readiness.

## Gate 1 — Visual identity and basic user experience (partial)

- [x] Central GoreeCloud Photos app icon adopted into web favicon, SVG icon and PWA icons; 180px Apple icon derived from an approved raster.
- [x] Web/PWA display name uses GoreeCloud Photos.
- [x] Adopt verified central light/dark wordmarks in shared web component and replace five primary UI logo surfaces plus browser title at source level. The updated source passed [latest main web compilation #42417477789](https://github.com/GoreeCloud/photos/actions/runs/42417477789); browser-rendered visual acceptance remains pending.
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
- [x] [Manual isolated build #42416035395](https://github.com/GoreeCloud/photos/actions/runs/42416035395) **passed** pinned Node/pnpm setup, no-lifecycle-script dependency install, explicit local SDK TypeScript compilation, inherited SvelteKit/Vite web compilation, and first-party PWA/asset byte validation. This is a source-build acceptance only, not a production, browser-UX or application-service test.
- [x] [Loopback HTTP static-delivery CI #42416380403](https://github.com/GoreeCloud/photos/actions/runs/42416380403) passed HTML shell, JSON manifest, five approved first-party assets, GET/HEAD in a disposable runner. [Latest branded-main rerun #42417477789](https://github.com/GoreeCloud/photos/actions/runs/42417477789) also passed on main 459a87b. Neither is browser JS interaction or backend API acceptance.
- [x] [Manual isolated server compilation #42417305584](https://github.com/GoreeCloud/photos/actions/runs/42417305584) **passed** pinned dependency install with lifecycle scripts disabled, SDK, plugin SDK, Nest build, and generated artifact checks. No database, private media, service startup or production use; this accepts compilation only.
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

### Initial web build evidence — November 7, 2026

- [Manual GitHub Actions run #42415821050](https://github.com/GoreeCloud/photos/actions/runs/42415821050) **failed during Vite compilation**, after successful checkout, pinned pnpm setup and lockfile installation with lifecycle scripts disabled.
- Failure: Rolldown could not resolve @immich/sdk from web/src/lib/queries/server-info.query.ts. The imported packages/sdk/package.json declares build/index.js as its module entry and a TypeScript tsc build script.
- Remediation: explicitly compile the @immich/sdk workspace using its existing TypeScript build script in the disposable runner **before** attempting the web build, without allowing package-install lifecycle scripts.
- This first failure remains recorded; web compilation is not accepted until a successful isolated rerun including PWA artifact verification. Deployment, security, runtime and data handling gates stay open.

### Isolated web build recovery evidence — November 7, 2026

- [PR #4](https://github.com/GoreeCloud/photos/pull/4) merged the deliberate SDK-first build prerequisite to [main 95a5652](https://github.com/GoreeCloud/photos/commit/95a565262507bd700c82a64dcfff1ff1af665916). PR and post-merge static CI passed.
- The [second manual web build #42416035395](https://github.com/GoreeCloud/photos/actions/runs/42416035395) **PASSED**: TypeScript SDK, full SvelteKit/Vite web source compilation, and generated PWA manifest and official icon integrity. No secrets, real photos, app server or deployment were used.
- This accepts **only** a disposable browser-source compilation and generated static artifacts; actual interactive web behavior, API/backend, security/privacy, media workflows, cross-platform devices and recovery remain unverified.


### Current-main web + server build acceptance — November 7, 2026

- [Main commit 459a87b](https://github.com/GoreeCloud/photos/commit/459a87b3894a7c52ff54f5a92917bcdef54dc305) contains the official Photos primary logo work and manually triggered server source build gate. [Post-merge static integrity](https://github.com/GoreeCloud/photos/actions/runs/42417295642) passed.
- [Manual backend build #42417305584](https://github.com/GoreeCloud/photos/actions/runs/42417305584) **PASSED** SDK TypeScript, plugin SDK bundling/declarations, Nest server compilation and static dist output checks; no server process was launched.
- [Manual branded-main web build #42417477789](https://github.com/GoreeCloud/photos/actions/runs/42417477789) **PASSED** SDK compilation, SvelteKit/Vite build, official asset hash checks, and loopback GET/HEAD static-delivery smoke. This includes source-level first-party logo and title changes.
- **Not accepted:** Interactive client UI, authenticated API, real server/database, uploads, photo processing, privacy/security, mobile apps, backup/restore, or deployment. Static loopback delivery and TypeScript compilation are not a service-level smoke test.
