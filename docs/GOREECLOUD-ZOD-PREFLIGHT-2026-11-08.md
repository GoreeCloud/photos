# Zod 4.6.6 security preflight — November 8, 2026

**Status: candidate, NOT merged or production accepted.**

High [GHSA-mrhx-c7xc-m3w5](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5) affects Zod 4.4.3 currently pinned directly by the Photos server. Oversized bounded array, Map, and Set inputs could accumulate invalid element issues before the limit check. This is relevant to schema validation but the actual Photos endpoint exposure is not established.

Official [Zod v4.4.3...v4.6.6](https://github.com/colinhacks/zod/compare/v4.4.3...v4.6.6) spans 327 commits, so this is NOT a trivial patch. Reviewed [upstream early size check](https://github.com/colinhacks/zod/commit/a0ebf970f2d752e5f58527cd2942ff48be4f46bd), adding checks before collection element parsing plus tests. Both manifests retain MIT with no runtime dependencies. The [upstream release note](https://github.com/colinhacks/zod/releases/tag/v4.6.6) reports malicious commits pushed with compromised Git credentials, later reverted, and states none were published to npm; this is a **vendor claim**, not independent package provenance proof. Preserve supply-chain skepticism and do not execute source scripts blindly.

Candidate updates the direct server package pin and transitive v4 resolution to 4.6.6. A bounded, synthetic Node guard verifies early max checks on 4096 array elements and small invalid Set/Map inputs, and nested error paths, without external requests or real media. Run under 12-second timeout inside manually triggered, credential-less server compilation CI. pnpm metadata resolved with isolated HOME, cleared auth env and lifecycle scripts disabled.

Require exact-head source CI, synthetic guard, Nest/SDK server compilation, frozen docs/web/E2E compatibility and full/production pnpm advisory audit. No real API or privacy/security/staging acceptance.


### Published artifact read-only inspection

A separate isolated npm registry lookup and npm pack of zod@4.6.6 were performed with lifecycle scripts disabled and no registry-auth environment. Registry and packaged manifests both identify MIT zod 4.6.6, with no runtime dependencies or preinstall/install/postinstall/prepare hooks. The registry exposes package integrity metadata and attestations (presence checked, NOT independently verified cryptographically). Its gitHead is 284243fb0d6532665afdc9239188773bb624f73c, matching the pre-rewrite commit identified in the vendor release note. The packed archive had 840 entries including 124 JS files and no bin/postinstall path flagged by the narrow filename scan. This does not constitute a full malicious-code/source-to-tarball reproducibility review.
