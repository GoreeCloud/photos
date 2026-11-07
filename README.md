# GoreeCloud Photos

**Rebranded Import** of [Immich](https://github.com/immich-app/immich) for GoreeCloud.

> **Development source baseline only. Not deployed or production-ready.**
>
> This is an attributed Immich derivative, not an independently authored replacement or an official Immich product. The initial rebrand covers repository identity, verified first-party web/PWA icons, display metadata and a browser fallback message; the application is NOT yet fully rebranded, integrated, tested or security-accepted.

## Purpose

GoreeCloud Photos is intended to deliver private, self-hosted photo and video management within GoreeCloud. The imported Immich source includes server, web, mobile and machine-learning components, but their presence does not establish verified GoreeCloud functionality or deployment.

## Source and provenance

- Upstream project and authors: [Immich contributors](https://github.com/immich-app/immich).
- Source branch: main (verified November 7, 2026).
- Imported commit: [87ef895041e160aef4f61f2d7af1ad3f8e38827d](https://github.com/immich-app/immich/commit/87ef895041e160aef4f61f2d7af1ad3f8e38827d).
- Import method: tracked source snapshot; original Git history is referenced, not copied.
- [Original upstream README](docs/UPSTREAM-README.md).
- [Import provenance, modifications and acceptance gates](docs/GOREECLOUD-IMPORT-PROVENANCE.md).

Internal package names, IDs, protocols, database layouts and many UI labels/assets remain upstream for compatibility, pending deliberate reviews.

## License and attribution

The original [LICENSE](LICENSE) is preserved. This derivative retains the GNU Affero General Public License v3.0 (AGPL-3.0), including applicable modification and network source-sharing obligations. Retain all file copyright headers and third-party notices. GoreeCloud does not claim upstream code authorship, Immich trademarks, logos or media ownership. Review rights for bundled assets and integrations before use or redistribution.

## Security, privacy and deployment

**Do not deploy or connect real photo libraries from this raw import.** Dependencies, startup scripts, workflows, permissions, storage, backup, migration, authentication and data retention have not passed independent review.

All 27 imported GitHub Actions workflows remain quarantined in [docs/upstream-github-workflows](docs/upstream-github-workflows); the upstream Renovate configuration and GitHub issue/discussion/release routing were also [archived](docs/upstream-repository-controls). The upstream root CODEOWNERS and contributing guide are preserved under docs. The only active GitHub Actions workflow performs [read-only, dependency-free import/branding checks](.github/workflows/goreecloud-source-checks.yml). Inherited setup scripts, application dependencies and containers have not been executed.

## Next milestones

1. Audit dependencies, license/asset rights, secrets, security and automation.
2. Continue verified GoreeCloud UI branding beyond the [official web/PWA icon adoption](docs/GOREECLOUD-BRAND-ADOPTION.md), and lawfully replace remaining upstream trademark-bearing assets.
3. Plan and validate GoreeCloud Identity, GoreeShield privacy, Wardveil security and GoreeCloud Mesh integration boundaries.
4. Test builds, authentication, installation, migration, backup/recovery, native mobile clients and accessibility using synthetic data.
5. Review the outcome of the [manual, isolated web compilation experiment](.github/workflows/goreecloud-web-build.yml); expand CI beyond the [static source integrity checks](.github/workflows/goreecloud-source-checks.yml) only with documented dependency and security acceptance.

See [release gates](docs/GOREECLOUD-RELEASE-GATES.md), the [supply-chain preflight](docs/GOREECLOUD-SUPPLY-CHAIN-PREFLIGHT.md), [GoreeCloud contribution guidance](CONTRIBUTING.md) and the [official web icon asset record](docs/GOREECLOUD-BRAND-ADOPTION.md). Original Immich instructions are at [docs.immich.app](https://docs.immich.app/) and are not validated GoreeCloud installation instructions.
