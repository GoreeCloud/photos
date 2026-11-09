# GoreeCloud Photos — Diagram and Serializer Advisory Preflight

**Date:** November 8, 2026
**Candidate baseline:** public source cbad4c427aff2bf844f605a9ee9d7a17aeaf4a8c
**Status:** Candidate in a review branch; do not treat as merged, production-tested or a deployed security fix.

As the GoreeCloud founder, I require inherited development and documentation tooling to retain its applicable licenses, compatibility, reproducibility and security. This review concerns a narrow Docusaurus documentation dependency cluster, not a claim that GoreeCloud Photos is safe for family photographs.

## Proposed dependency changes

The current advisory scan flags four **moderate** Mermaid 11.16.0 cases involving CSS injection, chart denial of service and architecture prototype pollution, and one **moderate** plus one **low** serialize-javascript 7.0.3 issue relating to crafted inputs and dangerous script closing sequences. Version 7.0.3 was previously accepted at source/build level for a separate high finding, but that does not cover subsequently reported issues.

The candidate advances Mermaid within the existing v11 line to **11.16.1** and serializer within v7 to **7.1.3**. The official comparisons reviewed were Mermaid 11.16.0 to 11.16.1 (15 commits, 34 changed files) and serialize-javascript 7.0.3 to 7.1.3 (18 commits, six changed files), including related tests and source patches. The npm registry manifests report MIT for Mermaid and BSD-3-Clause for serialize-javascript; serializer still requires Node >=20, while existing hosted compile uses Node 24. The reviewed changes are a limited source assessment, not a complete package attestation or malicious-code audit.

Metadata-only pinned pnpm resolution with lifecycle scripts disabled updates exactly the Mermaid documentation importer and two webpack-toolchain serializer parents; it does not alter the production Photos API, inherited license notices, stored media, databases or network services. The amended serializer smoke adds a spoofed function whose toString contains a closing script tag, and checks that the resulting serialized string cannot contain that unsafe literal. **The smoke never evaluates the output or loads third-party HTML.**

## Acceptance required before merging

- Exact GitHub source-integrity CI on the candidate SHA and the synthetic serializer guard.
- Frozen, isolated Docusaurus build plus web/static and server/SDK compilation, with E2E TypeScript compatibility where relevant.
- Full and production-scope pnpm advisory rescan, keeping the audit red if other findings persist.
- Evidence reconciliation after merging; no automatic production deployment or private-photo processing.

This patch is not a substitute for a browser XSS review, malicious diagram-input tests against a sandboxed browser, GoreeShield privacy/consent, Wardveil network/HTTP/media testing, backups, container scans, or Stable release acceptance.
