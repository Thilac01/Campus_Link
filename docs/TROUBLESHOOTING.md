# Troubleshooting

## Application does not start

Confirm the virtual environment is active and `python -c "import PySide6"` succeeds. Reinstall with
`python -m pip install -e .`. Inspect `%LOCALAPPDATA%\CampusLink\logs\campuslink.log` without sharing
personal data.

## Reset a development profile

Set `CAMPUSLINK_DATA_DIR` to a new empty directory rather than deleting an existing profile. This
preserves evidence and avoids accidental data loss.

## Network features are unavailable

This is expected in Phase 1. The interface reports Local mode, and all network-dependent modules
are disabled. Do not change firewall or campus network policy to enable unfinished functionality.

## Display or scaling issue

Use Windows recommended display scaling and update graphics/Qt packages. Record Windows version,
scale percentage, monitor layout, and a screenshot when reporting the problem.

