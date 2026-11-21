# Developer Guide

The package is split into `app` bootstrap/configuration, `database`, `network`, `security`, and
`ui`. Widgets may call application services but must not own sockets or long-running disk work.
Network and transfer code must expose typed events and remain independently testable.

## Setup and checks

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
ruff check .
mypy campuslink
pytest
campuslink
```

Use `CAMPUSLINK_DATA_DIR` for disposable instances. Never commit runtime databases, keys, logs, or
received files. Add schema evolution as numbered, transaction-safe migrations; never mutate a
released schema without an upgrade path. Public functions require type hints and focused tests.

When adding a protocol message, update its schema/state transition, size bounds, parser tests,
threat model, and protocol document together.

