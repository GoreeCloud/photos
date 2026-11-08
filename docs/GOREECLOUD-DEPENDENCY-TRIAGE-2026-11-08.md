# GoreeCloud Photos — Dependency Security Triage (November 8, 2026)

**Status:** Development/security assessment, not an application security or release acceptance.
**Authority:** Imported Photos source/lockfile and [prior November 7 advisory triage](GOREECLOUD-DEPENDENCY-TRIAGE-2026-11-07.md), with independently inspected upstream package sources.
**Baseline:** [GoreeCloud/photos main 59679acc](https://github.com/GoreeCloud/photos/commit/59679acc46572e78896202c01b8f14cce0ea8510) with [pnpm full/prod scan #42423630074](https://github.com/GoreeCloud/photos/actions/runs/42423630074).

The baseline advisory job **failed** as intended. Full inherited workspace: **1 critical / 22 high / 26 moderate / 7 low**. pnpm production-dependency scope **including docs/build tooling**: **0 critical / 14 high / 23 moderate / 4 low**. Counts represent reported registry advisory entries, not proof of exploitability or comprehensive security.

## Reviewed patch candidates

| Package and old version | Candidate | Lockfile parent | Source/compatibility review |
| --- | --- | --- | --- |
| SVGO 3.3.4 | **3.3.5** | @svgr/plugin-svgo and postcss-svgo | [Official SVG v3 diff](https://github.com/svg/svgo/compare/v3.3.4...v3.3.5) has 3 commits including security backport to removeScriptElement and regression fixtures. MIT license, unchanged runtime dependencies/Node minimum. Baseline GHSA-w27v-7q3p-w38r, high. |
| systeminformation 5.33.15 | **5.33.16** | @opentelemetry/host-metrics 0.38.3 | [Official systeminformation v5 diff](https://github.com/sebhildebrandt/systeminformation/compare/v5.33.15...v5.33.16) has 2 commits including Windows sanitizeShellString hardening. MIT license, same minimum Node runtime, no added runtime dependencies. Baseline GHSA-3f7j-7jwc-fxfj, high. |

These narrow patch-line overrides do not alter dependency major versions, authentication, user media or runtime API behavior intentionally. The SVG sanitizer fix addresses specific script-removal logic, not all malicious SVG attack paths. Windows host-metrics sanitization does not establish that Photos is confirmed to call the vulnerable function. Neither imported documentation nor application deployment is approved.

**Execution safety:** Resolve only dependency metadata in an isolated HOME with pnpm lockfile-only, lifecycle scripts disabled and registry auth environment cleared. No unreviewed scripts, personal photos or production service may be used. Preserve AGPL attribution, GoreeShield privacy and Wardveil security boundaries.

**Acceptance requirements:** Standard-library source/lockfile tests; exact-head hosted source integrity; separate disposable frozen-lockfile docs, static web/loopback HTTP and SDK/plugin/Nest server builds; full/prod registry audit. Failure must remain visible for any residual advisory. Record run evidence and confirmed counts before changing the release gate.

## Higher-risk open dependency and release blockers

- **Critical tar 6.2.1** arrives through @mapbox/node-pre-gyp 1.0.11. Another node-gyp path already uses tar 7.5.22. The registry recommends patched tar 7.5.19+ for GHSA-23hp-3jrh-7fpw. A v6-to-v7 override may break native package install assumptions, so review parent source and native-media build coverage before any forced major upgrade.
- **undici 8.11.2** occurs through node-gyp and testcontainers, with four high advisories fixed in v8.12.2. The [upstream source diff](https://github.com/nodejs/undici/compare/v8.11.2...v8.12.2) has 81 commits and an HTTP parser submodule change. Inspect vendored sources and behavior and run broader package tests separately.
- **immutable 5.1.6** through Sass has two high advisories patched by v5.1.8, but [the upstream source diff](https://github.com/immutable-js/immutable-js/compare/v5.1.6...v5.1.8) spans 42 commits affecting collection behavior and tests. Review and compile actual consumers before patching.
- Pending high findings also include image-size 2.0.2 via Docusaurus MDX, launch-editor 2.14.1 via webpack-dev-server, serialize-javascript 6.0.2 via webpack plugins and additional packages. Verify published fix provenance, ecosystem compatibility and reachability.

Release remains blocked on authenticated Photos service testing, synthetic media upload/render/share/delete, GoreeShield privacy/consent/retention, Wardveil network/upload/SSRF, GoreeCloud Identity and Mesh contracts, GoreeCloud UI brand/accessibility, offline backup/restore, and installation/deployment testing. **No Stable approval or real personal media testing.**
