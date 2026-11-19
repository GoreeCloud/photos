# GoreeCloud MIPS integration status

| System | Contract for Photos | Current verified state |
|---|---|---|
| GoreeCloud UI | Semantic visual tokens, accessibility, responsive patterns | Web uses canonical `gc-ui` generated token CSS snapshot; native visual/device verification pending |
| GoreeCloud Mesh | Consent-bound photo events and interoperable export/import | Not connected; avoid silent event publishing |
| GoreeCloud Identity | OIDC/OAuth2 PKCE, least-privilege identities, household roles | Not connected; initial library-only auth |
| GoreeShield | Consent for photo backup, retention and sharing, privacy by default | No implicit uploads, no telemetry, originals private; formal enforcement/audit pending |
| Wardveil | File scanner, media isolation, threat intelligence, vulnerability gates | Bounded signature-checked upload and auth; integrated sandbox and scanner pending |

No external Photos, Ente, Immich, Google account or cloud storage connection is enabled.

## Recommended interoperability after controls
- EXIF GPS indexing only with explicit personal choice. Strongly isolate location data from unauthorized sharing.
- Archive import via user-supplied Google Takeout directories with sidecar JSON and duplicate previews, no account scraping.
- Optional Immich / Ente export import via supported formats, documented license terms and consent.
- GoreeCloud Mesh events should initially be local, bounded, idempotent, and disabled by default.

These are plans, not current implementations.
