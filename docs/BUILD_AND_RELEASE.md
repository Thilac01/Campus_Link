# Build and Release

Executable packaging, installer generation, code signing, and the updater are **planned**, not
implemented. The release pipeline must:

1. Run lint, types, unit/integration/security/UI tests on a clean pinned environment.
2. Produce an isolated Windows build and software bill of materials.
3. Scan dependencies and review licenses.
4. Build an installer with application metadata, uninstall, and shortcuts.
5. Sign binaries and installer using a protected signing identity.
6. Publish a separately signed semantic-version update manifest and artifact hashes.
7. Test install, upgrade, rollback, database migration, and uninstall on clean Windows machines.

The running application must never replace itself. A dedicated updater will verify the manifest
signature and artifact before launching a user-confirmed installer. Signing secrets must not enter
source control or ordinary CI logs.

