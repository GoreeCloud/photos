# GoreeCloud Photos — Verified Features and Gaps

This is a development-stage self-hosted photo library. Capabilities below describe implemented source paths; complete device and deployment acceptance has **not** been established.

| Capability | API | Web (React) | Linux (Qt Quick 6.12) | Android (Jetpack Compose) |
| --- | --- | --- | --- | --- |
| Password-based single-library session | Implemented | Implemented | Implemented | Implemented |
| Password rotation and all-session revocation | Implemented | Accessible masked change form | CLI companion only | Not yet |
| Revoke all sessions without changing password | Implemented | CLI companion only | CLI companion only | CLI companion only |
| Explicit JPEG/PNG/WebP/GIF/MP4 uploads | Implemented | Implemented | Implemented | Implemented |
| Private image thumbnails | Implemented | Implemented | Implemented | Implemented |
| Favorites and reversible trash | Implemented | Implemented | Implemented | Implemented |
| Filename search, filtering and pagination | Implemented | Implemented | Implemented | Implemented |
| Restore from trash | Implemented | Implemented | Implemented | Implemented |
| Albums | Full create/rename/delete/membership API | Create, rename, delete, add/remove | Browse, create, add/remove members | Browse, create, add/remove members |
| Original media read and partial-byte streaming | Implemented | Download/preview | Native private Save-original dialog | User-directed SAF export with SHA-256 verification |
| Duplicate preflight by SHA-256 | Implemented | Not yet | Not yet | Used in explicit folder import |
| Explicit folder import | Via ordinary uploads | File chooser only | File picker only | System document-tree picker, foreground-only |
| Offline backup and restore | Manual unencrypted CLI plus read-only verifier | Not applicable | Not applicable | Not applicable |
| Multi-user and GoreeCloud Identity SSO | Not implemented | Not implemented | Not implemented | Not implemented |
| Encrypted backups, client E2EE, opt-in background sync | Not implemented | Not implemented | Not implemented | Not implemented |

Original media still retains embedded metadata. Preview JPEGs strip EXIF. The server performs signature checks but does **not** fully validate MP4 decoding. Mobile import does not use blanket storage access, request persistent folder grants, or read camera rolls automatically.

**Verification boundary:** Required CI runs Python API tests/lint, TypeScript/Vite production build, pinned Qt 6.12 QML static analysis plus Python compilation, and Android debug builds. A separate manual workflow checks real Qt offscreen startup when Ubuntu EGL packages are available. A physical Android 16 debug-app install/launch/uninstall smoke passed using an authorized development handset, without opening any personal files. None of these certifies full device interaction, accessibility, production hardening, or recovery.

The `photosctl` first-party companion CLI is available for authenticated health/library/album operations, explicit upload/download, and offline backup/verify/restore. It stores no credentials locally, does not schedule backups, and does not embed a terminal inside the Android or browser app.
