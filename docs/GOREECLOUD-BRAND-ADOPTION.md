# GoreeCloud Photos — First-party Web Icon Adoption

This is a bounded web/PWA asset replacement, **not full application rebranding** or visual acceptance.

## Source authority

- Canonical central source: https://github.com/GoreeCloud/brand-assets/tree/main/products/photos
- Official SVG: products/photos/app-icon.svg, Git blob 3231d720b1ae17a2c49f4d58e98c60acd331118a.
- Original asset index: products/photos/raster/asset-index.json, checked against all nine generated raster files.
- Design authority: https://github.com/GoreeCloud/gc-ui
- The first-party artwork is GoreeCloud-owned; inherited Immich art in the remaining upstream sources is subject to separate brand and asset-rights review.

## Implemented web files

| Web path | Source / transformation | SHA-256 |
| --- | --- | --- |
| web/static/icon.svg | Unmodified official app-icon.svg | cedeb508dc4a68875bfd40d495ae38ef9869bf615c0b02d4e2b569b6473bb3fb |
| web/static/favicon.ico | Unmodified raster/favicon.ico | e2f8f74c7ec727ca52759dd973560346a89fee1764d827e77ee79577c556e0b8 |
| web/static/goreecloud-photos-192.png | Unmodified raster/icon-192.png | 33ca452348119cfc3e085362084a7a4425a55159f989170a801a2d1bf08562bf |
| web/static/goreecloud-photos-512.png | Unmodified raster/icon-512.png | 03f9c527e95ab553a9b54cc1943743a8bba2e3757835b61befa3fe0c1dddfa19 |
| web/static/apple-icon-180.png | Raster/icon-512.png downsampled to 180px using Pillow 10.2.0 LANCZOS | b151decee7e040ec32e3f3d07e427415f2a1738766a4bc918b45fd4e08f334f2 |

The PWA manifest points at the 192px/512px first-party icons. Its icon purpose is **any**, not maskable, because an independently accepted mask-safe padded export is not yet documented. The two original Immich PWA raster files were removed from the active web static directory; the upstream source commit remains linked in the provenance record.

## Acceptance boundary

The GitHub source and local checks verify files and metadata only. Real favicon appearance, platform installation banners, browser caching, responsive layouts, alternative themes, accessibility and native mobile app icons require separate runtime testing. Do not claim full GoreeCloud UI adoption or external client delivery from this stage.
