# GoreeCloud Photos — pnpm Dependency Advisory Triage

**Date:** November 7, 2026
**Product maturity:** Attributed Immich source derivative; not deployed or security-accepted.
**Source baseline:** GoreeCloud/photos main fa89e9f0494ece5b3f08ae1a6dfe44db00c97bd1.
**Evidence:** [Full and production-scope audit](https://github.com/GoreeCloud/photos/actions/runs/42418292059); initial [full-only audit](https://github.com/GoreeCloud/photos/actions/runs/42418045175).

## Observed audit counts

| Scope queried by pnpm | Critical | High | Moderate | Low |
| --- | ---: | ---: | ---: | ---: |
| Full workspace, including development dependencies | 5 | 40 | 31 | 13 |
| pnpm production-dependency scope | 4 | 32 | 28 | 10 |

Both runner jobs intentionally **failed** on advisory findings. Counts are registry entries, not individually verified exploits. The pnpm production scope includes documentation-site dependencies; it is not equivalent to exposure in a deployed GoreeCloud photo server or browser client. No package fix, suppression, new credential, deployment or release was performed.

## Critical advisory source-path investigation

A static traversal of the imported pnpm lockfile matched dependencies by exact package/version and followed imported workspace dependencies plus transitive and optional dependencies. The upstream lockfile contains two YAML documents: a pnpm executable/toolchain segment followed by the application workspace lock; both were preserved from the source import. The following **observed paths** explain the critical samples and do not independently establish which paths execute in any deployment:

| Package version | Advisory | Observed shortest dependency path | Notes |
| --- | --- | --- | --- |
| dompurify 3.4.12 | GHSA-cg2g-xh64-v4q7 | docs → @docusaurus/theme-mermaid → mermaid → dompurify | Published patched range starts at 3.4.17 |
| shell-quote 1.10.0 | GHSA-pqg4-j6r4-53mv | docs → @docusaurus/core → webpack-dev-server → launch-editor → shell-quote | Published patched range starts at 1.11.0 |
| tinypool 1.1.1 | GHSA-5gmw-xhrv-c9v3 | docs → @docusaurus/core → tinypool | Published patched range starts at 2.1.1 |
| tinypool 1.1.1 | GHSA-85c8-ppgw-ccpr | docs → @docusaurus/core → tinypool | Published patched range starts at 2.1.2 |

Additional observations: the web dependencies resolve tinypool 2.2.0 through the FUTO backup UI/Lingui chain, not the vulnerable 1.1.1 snapshot. The inspected critical paths above did not appear in the traversed web/server production dependency roots. This is **preliminary static evidence**, not a complete dependency or attack-surface proof, and does not waive or suppress any advisory.

The fifth full-workspace critical sample, tar (GHSA-23hp-3jrh-7fpw), maps to tar 6.2.1 through an end-to-end/development toolchain; a separate tar 7.5.22 version is present. Its code paths and practical exploitability have not been independently reviewed.

## High-severity findings relevant to application paths

- **fast-uri 3.1.4 / GHSA-5jgf-p345-68v8:** The audit reports a patched range starting at 3.1.6 for this **individual advisory**. Static paths include web → svelte-jsoneditor → ajv → fast-uri and server → react-email → conf → ajv → fast-uri. The later published [GHSA-hrr3-gc8f-f4qj](https://github.com/fastify/fast-uri/security/advisories/GHSA-hrr3-gc8f-f4qj) identifies an additional URL-host normalization weakness and recommends at least 3.1.8 on the 3.x line. A candidate must account for the **full current advisory set**, not stop at 3.1.6. Dependency presence alone is not proof of a triggered exploit.
- **body-parser:** The audited 1.20.6 version is reached through docs → @docusaurus/core → webpack-dev-server → express 4. The server's direct body-parser dependency resolves to version 2.4.0 through the current lockfile, so the docs and server versions must not be conflated.
- **brace-expansion and others:** Additional high advisories involve multiple snapshot versions and importers. Do not assume a single override resolves every affected major version or that a vulnerable package is reachable on an exposed service path.

## Controlled remediation order

1. Review each high/critical advisory's actual affected version range and conditions against the lockfile and the relevant web, server and documentation usage, with Wardveil threat-model review.
2. Review source, maintainer release notes, license, scripts and dependency changes for candidate patches. Prefer the narrowest compatible, reproducible update; keep original AGPL/source attribution and build constraints.
3. Stage changes on a separate branch; run the source-integrity suite, isolated SDK/web/server compilation, static HTTP checks and targeted functional/security regressions. Never use real family photos as test data.
4. Re-run full and production-scope advisory intake and compare exact source commits. Do not automatically apply pnpm audit --fix, blanket ignores or unreviewed global overrides.
5. Expand review beyond pnpm: Python uv, Rust Cargo, Flutter/Dart, containers, native apps, asset/trademark rights and actual deployed service configuration.

**Gate status:** Open and release-blocking. The [release tracker](GOREECLOUD-RELEASE-GATES.md) is authoritative for accepted implementation milestones. A successful audit scan alone would not establish deployed security.


## Fast-uri v3.1.9 targeted remediation — source and build accepted

The first targeted security patch proposal sets a single pnpm override, fast-uri: 3.1.9, and updates the exact lockfile resolution from 3.1.4 to 3.1.9. This is the existing major-v3 release line; the vendor's BSD-3-Clause license and original attribution remain unchanged. The official [fast-uri repository](https://github.com/fastify/fast-uri) and the [v3.1.4-to-v3.1.9 upstream comparison](https://github.com/fastify/fast-uri/compare/v3.1.4...v3.1.9) were inspected for source, dependency, install-script and security-test changes. Its published package manifest at v3.1.9 has no runtime dependencies or install lifecycle scripts.

The lockfile was regenerated in metadata-only mode with install scripts disabled; the codebase was not run locally. Regression checks assert that the workspace override, resolved package and AJV dependency edge agree and that the old vulnerable 3.1.4 snapshot is absent. **The update passed separate frozen-lockfile web and Nest server builds and an independent advisory rerun on the exact patch head, then merged into main through [PR #12](https://github.com/GoreeCloud/photos/pull/12).** This is accepted as a scoped dependency patch only; it does not remediate the remaining findings or satisfy the Wardveil security gate.


### fast-uri validation and residual advisories — November 7, 2026

- [PR #12](https://github.com/GoreeCloud/photos/pull/12) merged the isolated v3.1.9 override, package resolution and lockfile to [main 8697b2f](https://github.com/GoreeCloud/photos/commit/8697b2fb904e640bc9456ff2ecc8d9f9d4f327af). The original v3.1.4 snapshot is absent. The upstream dependency's original BSD-3-Clause license and attribution remain applicable.
- Frozen-lockfile hosted checks on the **exact PR head** passed: [SDK + plugin + Nest server compile #42419438716](https://github.com/GoreeCloud/photos/actions/runs/42419438716), [web build + first-party PWA assets + loopback HTTP #42419436543](https://github.com/GoreeCloud/photos/actions/runs/42419436543), and [source-integrity CI #42419422022](https://github.com/GoreeCloud/photos/actions/runs/42419422022). No real media, secrets, production service or deployment was involved.
- [Post-patch pnpm audit #42419440996](https://github.com/GoreeCloud/photos/actions/runs/42419440996) still **failed** because other advisories remain. Full workspace: **5 critical / 34 high / 28 moderate / 11 low** (previously 5 / 40 / 31 / 13); pnpm production dependency scope: **4 critical / 26 high / 25 moderate / 8 low** (previously 4 / 32 / 28 / 10). These are registry advisory entry counts; changes may include advisory database updates between scans, and counts alone do not prove precisely which advisories were eliminated. No release waiver is implied.
- **Next targeted risk:** Review documentation-chain dompurify / shell-quote / tinypool critical findings and other web/server high-priority paths; inspect patched release source and compatibility before further changes. The entire dependency and operational security gate stays **OPEN**.


## Documentation-chain leaf patch — build accepted, security gate still open

The next targeted candidate pins DOMPurify 3.4.17 (from 3.4.12) and shell-quote 1.11.0 (from 1.10.0), both through one pnpm workspace override per package. This addresses critical advisory families reported through the inherited docs/Docusaurus chain; it is not a production Photos service claim.

Source/license preflight: DOMPurify upstream 3.4.17 retains the dual MPL-2.0/Apache-2.0 license, with a materially changed source and build pipeline since 3.4.12, including additional regression cases. shell-quote 1.11.0 retains MIT and its package scripts and minimum Node engine requirement; upstream changes include shell token escaping and parse handling security fixes. Both version tags and source diffs were reviewed. Current public dependencies and notice obligations remain in scope.

The change must pass a frozen-lockfile isolated *documentation-site compilation* (because that is where the vulnerable dependency versions are reached) alongside isolated web/server builds and pnpm advisory count reconciliation. The docs output is inherited Immich documentation, with upstream links and branding, **not approved for deployment** as GoreeCloud documentation. No source install/lifecycle script, runtime app, personal media or deployment is authorized by this test.


### DOMPurify and shell-quote accepted source/build evidence — November 7, 2026

- [PR #14](https://github.com/GoreeCloud/photos/pull/14) merged dompurify 3.4.17 and shell-quote 1.11.0 as narrow pinned versions on [main a071065](https://github.com/GoreeCloud/photos/commit/a071065d577fa8701fcaacf7b2f445bbf0fdce58). Official package licenses and notices remain applicable.
- The exact patch-head [web compile and HTTP smoke #42420066911](https://github.com/GoreeCloud/photos/actions/runs/42420066911) and [Nest server compilation #42420069123](https://github.com/GoreeCloud/photos/actions/runs/42420069123) passed. The new [post-merge docs compilation #42420206414](https://github.com/GoreeCloud/photos/actions/runs/42420206414) also passed; docs were not published.
- [Remaining pnpm audit findings #42420071308](https://github.com/GoreeCloud/photos/actions/runs/42420071308): full workspace 3 critical/33 high/27 moderate/9 low, pnpm production scope 2 critical/25 high/24 moderate/6 low. The audit still **failed** correctly. The two remaining production-scope critical advisories are tinypool 1.1.1 via the docs/Docusaurus chain. New dependency remediation is required; the entire Wardveil security gate is **not accepted**.

## Tinypool docs-toolchain security change — source/build accepted, security gate open

The follow-up advisory scan after the DOMPurify and shell-quote changes still reports two critical entries for tinypool 1.1.1, [GHSA-5gmw-xhrv-c9v3](https://github.com/advisories/GHSA-5gmw-xhrv-c9v3) and [GHSA-85c8-ppgw-ccpr](https://github.com/advisories/GHSA-85c8-ppgw-ccpr), through the Docusaurus documentation dependency chain. The imported web workspace already resolves tinypool 2.2.0 on a distinct chain. The official [tinylibs/tinypool](https://github.com/tinylibs/tinypool) manifests at v1.1.1 and v2.2.0 and their [upstream comparison](https://github.com/tinylibs/tinypool/compare/v1.1.1...v2.2.0) were inspected. Both are MIT-licensed, have the same main module export path, and declare no install lifecycle hooks; v2.2.0 targets Node 20 or Node 22+ and includes corrections for worker option/filename prototype-pollution flaws. **This is a 1.x → 2.x major upgrade, not a presumed compatible patch.**

The isolated candidate pins tinypool 2.2.0 through the existing pnpm override mechanism and regenerates only lockfile metadata with lifecycle scripts disabled. Acceptance required exact-branch frozen-lockfile documentation, web and server builds, source integrity, and repeat full and production-scope advisory results. Those scoped checks passed or produced bounded findings as recorded below; actual documentation behavior, server exposure, complete package risks and deployments remain unverified. The existing advisory gate stays open even if the two critical registry entries disappear.


### Verified Tinypool source/build evidence — November 7, 2026

- [PR #17](https://github.com/GoreeCloud/photos/pull/17) merged the Tinypool 2.2.0 lockfile and override into public [main d7a908d](https://github.com/GoreeCloud/photos/commit/d7a908d606a977f4d466cbadd8b53d91aaccc24f). The old 1.1.1 lockfile snapshot was removed, while the preexisting 2.2.0 resolution was reused. No install lifecycle script or production application ran locally.
- Exact patch-head hosted [source integrity #42420657616](https://github.com/GoreeCloud/photos/actions/runs/42420657616), [documentation compilation #42420669299](https://github.com/GoreeCloud/photos/actions/runs/42420669299), [web compilation and loopback static checks #42420671316](https://github.com/GoreeCloud/photos/actions/runs/42420671316), and [SDK/plugin/Nest server compilation #42420673174](https://github.com/GoreeCloud/photos/actions/runs/42420673174) all **passed**. [Post-merge main source integrity #42420823966](https://github.com/GoreeCloud/photos/actions/runs/42420823966) passed separately. No documentation or app deployment was performed.
- The [pnpm advisory inventory #42420675378](https://github.com/GoreeCloud/photos/actions/runs/42420675378) correctly **failed** on residual advisories. Full workspace: **1 critical / 33 high / 27 moderate / 9 low**. Pnpm production-dependency scope (which includes the inherited docs site): **0 critical / 25 high / 24 moderate / 6 low**. The remaining full-workspace critical entry is a tar advisory reached through the development/test dependency chain. Advisory counts do not prove actual exploitability, nor do they certify complete security of any deployed service.
- PR #18 proposed a narrower package-scoped override but overlapped the already merged candidate and was closed without merging; a separate future change can evaluate the narrower selector with fresh frozen builds. The current global pin is tested against this source, not an unconditional policy for future dependency additions.

**Gate remains open:** Wardveil must still triage and remediate remaining high findings, audit other language/container/mobile dependency graphs, and verify runtime authentication, privacy controls, media processing and recovery before any Stable/deployment decision.


## Brace-expansion 1.x security patch — scoped build accepted, advisory gate open

The full and production pnpm audit reports multiple high-severity advisory entries for brace-expansion. The imported lockfile contains version 1.1.15 as well as independent version 2.1.7 and 5.0.12 lines. The static ancestry analysis found version 1.1.15 in the documentation build toolchain and the server's development dependencies; some server runtime paths resolve a different major. **Presence in pnpm's production-dependency scope is not proof that an affected expansion path is reachable through the Photos service.**

The official [juliangruber/brace-expansion](https://github.com/juliangruber/brace-expansion) v1.1.15 and v1.1.20 package manifests and the [v1.1.15–v1.1.20 source comparison](https://github.com/juliangruber/brace-expansion/compare/v1.1.15...v1.1.20) were inspected. Version 1.1.20 retains MIT licensing, the same two dependencies, and adds vulnerability regression tests. The candidate uses a selector restricted to the **1.x line** so it does not replace unrelated v2.x/v5.x dependencies. This is a patch-line update, but a vulnerable expansion library may have behavioral security changes: no compatibility is presumed without verification.

Only metadata-only lockfile resolution is performed locally, with install lifecycle scripts disabled. Acceptance was conditional on exact source SHA, read-only integrity, isolated docs/web/server frozen-lockfile builds and updated full/production pnpm advisory results; the scoped results are recorded below. Do not mark Wardveil security, app service functionality, real user data handling or release readiness complete.


### Verified brace-expansion 1.x source/build evidence — November 7, 2026

- [PR #20](https://github.com/GoreeCloud/photos/pull/20) merged the version-scoped 1.1.20 override into [main 4e253ed](https://github.com/GoreeCloud/photos/commit/4e253edb62eb882f77da7bcfa8379825c31ffba4), replacing only the old 1.1.15 lockfile snapshot/minimatch edge; independent 2.1.7 and 5.0.12 resolution branches are preserved.
- Exact candidate branch hosted [source integrity #42421450008](https://github.com/GoreeCloud/photos/actions/runs/42421450008), [Docusaurus docs compile #42421461718](https://github.com/GoreeCloud/photos/actions/runs/42421461718), [web compile and static HTTP #42421463662](https://github.com/GoreeCloud/photos/actions/runs/42421463662), and [SDK/plugin/Nest backend compile #42421465504](https://github.com/GoreeCloud/photos/actions/runs/42421465504) all **passed**. [Post-merge main source checks #42421558813](https://github.com/GoreeCloud/photos/actions/runs/42421558813) passed. No application server or personal media was used.
- The [full/production dependency advisory query #42421467418](https://github.com/GoreeCloud/photos/actions/runs/42421467418) deliberately **failed** with residual findings. Full pnpm workspace: **1 critical / 28 high / 27 moderate / 9 low**. Production dependency scope (including docs): **0 critical / 20 high / 24 moderate / 6 low**. Compared with prior same-day scan, both scopes report five fewer high entries. Advisory count changes require per-advisory verification and are not a guarantee of complete security.
- Continue prioritized review of web/server high-severity dependencies, the remaining development/test tar critical, and independent Python/Rust/Flutter/containers security and licensing. No user data, application runtime, backup/recovery or deployment is accepted.


## follow-redirects 1.16.2 security candidate — pending isolated validation

The November 7 registry scan on the baseline GoreeCloud Photos workspace reported three high-severity advisories for follow-redirects 1.16.0 (GHSA-8r9p-f939-6h3c, GHSA-mrwp-f3q8-3g9p, GHSA-q3jh-wrc6-jgq8). A static lockfile dependency edge reaches this library via http-proxy 1.18.1; the upstream docs build/webpack development server is an important candidate consumer. The edge itself does not establish that the actual Photos web/server runtime exposes vulnerable HTTP redirects.

The official [follow-redirects upstream project](https://github.com/follow-redirects/follow-redirects), the [v1.16.0-to-v1.16.2 source comparison](https://github.com/follow-redirects/follow-redirects/compare/v1.16.0...v1.16.2) and published v1.16.0/v1.16.2 manifests were examined. The maintained 1.x patch line retains MIT licensing, no external runtime dependencies and no install lifecycle scripts. The patch introduces sensitive-header and redirect-handling changes with updated tests. This is an explicitly scoped dependency-compatibility candidate, not proof of exposure in a deployed instance.

Regenerate only the pnpm lockfile metadata with lifecycle scripts disabled; no user media or production service is used. Acceptance requires source-integrity, frozen-lockfile documentation/web/server builds and a full/production registry advisory comparison on the exact candidate SHA. Other findings, the full-workspace tar critical and Wardveil release gate remain open.


### Verified follow-redirects security patch — November 7, 2026

- [PR #22](https://github.com/GoreeCloud/photos/pull/22) merged the MIT-licensed follow-redirects 1.16.2 patch into [main 924404c](https://github.com/GoreeCloud/photos/commit/924404c53acf7d584154f2cda1aa0d24dab611b4), replacing the old 1.16.0 snapshot and http-proxy edge without modifying unrelated packages.
- Exact-head hosted [source integrity #42422931858](https://github.com/GoreeCloud/photos/actions/runs/42422931858), [Docusaurus docs compilation #42422939992](https://github.com/GoreeCloud/photos/actions/runs/42422939992), [web build and loopback HTTP #42422942013](https://github.com/GoreeCloud/photos/actions/runs/42422942013), and [SDK/plugin/Nest server compilation #42422944780](https://github.com/GoreeCloud/photos/actions/runs/42422944780) passed. [Post-merge main source CI #42423063185](https://github.com/GoreeCloud/photos/actions/runs/42423063185) passed separately. No application server or personal media was used.
- The [pnpm advisory query #42422946452](https://github.com/GoreeCloud/photos/actions/runs/42422946452) **failed** with residual findings: full workspace **1 critical / 25 high / 27 moderate / 9 low**; pnpm production-dependency scope (including docs) **0 critical / 17 high / 24 moderate / 6 low**. Both scopes reported three fewer high findings than the prior baseline. Registry advisory counts and compilation checks do not establish real Photos runtime safety.

## Joi v17 security candidate — awaiting isolated build and advisory acceptance

The full and production-scope pnpm advisory inventory reports two high-severity Joi findings (GHSA-4528-x5fx-h6hg and GHSA-6h2x-m376-mqjq) against 17.13.4. Static lockfile parent edges point to Docusaurus types and validation tooling. There is no evidence yet that these code paths are reachable from a deployed Photos authentication or media API.

The official [hapijs/joi](https://github.com/hapijs/joi) v17.13.4/v17.13.9 manifests and [upstream source comparison](https://github.com/hapijs/joi/compare/v17.13.4...v17.13.9) show an unchanged BSD-3-Clause license, identical runtime dependency declarations and backported security tests addressing prototype/message keys and email parsing complexity. The package has a prepublishOnly build script but no install lifecycle hooks; all imported package installs are nevertheless performed with scripts disabled. A patch-line pin to 17.13.9 is narrower than a major version change but cannot be assumed compatible without documentation/web/server compilation.

The candidate uses metadata-only pnpm resolution and awaits exact-source static tests, manual frozen-lockfile Docusaurus/web/server builds and a full/production advisory count comparison. Keep release, Wardveil vulnerability triage, user-media testing, privacy and data-recovery gates open.


### Verified Joi security patch — November 7, 2026

- [PR #23](https://github.com/GoreeCloud/photos/pull/23) merged the Docusaurus Joi 17.13.9 patch in [main f5672d7](https://github.com/GoreeCloud/photos/commit/f5672d728e565fe6eba9b5fb4a5b16f957831d2c), without changing its runtime dependency declarations.
- Exact-head hosted [source integrity #42423274342](https://github.com/GoreeCloud/photos/actions/runs/42423274342), [Docusaurus docs compile #42423285822](https://github.com/GoreeCloud/photos/actions/runs/42423285822), [web compile #42423288288](https://github.com/GoreeCloud/photos/actions/runs/42423288288), and [SDK/plugin/Nest server compile #42423290786](https://github.com/GoreeCloud/photos/actions/runs/42423290786) passed, as did [post-merge main integrity #42423396735](https://github.com/GoreeCloud/photos/actions/runs/42423396735).
- The [advisory scan #42423293198](https://github.com/GoreeCloud/photos/actions/runs/42423293198) **failed** with remaining findings: full pnpm workspace **1 critical / 23 high / 26 moderate / 7 low**; pnpm production scope including docs **0 critical / 15 high / 23 moderate / 4 low**. The two reported Joi high entries no longer appeared in this scan. Do not infer completed app cybersecurity from registry advisory totals.

## Body-parser 1.x docs-chain patch — source/build accepted, security gate open

The inherited lockfile contains body-parser 1.20.6 through Express 4.22.2 and a separately resolved body-parser 2.4.0 through Express 5/server. The registry reports GHSA-27r3-jxmh-p828 as high for the 1.x version. The exact Express 4 dependency path must not be confused with the deployed Photos server's direct 2.x dependency. The official [expressjs/body-parser](https://github.com/expressjs/body-parser) 1.20.6/1.20.9 manifests, MIT license, and [upstream 1.20.6-to-1.20.9 source comparison](https://github.com/expressjs/body-parser/compare/1.20.6...1.20.9) were reviewed. The patch line updates compressed-body handling and its qs dependency version range; tests cover trailing bytes after compression. No install lifecycle hook is declared.

The candidate uses a **major-scoped 1.x override** to retain the server's direct body-parser 2.4.0, with metadata-only lockfile regeneration and scripts disabled. This minor-compatible update remains a candidate until exact-source static integrity, isolated documentation/web/server frozen-lockfile builds and a fresh full/prod registry scan are reviewed. Wardveil, personal data, app runtime, staging and deployment gates remain open.


### Verified body-parser 1.x security patch evidence — November 7, 2026

- [PR #24](https://github.com/GoreeCloud/photos/pull/24) merged the selector-scoped body-parser 1.20.9 security patch as [main 181c87a](https://github.com/GoreeCloud/photos/commit/181c87ad7ba498bdf42bdc8e482c0368b4905787). The inherited Express 4 docs/tooling path resolves 1.20.9 with its updated qs dependency; the Photos server's direct Express 5/body-parser 2.4.0 resolution is unchanged.
- The exact patch SHA passed [source integrity #42423613550](https://github.com/GoreeCloud/photos/actions/runs/42423613550), [Docusaurus docs build #42423623708](https://github.com/GoreeCloud/photos/actions/runs/42423623708), [web compilation and local static HTTP #42423625948](https://github.com/GoreeCloud/photos/actions/runs/42423625948), and [SDK/plugin/Nest server compilation #42423628000](https://github.com/GoreeCloud/photos/actions/runs/42423628000). [Post-merge source CI #42423766702](https://github.com/GoreeCloud/photos/actions/runs/42423766702) also passed.
- Independent [pnpm advisory #42423630074](https://github.com/GoreeCloud/photos/actions/runs/42423630074) **failed as intended** with remaining findings: full workspace **1 critical / 22 high / 26 moderate / 7 low**; pnpm production scope (including docs) **0 critical / 14 high / 23 moderate / 4 low**. One fewer high entry in each scope than the prior scan. These are registry advisory counts, not proof of runtime exploitability.
- The remaining full-workspace critical tar advisory belongs to the development/e2e dependency graph. Any major-version or dependency-tree update requires source review, protected lockfile changes, separate frozen builds and test coverage before acceptance. Other high alerts, unsupported platforms, privacy, authorization, real media handling and backup/restore remain release-blocking.
