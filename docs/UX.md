# GoreeCloud Photos — Purpose-led UI and UX

**Product principle:** Every GoreeCloud application's UI and UX must communicate and serve its particular purpose. GoreeCloud Photos should feel like a photo library, not an analytics dashboard, generic file explorer, chat client, or settings console.

## Photos-specific interaction contract

- Lead with the owner's pictures and videos in a responsive, touch-friendly gallery; keep import, search, favorites, albums, and reversible trash close to the media.
- Present images in visual tiles with accessible filenames, and offer native, deliberate actions for previews and saving originals.
- Group the web gallery by **UTC import date** from `created_at`. This is not a capture-time timeline; capture metadata is not extracted, inferred, or shared.
- Keep operational metrics available but secondary: web storage/library statistics live behind an accessible, keyboard-operable **Library details** disclosure.
- Protect privacy through on-demand authenticated thumbnail loading, no public object URLs, no tracking, no default indexing of local device media, and no silent metadata or facial analysis.
- Respect GoreeCloud UI's already verified centralized tokens for fonts, color, spacing, focus, and states. The shared design language remains the authority; the media-first information hierarchy is the application-specific expression.
- Treat native accessibility (screen readers, visible focus, appropriate semantic headings/labels), responsive layouts, and low-resource devices as release-acceptance requirements rather than assumptions.

## Implemented versus unverified

The web gallery has source-implemented image-first responsive tiles, adjacent UTC import-day sections, accessible media actions, and collapsed library metrics. Linux uses its native Qt Quick gallery with responsive visual tiles; Android uses Jetpack Compose with opt-in foreground imports. These three experiences are not claimed to be identical or fully accepted.

Before production: visually review representative real libraries, keyboard Tab order, contrast, photo crop behavior, small screens, dynamic text sizes, TalkBack/Orca/NVDA, zoom and reduced-motion preferences. Never interpret the existence of CSS/QML or passing static CI as proof of accessibility or real-device usability.
