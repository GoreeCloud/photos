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


## Controlled experimental build mechanism (pending)

An owner-triggered (workflow_dispatch-only) GitHub Actions workflow stages Node 24 and pnpm@12.16.1 on a disposable Ubuntu 24.04 runner. It checks out source without submodules/persistent GitHub credentials; installs lockfile dependencies with --ignore-scripts; attempts only the inherited web Vite build; and verifies exported web icon/PWA assets byte-for-byte against approved source. The workflow uses contents: read, no secrets, no cache and no deployment targets.

Source review before enabling: root package scripts are formatting-only; the inherited pnpmfile hook contains a package-manifest rewrite for exiftool-vendored dependencies; web build script invokes Vite; Vite configuration imports SvelteKit, Tailwind and image plugins, plus a local CSP manifest writer. Indirect dependencies, plugins and generated output are not fully reviewed, so the disposable runner and read-only credentials are required safeguards. The build is **not** a production-security approval.

Inherited web Vite development configuration currently permits all dev-server Hosts and contains upstream product/payment URLs. Do not expose that dev server publicly or interpret upstream purchase links as GoreeCloud-approved. Review and replace such links before interface release.

### Isolated web build iteration — November 7, 2026

The initial manual experiment failed at Vite/Rolldown module resolution for @immich/sdk, not dependency installation. The SDK is a local TypeScript workspace package whose entrypoints are generated by its explicit tsc build; disabled install lifecycle scripts mean its outputs must be built deliberately. Remediation invokes the existing reviewed @immich/sdk build script before web compilation. See the release-gate document for evidence. No production installation or personal media was involved.

### Isolated build recovered; static HTTP check pending

After the SDK-first correction in Photos PR #4, owner-triggered GitHub Actions run #42416035395 succeeded in the sandboxed dependency install, SDK compile, web compile and generated PWA/brand-file validation. A separate read-only loopback HTTP script now tests serving the compiled static shell, manifest and official images from Python's standard library; this is a bounded asset delivery check, not a real browser/UI/API/backend test or deployment. Remaining dependency provenance, vulnerability and privacy gates remain open.


### Independent server compile experiment — pending

A new owner-dispatched-only server compile workflow isolates pnpm lockfile installation (with lifecycle scripts disabled), local SDK TypeScript compilation, plugin SDK bundling and declaration generation, and inherited Nest server build in a disposable Ubuntu runner. The Nest build is compilation only. Source-review scope: plugin SDK esbuild.js bundles two local TypeScript source entrypoints into dist without explicit network or subprocess calls; plugin package build also runs TypeScript and local import-alias rewriting. The package manager and toolchain dependencies remain third-party inputs without full security acceptance. The workflow must not use production secrets, access personal photos, run a database or serve the application. Compiled outputs are statically inspected but not evaluated or launched. No claim of successful build until GitHub hosted run succeeds.


### Hosted compilation results — November 7, 2026

The manually triggered [server compile #42417305584](https://github.com/GoreeCloud/photos/actions/runs/42417305584) passed all steps: pnpm lockfile installation with lifecycle scripts disabled, local SDK and plugin SDK builds, Nest server compilation, and generated entrypoint checks without running services or attaching storage. The updated-source [web build and loopback delivery #42417477789](https://github.com/GoreeCloud/photos/actions/runs/42417477789) also passed all steps on main 459a87b. Neither test used real user media or production credentials, but both executed inherited third-party build dependencies on disposable hosted runners. These are bounded build checks, not comprehensive dependency or runtime security reviews; CVE triage, legal review, and integration validation remain required.


### Read-only registry advisory triage (not yet executed)

A new owner-triggered workflow performs pinned pnpm 12.16.1 audit JSON reporting against the current lockfile without installing dependencies, running package lifecycle scripts, changing versions or applying fixes. It uses a disposable runner, pinned read-only GitHub Actions and no private media. The parser requires complete nonnegative per-severity counts and fails closed on malformed output or nonzero audit exit codes. Public advisory databases are incomplete by nature, so a green scan is not proof of complete source safety. This scan covers only pnpm packages; Python uv, Flutter/Dart, Rust, container images, Git submodules and licensed assets need separate review. The authenticated GitHub Dependabot-alerts endpoint was not accessible during preflight; do not infer that there are zero alerts.
