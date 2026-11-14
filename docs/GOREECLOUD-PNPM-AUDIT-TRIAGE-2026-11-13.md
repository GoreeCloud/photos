# Photos pnpm advisory diagnostics — November 13, 2026

**Status:** narrowly scoped diagnostic change on a review branch; no dependency upgrades, security approval, real media processing or deployment.

The November 9, 2026 owner-triggered [pnpm advisory CI run](https://github.com/GoreeCloud/photos/actions/runs/42545468680) failed safely. It reported **full workspace: 5 low, 4 moderate, 0 high, 0 critical** and **production scope: 2 low, 4 moderate, 0 high, 0 critical**. These are upstream registry metadata counts, **not** a claim of exploitability or exhaustive security coverage.

The existing summary script previously printed advisory identity examples only for high/critical severity. This meant its logs supplied only counts for the current moderate/low findings, making package triage unnecessarily difficult.

This patch preserves the **fail-closed** audit gate and the existing strict metadata-count parser, but prints up to 12 sanitized, severity-ordered public advisory identity samples across **all** severity levels when the pnpm JSON includes suitable `advisories` entries. If none are present, logs explicitly state that identities were unavailable rather than implying there are no findings.

The workflow remains **manual `workflow_dispatch` only**, uses no package install or lockfile changes, exports no untrusted advisory narrative text, and does not publish output as a release artifact. Manual rerun is required to learn which package/advisory identities the current registry supplies. Review every proposed dependency upgrade for license, source, functionality and compatibility before adoption.

**Release gate remains OPEN:** dependency audit nonzero and privacy/security, media decoder, assets, backend, mobile, ML, native, containers, independent real-device checks and recovery still require work. Do not point this import at actual photo libraries.
