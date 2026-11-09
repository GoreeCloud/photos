# serialize-javascript v7.0.3 security preflight — November 8, 2026

**Status: breaking-major candidate, NOT merged or production accepted.**

High [GHSA-5c6j-r48x-rmvq](https://github.com/advisories/GHSA-5c6j-r48x-rmvq) affects the inherited serializer 6.0.2 under copy-webpack-plugin and css-minimizer-webpack-plugin. A crafted RegExp.flags or spoofed Date ISO response can lead to injection if later-executed JavaScript is serialized using attacker input. The actual Photos runtime exposure is not established; the observed dependency path is documentation/webpack build tooling.

Reviewed official [v6.0.2...v7.0.3](https://github.com/yahoo/serialize-javascript/compare/v6.0.2...v7.0.3) source, 21 commits and upstream regression fixtures. Version 7.0.3 retains BSD-3-Clause, raises Node minimum to 20, removes randombytes in favor of crypto.getRandomValues, sanitizes regexp flags and checks Date ISO strings. Its major change may alter behavior in inherited webpack plugins, hence compilation is mandatory. Hosted CI uses Node 24. No imported package scripts run in local metadata resolution.

Candidate overrides only inherited v6 serializer consumers to 7.0.3 and updates both webpack plugin parent references. An own 12-second-bounded synthetic no-eval test passes spoofed RegExp and Date objects, asserts no direct injection strings in output, and verifies ordinary primitives/regex serialization. It explicitly never evaluates generated JavaScript or uses personal data.

Require exact-head source CI, bounded smoke and Docusaurus build, frozen web/server/E2E checks, and independent pnpm full/production advisory scan. Remaining Wardveil/GoreeShield, authentication, media, license and deployment requirements remain blocked.
