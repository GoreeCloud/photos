# GoreeCloud Photos — Objectives

**Product objective:** provide a user-controlled, privacy-first, self-hosted photo and video collection with first-party browser, Linux-native and Android-native applications.

## Measurable engineering outcomes

1. **Ownership and portability.** Keep originals and index owned by the self-hosting user, with exportable archive contents and transparent schemas. Maintain backup and restore verification with isolated recovery tests.
2. **Privacy.** Avoid analytics, unconsented scans, public media URLs and implicit third-party uploads. Scope access to explicit authenticated actions; make media collection opt-in on devices.
3. **Security.** Validate ingress and file types, bound resource use, use robust local password/token boundaries, retain protected GitHub main and passing real CI checks.
4. **Quality.** Require tests for authenticated reads/writes, duplicates, restore and concurrency; test native GUI launch and the Android build in CI, with separate physical-device acceptance.
5. **Interoperability.** Implement actual GoreeCloud UI, GoreeShield, Wardveil, Identity and Mesh contracts where applicable; record non-integrated areas accurately and retain offline fallback.
6. **Maintainability.** Keep code, configuration, scripts, documentation, licensing and workflows in the public [GoreeCloud/photos](https://github.com/GoreeCloud/photos) repository, with explicit third-party attribution and reviewable changes.

## Evidence required before release

A working test on a private HTTPS test deployment, actual supported Android and Linux hardware, reproducible signed packaging, bounded security review, clean licensing review, documented disaster recovery with encrypted off-host copies, and independently verified applicable MIPS contracts. None is inferred from source existence or passing CI alone.
