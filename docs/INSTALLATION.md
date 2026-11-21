# Installation

## Developer installation (current)

Install a supported 64-bit Python and run the PowerShell commands in the README. PySide6 is a
required runtime dependency. The first launch creates `%LOCALAPPDATA%\CampusLink` and shows the
local-profile wizard.

Windows may block script activation. For a temporary session-only policy:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## End-user installer (planned)

No installer or signed executable exists in Phase 1. Phase 10 will compare PyInstaller and Nuitka,
build an Inno Setup or WiX installer, create shortcuts/uninstall support, document firewall rules,
sign releases, and validate on a clean Windows VM. Users must not be told that Python is unnecessary
until that artifact is built and tested.

