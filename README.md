# CampusLink

CampusLink is a local-first university communication and collaboration desktop application.
This repository contains the desktop foundation plus an initial authenticated peer messaging
slice and resumable transfer engine. It is not production-ready.

## Implemented

- PySide6 three-column desktop shell with accessible light/dark solid-surface themes.
- First-run local profile setup with clear unverified-identity language.
- Atomic local settings, persistent window size, privacy-preserving defaults.
- SQLite schema and migration ledger for planned product entities.
- Structured JSON file logging.
- Versioned, bounded, length-prefixed protocol framing abstraction.
- Safe transfer destination path validation.
- Persistent per-device certificates and explicit fingerprint trust records.
- TLS 1.3 peer transport with pinned server identity and challenge-response client authentication.
- Working one-to-one message exchange, delivery acknowledgement, and local history.
- Bounded, pauseable, cancellable, resumable, SHA-256-verified file processing off the UI thread.
- Unit tests for persistence, framing, settings, and path validation.

Automatic discovery, peer bulk-channel negotiation, folder transfer, groups, screen sharing,
remote assistance, location, voice, relay, installer, signing, and updates remain planned and
intentionally unavailable. The File Transfers page currently validates the local streaming engine;
it does not claim that the selected destination is a remote peer.

## Run on Windows

Use Python 3.11 or newer. From PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
campuslink
```

If `py -3.12` is unavailable, use a locally installed supported Python, for example
`python -m venv .venv`. Application data is stored in `%LOCALAPPDATA%\CampusLink`.
For isolated local instances, set `CAMPUSLINK_DATA_DIR` before launching each process.

```powershell
$env:CAMPUSLINK_DATA_DIR = "$PWD\.runtime\user-a"
campuslink
```

Run tests with `pytest`. See [Developer Guide](docs/DEVELOPER_GUIDE.md) and
[Testing](docs/TESTING.md).

## Status

Version 0.2.0. Automated tests cover the current identity, transport, message, and transfer
primitives, with an offscreen UI construction check on Windows. No benchmark, security audit,
installer test, or clean-machine validation has yet been claimed.
