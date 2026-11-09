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


### First lockfile advisory evidence and scoped rerun — November 7, 2026

- [Initial full-workspace pnpm audit #42418045175](https://github.com/GoreeCloud/photos/actions/runs/42418045175) found **5 critical, 40 high, 31 moderate and 13 low advisory entries** among inherited pnpm workspace dependencies. The run deliberately **failed** the audit gate. These are registry advisory counts, not evidence that every entry is exploitable in GoreeCloud Photos; no production application exists.
- The next bounded owner-triggered revision separately queries all workspace dependencies and pnpm's production-dependency scope. It prints only a small, sanitized critical/high advisory sample (public package, advisory identifier, and published fix range) without echoing advisory prose or installing dependencies. This allows targeted package ownership and affected-version triage before any proposed upgrades.
- The counts and sample do not establish completeness of public vulnerability databases, applicability of individual advisories, or permission to apply unreviewed automated fixes. Preserve this gate as open until all material findings are assessed and appropriately remediated or explicitly accepted with evidence.


### Confirmed production-scope advisory inventory — November 7, 2026

[GitHub Actions run #42418292059](https://github.com/GoreeCloud/photos/actions/runs/42418292059) reported 4 critical, 32 high, 28 moderate and 10 low advisory entries in pnpm's production-dependency scope, compared with 5 critical, 40 high, 31 moderate and 13 low across the full workspace. The audit gate deliberately failed. The [detailed dependency triage](GOREECLOUD-DEPENDENCY-TRIAGE-2026-11-07.md) documents inspected source paths and initial remediation ordering, distinguishing documentation tooling from actual web/server dependency reachability. No vulnerabilities were suppressed, automatically fixed or declared non-exploitable.


### Targeted fast-uri lockfile update and validation — November 7, 2026

[Photos PR #12](https://github.com/GoreeCloud/photos/pull/12) merged a source-reviewed pin of fast-uri 3.1.9 and its regenerated lockfile after clean [web](https://github.com/GoreeCloud/photos/actions/runs/42419436543), [server](https://github.com/GoreeCloud/photos/actions/runs/42419438716) and [static](https://github.com/GoreeCloud/photos/actions/runs/42419422022) checks. The manual [post-patch audit #42419440996](https://github.com/GoreeCloud/photos/actions/runs/42419440996) reported 5 critical/34 high/28 moderate/11 low entries overall and 4 critical/26 high/25 moderate/8 low in pnpm production scope; **audit still failed as intended**. These are advisory counts, not independently proven exploitability. Other dependency ecosystems and remaining pnpm advisories require further review; no broad Wardveil release clearance.


### Documentation-chain DOMPurify/shell-quote build verification — November 7, 2026

[PR #14](https://github.com/GoreeCloud/photos/pull/14) pinned dompurify 3.4.17 and shell-quote 1.11.0 from reviewed upstream releases. Frozen web and server builds passed on the exact patch head; the separately triggered [post-merge Docusaurus build #42420206414](https://github.com/GoreeCloud/photos/actions/runs/42420206414) passed and its static HTML output was checked without serving/publishing it. The [scope-separated registry audit #42420071308](https://github.com/GoreeCloud/photos/actions/runs/42420071308) still **failed** with full workspace 3 critical/33 high/27 moderate/9 low and pnpm production scope 2 critical/25 high/24 moderate/6 low. These results are advisory counts, not complete security clearance; docs branding remains inherited and not approved for deployment.


### Tinypool docs-chain build and advisory milestone — November 7, 2026

[PR #17](https://github.com/GoreeCloud/photos/pull/17) merged v2.2.0 for inherited Docusaurus Tinypool following passing frozen-lockfile [docs](https://github.com/GoreeCloud/photos/actions/runs/42420669299), [web](https://github.com/GoreeCloud/photos/actions/runs/42420671316), and [server](https://github.com/GoreeCloud/photos/actions/runs/42420673174) compilation and [source integrity](https://github.com/GoreeCloud/photos/actions/runs/42420657616). The independent [advisory rerun #42420675378](https://github.com/GoreeCloud/photos/actions/runs/42420675378) intentionally remained red: full workspace 1 critical/33 high/27 moderate/9 low; pnpm production dependency scope 0 critical/25 high/24 moderate/6 low. No old Tinypool 1.1.1 snapshot remains. The remaining full-workspace critical tar advisory relates to development/test tooling and needs independent threat/compatibility review. No system is deployed and no broader Wardveil security acceptance is implied.


### Brace-expansion 1.x major-scoped patch evidence — November 7, 2026

[PR #20](https://github.com/GoreeCloud/photos/pull/20) merged a backported brace-expansion v1.1.20 security fix after green [docs](https://github.com/GoreeCloud/photos/actions/runs/42421461718), [web](https://github.com/GoreeCloud/photos/actions/runs/42421463662), [server](https://github.com/GoreeCloud/photos/actions/runs/42421465504) and [source checks](https://github.com/GoreeCloud/photos/actions/runs/42421450008); existing 2.x/5.x major lines were not modified. The [advisory rerun #42421467418](https://github.com/GoreeCloud/photos/actions/runs/42421467418) remains red: full workspace 1 critical/28 high/27 moderate/9 low, pnpm production scope 0 critical/20 high/24 moderate/6 low. This is remediation/build evidence, not proof of runtime exploitability or production security acceptance.


### follow-redirects inherited http-proxy patch — November 7, 2026

[PR #22](https://github.com/GoreeCloud/photos/pull/22) merged follow-redirects 1.16.2 in the existing 1.x line, with green source/docs/web/server checks. The [scope-separated registry audit #42422946452](https://github.com/GoreeCloud/photos/actions/runs/42422946452) still failed: full workspace 1 critical/25 high/27 moderate/9 low; pnpm production scope 0 critical/17 high/24 moderate/6 low. These are advisory entry counts, not a security clearance or proof of deployed exposure.


### Joi 17.x documentation-toolchain security patch — November 7, 2026

[PR #23](https://github.com/GoreeCloud/photos/pull/23) merged Joi 17.13.9 after passing hosted [source](https://github.com/GoreeCloud/photos/actions/runs/42423274342), [docs](https://github.com/GoreeCloud/photos/actions/runs/42423285822), [web](https://github.com/GoreeCloud/photos/actions/runs/42423288288), and [server](https://github.com/GoreeCloud/photos/actions/runs/42423290786) compilation/integrity checks. The [advisory rerun #42423293198](https://github.com/GoreeCloud/photos/actions/runs/42423293198) remained red: full pnpm workspace 1 critical/23 high/26 moderate/7 low; pnpm production scope 0 critical/15 high/23 moderate/4 low. No runtime Photos service, user media or deployment was included.


### Express 4 body-parser 1.x targeted patch — November 7, 2026

[PR #24](https://github.com/GoreeCloud/photos/pull/24) merged a major-scoped body-parser 1.20.9 patch while preserving Photos server body-parser 2.4.0. Pinned, disposable [docs](https://github.com/GoreeCloud/photos/actions/runs/42423623708), [web](https://github.com/GoreeCloud/photos/actions/runs/42423625948), [server](https://github.com/GoreeCloud/photos/actions/runs/42423628000) and source checks passed. [Advisory run #42423630074](https://github.com/GoreeCloud/photos/actions/runs/42423630074) remained red: full 1 critical/22 high/26 moderate/7 low; production dependency scope (including inherited docs) 0 critical/14 high/23 moderate/4 low. No live service or private media was tested or deployed.


### E2E-only utimes / tar 6 native dependency elimination — November 8 candidate

Static dependency tracing identified the tar 6.2.1 critical advisory as E2E devDependencies → utimes 5.2.1 → @mapbox/node-pre-gyp 1.0.11. The only tracked direct package imports were five fixture timestamp adjustments. A candidate changes them to built-in fs.promises.utimes with Date-valued millisecond times and removes the obsolete native addon plus its disabled build allowlist item. Pnpm 12.16.1 lockfile-only, ignore-scripts resolution pruned 26 packages including tar 6.2.1 and retained tar 7.5.22 for server Node-gyp. Synthetic same-host timestamp checks and source integrity passed locally. **Hosted E2E TypeScript, docs/web/server builds, registry advisory rerun, database-backed E2E, and Stable release review are still required.** No real media or user data was read, modified or uploaded.


### E2E tar 6 critical elimination — source/build verified on November 8

[PR #30](https://github.com/GoreeCloud/photos/pull/30) merged native Node fs timestamp fixtures, removing the E2E-only utimes → node-pre-gyp → tar 6.2.1 dependency subtree while keeping tar 7.5.22. The [source](https://github.com/GoreeCloud/photos/actions/runs/42536693952), [docs](https://github.com/GoreeCloud/photos/actions/runs/42536717996), [web/static](https://github.com/GoreeCloud/photos/actions/runs/42536719832) and [server/E2E TypeScript/synthetic mtime](https://github.com/GoreeCloud/photos/actions/runs/42536714616) gates passed on the exact amended candidate. [Postmerge source](https://github.com/GoreeCloud/photos/actions/runs/42536902128) and [isolated standalone E2E typecheck](https://github.com/GoreeCloud/photos/actions/runs/42536934896) passed. The [registry audit](https://github.com/GoreeCloud/photos/actions/runs/42536722363) returned **zero critical** in both scopes but still **FAILED** for seven high in each, plus moderate/low entries. Database-backed E2E, real media, deployment, broader packages, privacy and Wardveil release acceptance remain unverified.


### Multi-ecosystem provenance guard / Node advisory milestone — November 8

[PR #36](https://github.com/GoreeCloud/photos/pull/36) added the source-only, least-privilege [multi-ecosystem metadata inspector](GOREECLOUD-MULTILANG-SUPPLY-CHAIN-2026-11-08.md). Its owner-triggered [main workflow #42543996816](https://github.com/GoreeCloud/photos/actions/runs/42543996816) **failed as designed** on 16 optional OpenVINO nightly wheel entries lacking SHA-256. The same source audit identified seven full-commit-pinned but not source-audited Git dependencies and SHA-pinned Dockerfile bases that still lack image content/CVE validation. No dependency installation, remote image pull, ML processing or real photos were involved.

[PR #38](https://github.com/GoreeCloud/photos/pull/38) closed another seven Node advisory entries following the verified [Mermaid/serializer patch PR #37](https://github.com/GoreeCloud/photos/pull/37). The [postmerge main pnpm registry audit #42545468680](https://github.com/GoreeCloud/photos/actions/runs/42545468680) remains **RED**: full 0 critical/0 high/4 moderate/5 low; production including docs 0/0/4 moderate/2 low. These registry counts do not validate actual Photos runtime, browser/media security, Python/Rust/Flutter exposure, immutable backups, permission controls, or deployment.
