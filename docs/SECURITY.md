# Security and Threat Model

CampusLink is not yet security-audited and must not be described as production-ready. The current
transport uses established TLS and cryptography libraries, but the overall application has not had
an independent protocol or implementation review.

## Assets and boundaries

Assets include device private keys, message history, transferred files, profile data, session
consent, and update trust roots. Hostile peers and local networks are untrusted. The local OS user
and explicitly configured university relay are separate trust boundaries; a relay must not gain
message plaintext merely by routing traffic.

## Threats and planned controls

| Threat | Control |
|---|---|
| Impersonation / MITM | TLS 1.3, persistent device keys, fingerprint confirmation, key-change warning |
| Unauthorized pairing | explicit local confirmation, short-lived invitation, rate limits |
| Replay / duplication | unique IDs, authenticated session context, replay window, idempotency |
| Malformed or oversized input | strict schemas, 4 MiB control bound, bounded queues, timeouts |
| Directory traversal | normalized relative paths, approved root, symlink/overwrite policy |
| Remote-control abuse | separate session consent, visible state, revocation, emergency stop |
| Update tampering | pinned signing key, signed manifest, artifact hash/signature, rollback |
| Resource exhaustion | connection and peer rate limits, quotas, backpressure, disk-space checks |

## Privacy defaults

Discovery and location are off. Profiles are local and unverified. Notification previews are off.
Executables are never launched automatically. Screen capture and remote input require visible,
session-specific consent. Private keys are not stored in the application database, but the current
PEM key relies on inherited operating-system file ACLs. Windows-protected credential storage and a
key migration path are release blockers.

## Reporting

Do not place credentials, private keys, sensitive messages, or personal information in logs or
bug reports. Security reports should include the version, reproduction steps, and impact without
publishing exploit material before maintainers can respond.
