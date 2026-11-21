"""Application paths and durable user settings."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

APP_NAME = "CampusLink"


def app_data_dir() -> Path:
    """Return a per-user data directory without relying on the working directory."""
    override = os.environ.get("CAMPUSLINK_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    base = os.environ.get("LOCALAPPDATA")
    if base:
        return Path(base) / APP_NAME
    return Path.home() / ".campuslink"


@dataclass(slots=True)
class AppSettings:
    theme: str = "system"
    notifications_enabled: bool = True
    show_message_preview: bool = False
    discoverable: bool = False
    window_width: int = 1280
    window_height: int = 800

    @classmethod
    def from_mapping(cls, values: dict[str, Any]) -> AppSettings:
        allowed = {field.name for field in cls.__dataclass_fields__.values()}
        return cls(**{key: value for key, value in values.items() if key in allowed})


class SettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or app_data_dir() / "settings.json"

    def load(self) -> AppSettings:
        try:
            values = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(values, dict):
                return AppSettings()
            return AppSettings.from_mapping(values)
        except (FileNotFoundError, json.JSONDecodeError, OSError, TypeError):
            return AppSettings()

    def save(self, settings: AppSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
        temporary.replace(self.path)

