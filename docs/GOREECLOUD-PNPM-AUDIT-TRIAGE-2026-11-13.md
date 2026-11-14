# Photos pnpm advisory diagnostics — November 13, 2026

**Status:** narrowly scoped diagnostic change on a review branch; no dependency upgrades, security approval, real media processing or deployment.

The November 9, 2026 owner-triggered [pnpm advisory CI run](https://github.com/GoreeCloud/photos/actions/runs/42545468680) failed safely. It reported **full workspace: 5 low, 4 moderate, 0 high, 0 critical** and **production scope: 2 low, 4 moderate, 0 high, 0 critical**. These are upstream registry metadata counts, **not** a claim of exploitability or exhaustive security coverage.

The existing summary script previously printed advisory identity examples only for high/critical severity. This meant its logs supplied only counts for the current moderate/low findings, making package triage unnecessarily difficult.

This patch preserves the **fail-closed** audit gate and the existing strict metadata-count parser, but prints up to 12 sanitized, severity-ordered public advisory identity samples across **all** severity levels when the pnpm JSON includes suitable `advisories` entries. If none are present, logs explicitly state that identities were unavailable rather than implying there are no findings.

The workflow remains **manual `workflow_dispatch` only**, uses no package install or lockfile changes, exports no untrusted advisory narrative text, and does not publish output as a release artifact. Manual rerun is required to learn which package/advisory identities the current registry supplies. Review every proposed dependency upgrade for license, source, functionality and compatibility before adoption.

**Release gate remains OPEN:** dependency audit nonzero and privacy/security, media decoder, assets, backend, mobile, ML, native, containers, independent real-device checks and recovery still require work. Do not point this import at actual photo libraries.

## Verified pnpm 12.16.1 schema and fail-closed count reconciliation

An authorized read-only [manual diagnostic workflow](https://github.com/GoreeCloud/photos/actions/runs/43560157601), targeting draft PR #40 at `07dc1e05`, **failed closed** because pinned pnpm 12.16.1 did **not** include the `metadata.vulnerabilities.total` property, even though it emitted all five integer severity counts and an `advisories` object. The reporter previously treated the absent optional field as malformed and printed no useful identities.

A separate local read-only execution of **the same pinned pnpm 12.16.1 CLI** against the identical public lockfile confirmed the actual schema and reconciled *every* advisory object's severity to the metadata counts. The reporter now uses two strict paths:

1. When `total` is supplied, it **must** be an exact nonnegative integer equal to the complete five-level severity count sum. A malformed or inconsistent explicit total is never ignored.
2. When `total` is absent, a bounded array/dictionary of advisory records **must** be supplied, every entry must have one recognized severity, and the advisory count for **each** severity must exactly match the metadata. Absent, incomplete, inconsistent or malformed input remains **UNVERIFIED**, not clean.

An empty advisory object may corroborate all-zero explicit per-severity counts; it cannot silently clear nonzero findings. Tests cover both valid pnpm forms, incomplete metadata, malformed totals, missing identities, duplicate severity mismatches and log sanitization.

## Latest source-only advisory inventory — not cleared

At the November 13, 2026 (America/Chicago) local read-only scan of draft branch `07dc1e05`:

| Scope | Low | Moderate | High | Critical | Total entries |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full workspace | 5 | 7 | 0 | 0 | 12 |
| Production scope | 2 | 5 | 0 | 0 | 7 |

The 7 production-scope entries identify public dependency components `esbuild`, `uuid`, `katex`, `deepmerge`, `glob`, `minimatch`, and `@sveltejs/kit`; the full scope adds multiple separate `@sveltejs/kit` advisories, `@sveltejs/adapter-static` and `cookie`. These are advisory **entries**, not proof that each issue is exploitable in the shipped application. No dependencies were upgraded or product content opened.

The audit command correctly exits nonzero with findings, and a successful reporter parse must still exit **1**, not signal a clean dependency gate. Review package paths, runtime reachability, licensing, upgraded versions, tests, and operating-system/browser compatibility before any dependency change; do not merge or deploy on the strength of this diagnostic alone.

## Proposed narrowly scoped SvelteKit patch (review branch)

**Not merged, installed, deployed, or production-approved.** This stacked review branch is based on audit-diagnostic draft PR #40. It raises the **direct web** dependency minimum from `@sveltejs/kit ^3.0.0` to `^3.1.1` and updates only the associated pnpm lockfile peer identities and integrity metadata. The actual resolved version is **3.1.1**; all other package versions remain unchanged except a package deprecation annotation. No new direct library is introduced.

The pinned pnpm 12.16.1 lockfile-only update ran with `--ignore-scripts`; source code was not downloaded into the app or executed. Public registry metadata for SvelteKit 3.1.0 and 3.1.1 both states MIT, Node >=22.17, and identical eight runtime and five peer dependency declarations. An offline review of the npm package diff identified 19 changed paths (32,423 diff bytes) including runtime forms, env and guard code, version and types; a bounded source heuristic found no added external execution, fetch, credential or secret operations. **These checks do not guarantee the upgraded package is safe or compatible.**

Before patch, public registry advisory metadata reported **production 5 moderate / 2 low** and **full 7 moderate / 5 low**. Following the isolated lockfile update, read-only pinned pnpm audits reported **production 4 moderate / 2 low**, **full 6 moderate / 5 low**. The `@sveltejs/kit@3.1.0` production moderate GHSA-mw6w-2fmv-pvw3 finding disappeared; a separate SvelteKit advisory through other workspace paths remains in full scope. **The audit still fails with unresolved issues and is not cleared.**

Review the separate SvelteKit patch against actual web build, static frontend smoke, dependency provenance and lockfile integrity checks in nonproduction CI. Independent human-interface/browser behavior, source/legal/privacy review, production deployment and the six remaining production advisory entries are not accepted. No dependency should be upgraded solely to force a green advisory count.


## Server React Email dependency-path patch — separate stacked draft

The public pnpm 12 audit identified `server > react-email@6.11.5 > glob@13.0.6` as one moderate advisory route. `react-email@6.11.8`, published November 6, 2026, upgrades the direct dependency to `glob ^14.0.3`. A **lockfile-only, no-scripts** pnpm update resolved `react-email@6.11.8`, `glob@14.0.6`, and its `minimatch@11.0.8` dependency, with no new direct runtime library and **no change to pnpm release-age exclusions or existing supply-chain policy**. The original `react-email` declaration was `^6.0.0`; this draft sets `^6.11.8`.

The inspected registry package metadata identifies MIT license and the unchanged Node `>=20.19.0` engine requirement. Package dependency changes between 6.11.5 and 6.11.8 include the `glob` major update; this upstream source/package change is bigger than the manifest diff and is not considered safe solely on metadata. Source scan and disposable server build with `pnpm install --frozen-lockfile --ignore-scripts` are required before acceptance.

**Measured read-only pnpm advisory delta against parent PR #41 (using the same lockfile as input):**

| Scope | Parent | This isolated patch |
| --- | --- | --- |
| Production | 4 moderate / 2 low | **3 moderate / 2 low** |
| Full dependency graph | 6 moderate / 5 low | **6 moderate / 5 low** |

The `glob` advisory no longer appears in production scope because the React Email path moved to `glob 14`. **The full graph still contains a separate affected `glob` route**. Another production `minimatch@10.2.6` path also remains, as do other advisory entries. Both read-only audits continue to exit **nonzero**: product risk and production gate are **not cleared**. This patch must remain separately reviewable and unmerged until the exact-head disposable server compile/test, source/license review, integration compatibility and residual advisory remediation are verified. It does not access media, credentials or a live server and does not permit deployment.
