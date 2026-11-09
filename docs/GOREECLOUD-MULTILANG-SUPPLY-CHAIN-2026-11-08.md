# GoreeCloud Photos — Multi-Ecosystem Supply-Chain Preflight

**Date:** November 8, 2026
**Product:** GoreeCloud Photos
**Baseline:** Public GoreeCloud/photos main cbad4c427aff2bf844f605a9ee9d7a17aeaf4a8c
**Maturity:** Read-only static review; **release blocked**.

As the GoreeCloud founder, I require privacy-first, auditable and recoverable software. Passing the Node.js advisory scan does not certify my machine-learning models, Rust codecs, Flutter mobile clients, Docker images, native plugins, or uploaded media.

## Verified source-lockfile observations

An isolated authorized checkout was inspected without running imported packages or downloading model artifacts. The Python standard-library verifier in scripts/goreecloud/inspect_multilang_supply_chain.py audits only recorded source, artifact digest and Git commit pin metadata.

| Ecosystem | Verified recorded inventory | Status |
| --- | --- | --- |
| Python uv machine learning | 127 package entries, 1,531 wheels/sdists, 1 pinned Git source, three registry hosts | **16 wheel entries lacking SHA-256** for one optional OpenVINO nightly package |
| Rust Cargo native codecs | 112 entries, 108 registry dependencies with SHA-256 checksums, one Git source pinned by full commit | Metadata pinned where supported; code, license and vulnerability review still required |
| Flutter root | 258 packages: 242 hosted with hashes, five Git sources with full resolved commit hashes, eight SDK and three local packages | Five Git-source code reviews remain open |
| Flutter UI | 24 entries: 21 hosted with hashes and three SDK packages | Hash metadata present; full code/runtime review open |
| Dockerfiles | Five Dockerfiles with 17 external base-image references containing SHA-256 digests | Digest metadata present; image contents and CVE scans unverified |

**Important distinction:** The 16 missing OpenVINO hashes refer to 16 platform-specific wheel entries for one nightly package, not 16 separately proven vulnerabilities. This gap prevents reproducibility acceptance for that optional accelerator configuration. Five Flutter Git sources, one Python model Git source, and one Rust codec Git source are commit-pinned but still need provenance, permission and license reviews. Digest-pinned images can still contain vulnerable software.

## Enforcement and scope

The verifier uses only Python's standard library (TOML and constrained pub-lockfile indentation parsing). It does not install packages, execute imported code, access private photos, build images, or contact registries. It emits JSON with blockers and separate review-only findings. Default reporting exits normally; its --enforce mode returns exit code 2 when missing artifact hashes or unpinned sources are detected, and 3 for unreadable/unsupported metadata. Source-integrity tests assert this known blocked state.

The isolated .github/workflows/goreecloud-multilang-supply-chain.yml workflow is owner-triggered only, using pinned Checkout, no persisted credentials or submodules, read-only contents permission and a disposable Ubuntu runner. It runs enforcement, so the workflow is expected to remain **RED by design** while the missing OpenVINO hashes persist. A later green result would establish only metadata guard success, not complete Wardveil supply-chain approval.

## Next acceptance gates

1. Verify a reproducible and supported source of OpenVINO wheel hashes, independently review their provenance and confirm optional accelerator compatibility. Do not invent hashes or silently drop the accelerator feature.
2. Audit the pinned model, codec and Flutter Git source, scripts, permissions, licenses and security advisories through controlled ecosystem tooling.
3. Scan pinned base-image digests and built images, including upstream Immich base-server images and accelerator variants, with reproducible builds, backups and rollback.
4. Execute authenticated server, synthetic photo upload/reimport/delete/share, storage and recovery, mobile, GoreeShield privacy and Wardveil network-isolation tests before any release.

**Not established:** Full package provenance, third-party attestations, vulnerability coverage beyond metadata checks, malicious-code absence, runtime security, user-data privacy, deployment readiness or consent to process real private photographs.
