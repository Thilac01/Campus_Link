# Changelog

## 0.2.0 - 2026-11-21

### Added

- Persistent device certificates, verification codes, trust/block records, and key-change checks.
- TLS 1.3 peer transport with certificate pinning and mutual challenge-response authentication.
- Functional secure Chat page with manual pairing, message delivery states, and history.
- Bounded resumable file processing with pause, cancellation, atomic completion, and SHA-256 checks.
- File Transfers UI that keeps disk work off the Qt thread.

### Security limitations

- Device key files currently rely on the application-data directory's operating-system ACLs;
  Windows credential protection is required before production distribution.
- Pairing is manual; automatic discovery and invitation/QR workflows are not yet implemented.
- Peer file bytes are not yet sent over a negotiated bulk channel.

## 0.1.0 - 2026-11-21

### Added

- Phase 0 requirements, architecture, protocol, threat model, UI, testing, and release documents.
- Phase 1 PySide6 shell, setup wizard, themes, settings, structured logging, and SQLite schema.
- Protocol framing and safe transfer-path primitives with unit tests.

### Known limitations

- Network, collaboration, media, relay, update, executable, and installer features are not yet implemented.
- Automated tests require development dependencies that are not bundled in the repository.
