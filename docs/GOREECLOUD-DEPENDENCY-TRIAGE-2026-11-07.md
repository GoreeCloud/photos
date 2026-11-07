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


## Tinypool documentation-chain major upgrade — candidate, pending validation

The next scoped patch proposes using tinypool 2.2.0 for the **@docusaurus/core dependency only**, replacing its vulnerable tinypool 1.1.1 resolution. The imported workspace already resolves tinypool 2.2.0 in the independent web/Lingui chain. The upstream v1.1.1-to-v2.2.0 source comparison includes the 2.1.1/2.1.2 worker-option prototype-pollution fixes and additional Worker compatibility tests; its MIT license remains unchanged, and package engine support moves to Node 20+ (the disposable CI uses Node 24). This is a **major version** and is not assumed compatible until the actual docs build and web/server regressions pass.

Only metadata/lockfile resolution is being changed; there is no user-data processing or production deployment. Hosted read-only advisory checks must independently verify whether both critical docs-chain entries disappear. Any static CI failure, frozen-lockfile resolution failure, documentation compilation failure or high-risk regression blocks merge, and all other advisories remain open.
