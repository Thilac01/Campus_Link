"""Safe destination path handling for future folder transfers."""

from __future__ import annotations

from pathlib import Path, PurePosixPath


class UnsafePathError(ValueError):
    pass


def safe_destination(root: Path, relative_path: str) -> Path:
    protocol_path = PurePosixPath(relative_path)
    if not relative_path or protocol_path.is_absolute() or ".." in protocol_path.parts:
        raise UnsafePathError("Transfer path must be relative and cannot contain '..'")
    if any(":" in part or part in {"", "."} for part in protocol_path.parts):
        raise UnsafePathError("Transfer path contains an unsafe component")
    resolved_root = root.resolve()
    candidate = resolved_root.joinpath(*protocol_path.parts).resolve()
    if candidate != resolved_root and resolved_root not in candidate.parents:
        raise UnsafePathError("Transfer path escapes the approved destination")
    return candidate

