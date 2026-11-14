# Photos pnpm advisory diagnostics — November 13, 2026

**Status:** narrowly scoped diagnostic change on a review branch; no dependency upgrades, security approval, real media processing or deployment.

The November 9, 2026 owner-triggered [pnpm advisory CI run](https://github.com/GoreeCloud/photos/actions/runs/42545468680) failed safely. It reported **full workspace: 5 low, 4 moderate, 0 high, 0 critical** and **production scope: 2 low, 4 moderate, 0 high, 0 critical**. These are upstream registry metadata counts, **not** a claim of exploitability or exhaustive security coverage.

The existing summary script previously printed advisory identity examples only for high/critical severity. This meant its logs supplied only counts for the current moderate/low findings, making package triage unnecessarily difficult.

This patch preserves the **fail-closed** audit gate and the existing strict metadata-count parser, but prints up to 12 sanitized, severity-ordered public advisory identity samples across **all** severity levels when the pnpm JSON includes suitable `advisories` entries. If none are present, logs explicitly state that identities were unavailable rather than implying there are no findings.

The workflow remains **manual `workflow_dispatch` only**, uses no package install or lockfile changes, exports no untrusted advisory narrative text, and does not publish output as a release artifact. Manual rerun is required to learn which package/advisory identities the current registry supplies. Review every proposed dependency upgrade for license, source, functionality and compatibility before adoption.

**Release gate remains OPEN:** dependency audit nonzero and privacy/security, media decoder, assets, backend, mobile, ML, native, containers, independent real-device checks and recovery still require work. Do not point this import at actual photo libraries.

## Severity-total consistency safeguard

The summary now also requires `metadata.vulnerabilities.total` to be a nonnegative integer **exactly equal** to the sum of per-severity counts. Missing, malformed, understated, or overstated totals are rejected as unverified rather than misreported as a clean audit. This is a deliberately conservative compatibility gate: if a future pnpm schema intentionally changes its count semantics, verify and adapt that schema before changing this guard.


## Proposed narrowly scoped SvelteKit patch (review branch)

**Not merged, installed, deployed, or production-approved.** This stacked review branch is based on audit-diagnostic draft PR #40. It raises the **direct web** dependency minimum from `@sveltejs/kit ^3.0.0` to `^3.1.1` and updates only the associated pnpm lockfile peer identities and integrity metadata. The actual resolved version is **3.1.1**; all other package versions remain unchanged except a package deprecation annotation. No new direct library is introduced.

The pinned pnpm 12.16.1 lockfile-only update ran with `--ignore-scripts`; source code was not downloaded into the app or executed. Public registry metadata for SvelteKit 3.1.0 and 3.1.1 both states MIT, Node >=22.17, and identical eight runtime and five peer dependency declarations. An offline review of the npm package diff identified 19 changed paths (32,423 diff bytes) including runtime forms, env and guard code, version and types; a bounded source heuristic found no added external execution, fetch, credential or secret operations. **These checks do not guarantee the upgraded package is safe or compatible.**

Before patch, public registry advisory metadata reported **production 5 moderate / 2 low** and **full 7 moderate / 5 low**. Following the isolated lockfile update, read-only pinned pnpm audits reported **production 4 moderate / 2 low**, **full 6 moderate / 5 low**. The `@sveltejs/kit@3.1.0` production moderate GHSA-mw6w-2fmv-pvw3 finding disappeared; a separate SvelteKit advisory through other workspace paths remains in full scope. **The audit still fails with unresolved issues and is not cleared.**

Review the separate SvelteKit patch against actual web build, static frontend smoke, dependency provenance and lockfile integrity checks in nonproduction CI. Independent human-interface/browser behavior, source/legal/privacy review, production deployment and the six remaining production advisory entries are not accepted. No dependency should be upgraded solely to force a green advisory count.
