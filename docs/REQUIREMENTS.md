# Phase 0–1 Requirements

## Functional acceptance

1. First launch requests a display name and optional local profile fields.
2. The interface presents the required three-column navigation model and resizes without blocking.
3. Light, dark, and system appearance modes use solid surfaces and persist.
4. Profile, settings, schema version, and future entity tables persist locally.
5. Unimplemented modules are visibly disabled and cannot imply functionality.
6. Logs are structured and stored in the per-user application data directory.
7. Protocol framing handles partial/multiple reads and rejects invalid lengths and versions.

## Non-functional acceptance

- No network, disk-heavy, or future transfer operation occurs on the Qt UI thread.
- Defaults minimize disclosure: no discovery, location, or notification preview.
- Application data does not depend on the launch working directory.
- Phase 1 tests cover configuration, database, framing, and safe paths.
- No production, encryption, benchmark, signature, or installer claim is made without evidence.

## Dependency selection

| Dependency | Purpose | Rationale | License review |
|---|---|---|---|
| Python 3.11+ | runtime | typed asyncio and maintained Windows runtime | PSF; verify release support |
| PySide6 6.x | desktop UI | official Qt binding, native widgets, accessibility/high-DPI | LGPL/commercial; comply before distribution |
| SQLite | local storage | transactional, embedded, mature | public domain |
| pytest / pytest-qt | development tests | established Python and Qt test tooling | verify pinned release metadata |

Versions and licenses must be rechecked from primary sources before a public release; this table is
not a completed legal review. Future candidates (cryptography, mDNS, WebRTC/media, keyring,
packaging) require ADRs and compatibility prototypes before selection.

