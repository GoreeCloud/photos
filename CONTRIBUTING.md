# Contributing to GoreeCloud Photos

GoreeCloud Photos is a **development-stage, attributed Immich derivative**, not an official Immich project. Contributions must preserve the [AGPL-3.0 license](LICENSE), existing copyright notices, upstream provenance and third-party attribution.

## Before proposing changes

- Use a focused branch and pull request; do not commit secrets, photographs, credentials, identifiers or real-user metadata.
- Inspect relevant third-party source, dependencies, scripts and permissions before execution. Do not run inherited installers or Docker Compose against private media for early development tests.
- Keep compatibility-sensitive identifiers and schema changes deliberate and tested rather than applying global text replacement.
- Use the verified [GoreeCloud UI design authority](https://github.com/GoreeCloud/gc-ui) and [official Photos brand assets](https://github.com/GoreeCloud/brand-assets/tree/main/products/photos).
- Preserve the upstream application source and [import provenance](docs/GOREECLOUD-IMPORT-PROVENANCE.md). The [original Immich contributing guide](docs/UPSTREAM-CONTRIBUTING.md) is historical upstream documentation, not current GoreeCloud contribution policy.

## Read-only source integrity checks

Run: python3 -m unittest discover -s tests/goreecloud -p 'test_*.py' -v

These tests use only Python's standard library and Git metadata. They intentionally do not execute Immich source or fetch dependencies. Review [release gates](docs/GOREECLOUD-RELEASE-GATES.md) before enabling broader builds or tests.

## Security and privacy

Do not publish exploit details, user records or credentials in public issues or pull requests. Coordinate sensitive findings privately with the repository owner through an authorized private channel. Repository visibility and passing static checks do not certify deployment safety.
