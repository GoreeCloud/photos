# GoreeCloud Photos — Scoped Parser Advisory Preflight

**Date:** November 8, 2026
**Candidate baseline:** public source cbad4c427aff2bf844f605a9ee9d7a17aeaf4a8c
**Status:** Candidate only; exact-hosted CI and registry scans still required.

As the GoreeCloud founder, I require a narrowly scoped and verifiable response to inherited parser advisories. I do not approve forced across-major upgrades, unreviewed installation scripts, changes to real family media or a declaration that this source snapshot is production safe.

## Current evidence and candidate

The November 8 source-lockfile pnpm scan reports 16 moderate advisories overall. This candidate addresses several inherited documentation/build-tool chains without redesigning the Photos API:

| Package | Existing | Candidate | Scope |
| --- | --- | --- | --- |
| brace-expansion | 1.1.20 | 1.1.21 | Only v1, retaining independent v2.1.7 and v5.0.12 |
| qs | 6.15.3 | 6.16.1 | Only the Express 4 dependency edge; other existing qs 6.16.1 edges retained |
| colord | 2.9.3 | 2.9.4 | Existing v2 |
| postcss-selector-parser | 6.1.4 and 7.1.5 | 6.1.5 and 7.1.6 | Each original major separately |

Official source comparisons and published manifests were inspected for target versions. The brace-expansion 1.1.21 upstream change specifically limits repeated rewriting of the pathological brace pattern (GHSA-q2hr-2g5m-vwhr). The qs changes include bounds on bracket-key/comma parsing and unsafe stringification input. The PostCSS selector parser updates address quadratic parsing, while colord improves oversized malformed color rejection. Published licenses remain MIT for brace-expansion, colord and both PostCSS versions; qs is BSD-3-Clause. Some upstream development scripts include prepare/prepublish commands; the candidate pnpm lockfile update used **--lockfile-only --ignore-scripts** with isolated HOME and cleared auth variables. No lifecycle script or unknown upstream code was executed locally.

Only expected package integrity metadata and directly affected edges should change. The scoped selector must preserve patched brace-expansion 2.x/5.x and all unrelated Express 5 qs edges.

A new bounded synthetic Node regression exercises upstream brace expansion semantics with a 12,000-brace malformed pattern, a maxRewrites escape hatch, qs comma parsing and prototype protection, malformed colord input, and v6/v7 CSS selector API compatibility. An external 12-second timeout in the existing manually triggered documentation workflow prevents indefinitely hanging a disposable runner. **This is not adversarial fuzzing or a full browser/server runtime security test.**

## Mandatory acceptance and release limits

Require exact candidate SHA source CI, synthetic timed regression, frozen independent docs/web/server builds, and full/production pnpm advisory rescan before merging. Any unresolved advisory remains visible and audit red. Review the imported code and documentation asset licenses separately, and preserve real photo authorization, authentication, GoreeShield retention/consent, Wardveil defense, recovery, and deployment gates as OPEN.

## First hosted regression correction

The first PR #38 documentation workflow failed because our synthetic malformed-brace test expected exactly two outputs. The official 1.1.21 patch test asserts bounded processing and maxRewrites behavior for that input, not a specific output count. The amended test now checks a nonempty result and retains bounded duration, maxRewrites behavior and an external 12-second timeout. Only a new exact-head hosted run can accept the candidate.

The second hosted attempt reached qs and revealed another incorrect fixture assumption: when arrayLimit is 1, two bracket-index inputs are deliberately represented as an **object** rather than an array. The test now asserts that bounded behavior. It also checks that no prototype mutation occurs without claiming a particular object shape, and counts three tag selectors (section, a, img) in the PostCSS sample. These changes align assertions with existing documented APIs, without disabling any checks or external timeout. Fresh hosted results are still required.
