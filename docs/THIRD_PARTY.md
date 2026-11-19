# Third-party provenance and licensing

GoreeCloud Photos source is an independently authored implementation, licensed MIT. It does **not** copy the upstream Immich or Ente server/client code.

- **GoreeCloud UI:** `web/src/gc-ui-tokens.css` is a snapshot of the canonical generated CSS in [GoreeCloud/gc-ui](https://github.com/GoreeCloud/gc-ui) at commit `79949b3db58f2214e8d4c4eb2b647f75e1cfc724`, from `src/tokens.css`. It is MIT licensed, copyright (c) 2026 GoreeCloud. The MIT notice is retained in the root LICENSE. The CSS is an alpha design-token bridge, not a stable package.
- **FastAPI** (MIT), **Starlette** (BSD-3-Clause), **Uvicorn** (BSD-3-Clause), **Pillow** (HPND), **React** (MIT), **Vite** (MIT), **Qt for Python / Qt Quick** (open-source licensing varies by module; Qt 6.12 LGPL/GPL obligations), **Jetpack Compose** (Apache-2.0) are external build/runtime dependencies and retain their own source and license obligations.
- **Immich** and **Ente** are AGPL-3.0 upstream examples. No AGPL-licensed code has been copied. Mixing substantial AGPL portions into this MIT code would require a specific compatibility/provenance review and likely change distribution obligations. Do not cherry-pick their source without documented review.
- **libvips** (LGPL-2.1-or-later) is recommended for a future isolated media worker but is **not currently included or executed**.
- **FFmpeg** is recommended for future video processing only after inspecting configured codecs, license options and sandboxing; it is **not currently included or executed**.

Dependencies are package-managed, not vendored wholesale, to preserve upstream patchability and provenance. Their versions and transitive licenses must be re-audited and pinned in lockfiles before deployment.
