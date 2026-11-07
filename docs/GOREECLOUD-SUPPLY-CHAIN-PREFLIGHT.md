# GoreeCloud Photos — Static Supply-Chain Preflight

**Date:** November 7, 2026.
**Scope:** Tracked import snapshot of Immich main 87ef895041e160aef4f61f2d7af1ad3f8e38827d and the GoreeCloud hardening changes. This is limited source/configuration inspection, **not a comprehensive malware/vulnerability/secret scan** and not a runtime security assessment.

## Observed dependency and automation surfaces

| Component | Read-only observation | Status |
| --- | --- | --- |
| Root JS workspace | pnpm@12.16.1 specified; root package.json has two formatting scripts | Lockfile and scripts not executed |
| Web app | 48 dependencies and 44 development dependencies declared in web/package.json | Install, audit and build pending |
| Server | 81 dependencies and 47 development dependencies declared in server/package.json | Install, audit and build pending |
| Machine learning | Python pyproject.toml and uv.lock present | Dependency/provenance review pending |
| Mobile | Flutter pubspec.lock, Android Gradle and iOS Podfile.lock present | Native toolchain and permissions review pending |
| Native/Rust | Cargo.lock present | Build, license and audit pending |
| Upstream GitHub Actions | 27 workflow files retained only under docs/upstream-github-workflows | Quarantined, not evaluated individually |
| Upstream Renovate | Imported configuration inherited local immich-app/.github automation | Archived; not active at root |
| GitHub issue/discussion/release routing | Imported templates referenced Immich issue routing and product naming | Archived, replaced with neutral GoreeCloud routing |
| External test assets | Git submodule pointer to immich-app/test-assets | Pin preserved, contents not fetched or reviewed |
| Deployment infrastructure | deployment/.env has three op:// secret-manager references and one shell variable expression | References only, **not raw credentials**, but deployment script not executed or accepted |

## Security observations

1. The inspected deployment/.env values for the Cloudflare account, Cloudflare token and Terraform state connection fields use **op:// references** rather than literal credentials. No credential values were displayed, fetched, expanded or executed in this review. A password-manager reference is not evidence that an authorized secret exists or that deployment is safe.
2. Quarantining inherited automation prevents accidental execution or imported product-specific review routing. The new single GitHub Actions workflow requests only repository read permission and invokes the bounded standard-library source integrity suite.
3. The verified GoreeCloud Photos web icons derive from centrally published first-party assets. Remaining embedded upstream assets and third-party notices require a complete license/trademark review.
4. Importing upstream containers, installation scripts, published packages, images or lockfiles does not establish their safety. No execution or download of unreviewed dependencies occurred in this preflight.

## Next checks before expanding CI

- Analyze lockfiles with independently reviewed, versioned scanners and triage critical/high findings rather than equating a scan result to acceptance.
- Inspect dependency lifecycle scripts, network endpoints, authorization flows and upload/file-processing entry points before enabling runtime tests.
- Use only synthetic, non-identifying photos/videos in isolated test environments; block public inbound access until reviewed.
- Review OAuth, token/session storage, file URLs, metadata privacy, retention, encrypted transport and database/backup behavior.
- Verify exact container/image provenance, mobile permissions, reproducible builds and rollback.
- Require explicit per-gate evidence in docs/GOREECLOUD-RELEASE-GATES.md before deployment.
