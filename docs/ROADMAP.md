# GoreeCloud Photos — Development Roadmap

**Status:** development preview, not a production or Anchor release. Planned items are not implemented unless listed as verified in [FEATURES.md](FEATURES.md).

## Near-term: security and recoverability
- Verify local and representative real-device workflows for Android and Linux, including denied permissions and accessibility.
- Add independently testable backup verification and recovery drills; establish encrypted off-device copies and owner-approved recovery procedures. The existing archive is manual and unencrypted.
- Add read-only/administrative first-party CLI support with documented credential handling; maintain automated CLI checks.
- Harden untrusted media handling, ingress limits, authorized sessions, and deployment defaults.
- Keep mandatory protected-branch checks and all clients compiling across changes.

## Subsequent: privacy-first media management
- Add more interoperable image/video formats after format decoders and sandboxing are validated.
- Improve duplicate-aware import, resumability, offline access, and opt-in background sync.
- Expand native album actions, media preview, accessibility, translations and platform packaging.
- Design intentional multi-user/family access with concrete GoreeCloud Identity contracts and least privilege.

## Integration prerequisites
- **GoreeCloud UI:** continue reusing verified `gc-ui` tokens and assess native interfaces against the approved design system.
- **GoreeShield:** establish enforceable consent, privacy, retention and disclosure contracts rather than claiming integration.
- **Wardveil:** align media validation, audit and threat-response controls with an actual supported contract.
- **GoreeCloud Mesh:** design explicit opt-in sync and event API contracts, never broadcast private photos by default.
- **GoreeCloud Identity:** currently lacks a verified standalone integration source or contract; authentication remains local-only.

## Release gates
No production or Anchor designation until required MIPS integration applicability, authorization review, encrypted recovery testing, signed distribution, real-device verification, and security acceptance have evidence. Track open gaps in [GitHub issues](https://github.com/GoreeCloud/photos/issues).
