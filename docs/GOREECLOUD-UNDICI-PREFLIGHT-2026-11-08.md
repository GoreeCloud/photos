# Undici v8.12.2 security preflight — November 8, 2026

**Status: candidate, NOT merged or production accepted.**

Baseline: GoreeCloud/photos a76372c, 0 critical and 6 high pnpm advisory entries. Four high entries correspond to undici 8.11.2 in node-gyp and testcontainers chains: GHSA-2m5v-pch6-74hx (TLS verifier option loss), GHSA-4w7w-5xrc-9h26 (cross-origin shared-cache confusion), GHSA-qrxm-fqhp-jwvm (TLS renegotiation crash), GHSA-xjj6-f33q-929c (excessive content-encoding crash). Runtime reachability in Photos is not established.

Official [nodejs/undici v8.11.2...v8.12.2](https://github.com/nodejs/undici/compare/v8.11.2...v8.12.2) has 81 commits, including parser/WASM and Agent/TLS/cache changes. [Upstream security release](https://github.com/nodejs/undici/releases/tag/v8.12.2) describes additional medium fixes. MIT, Node >=22.19; the existing isolated workflows use Node 24. This is targeted package review, not exhaustive source verification or proof that binary assets are safe. No package lifecycle script ran during lockfile resolution.

Candidate: parent-major-scoped undici@8 mapping to v8.12.2 changes only the node-gyp and testcontainers transitive edges and single package integrity. pnpm metadata resolved in isolated HOME with auth env cleared and scripts ignored. A new 15-second-bounded synthetic loopback-only HTTP test checks that a cache composed after a redirect cannot poison a trusted response from another origin. It uses no real service, photos, credentials, external endpoints, or database. It covers only the redirect/cache advisory, not TLS or HTTP parser behavior.

Require exact-head GitHub source CI, frozen docs/web/server builds, E2E TypeScript plus bounded cache test, and independent full/production pnpm registry audit before merge. Residual advisories and all privacy, authentication, media and deployment release gates remain open.
