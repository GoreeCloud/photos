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
