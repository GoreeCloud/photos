# GoreeCloud Photos — Import Provenance and Safety Gates

## Source

- Classification: **Rebranded Import**, incomplete rebrand.
- Source: [immich-app/immich](https://github.com/immich-app/immich), main.
- Pinned source commit: 87ef895041e160aef4f61f2d7af1ad3f8e38827d.
- Source tree SHA: f42ed56eadcddfff901ff5bf7c55f8b7373dc284.
- Import date: November 7, 2026.
- License: GNU AGPL-3.0; upstream LICENSE preserved byte for byte.
- Method: all checked-out tracked files copied into a snapshot, with the external e2e/test-assets submodule gitlink preserved. Full upstream history was not imported.

## Deliberate changes

1. Repository README replaced with transparent GoreeCloud Photos development status.
2. Upstream README archived intact at docs/UPSTREAM-README.md.
3. Web PWA name changed to GoreeCloud Photos and short_name to Photos in web/static/manifest.json.
4. Browser JavaScript-disabled text changed in web/src/app.html.
5. All 27 upstream GitHub workflows moved from .github/workflows to docs/upstream-github-workflows to disable automatic execution.
6. Upstream root CODEOWNERS moved to docs/UPSTREAM-CODEOWNERS to avoid invalid auto-review assignments.
7. This provenance file added.

Unchanged internal immich IDs, APIs, storage, deployment files, other labels, icons and external domains are inherited technical/brand elements, NOT GoreeCloud implementation or authorization to use Immich trademarks. The original branding assets must be reviewed prior to distribution.

## Submodule

The e2e/test-assets gitlink remains pinned at 6742055402de1aa48f93d12ded7d18f4057f9d1f, pointing to the upstream test-assets project through the unchanged .gitmodules. Its contents were not downloaded, executed or audited.

## Verification limits and acceptance gates

No dependency resolution, startup hook, test, package builder, container, installation or deployment was executed during import. No successful end-to-end or security testing is claimed.

Before using photos with any personal media, independently review dependency integrity, scripts, package licenses, branding and third-party media rights; audit secrets and data handling; define GoreeShield consent/retention and Wardveil security controls; verify GoreeCloud Identity and Mesh boundaries; test photo library isolation, authorization, cold start, TLS, backup/restore, media migrations, upgrade and rollback using synthetic assets; and add CI only after inspecting each workflow. Treat the upstream license and appropriate network-accessible source obligations as ongoing requirements.

For future upstream updates: compare against the pinned source commit, document new hashes and modified files, reconcile with GoreeCloud changes, inspect new automation, and verify regression behavior before calling an update complete.


## November 7, 2026 — Post-import repository hardening (separate GoreeCloud change)

- Added a read-only, dependency-free static integrity suite and a single least-privilege GitHub Actions workflow pinned to the verified actions/checkout v4.2.2 commit. No inherited Immich workflows were activated.
- Used the verified first-party [GoreeCloud Photos brand assets](GOREECLOUD-BRAND-ADOPTION.md) to replace web/PWA SVG, favicon and raster icons; PWA icons deliberately use purpose any, not unverified maskable compliance.
- Quarantined the inherited Renovate configuration and GitHub contributor issue, discussion, release and PR-routing controls under docs/upstream-repository-controls; replaced current contributor/PR instructions with GoreeCloud-specific review language.
- Retained the original upstream contributing guide at docs/UPSTREAM-CONTRIBUTING.md.
- Created an explicit [release gate tracker](GOREECLOUD-RELEASE-GATES.md) identifying untested security, runtime, privacy, recovery, mobile and deployment work.

The files are source modifications, not evidence of validated live runtime behavior. No automated dependency installation, Immich source tests, deployments or processing of personal images were undertaken in this hardening stage.

## Targeted web source identity update — November 7, 2026

Official GoreeCloud Photos central brand wordmarks were verified by Git blob SHA, copied unchanged, and referenced via a reusable light/dark or icon Svelte component. Auth, navigation, onboarding, error, shared-link password-header and document title source markup were updated. The shared SDK, inherited version/about disclosures, storage contracts and service IDs were not globally renamed. This source-level brand step is not full runtime UI/visual acceptance and does not establish new deployment behavior.
