"""
Core settings storage functionality.

Handles JSON-based persistent storage with platform-appropriate paths.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional


class SettingsStorage:
    """Handles persistent storage of application settings."""

    def __init__(self, app_name: str = "HDL-FSM-Editor", config_name: str = "settings.json"):
        self.app_name = app_name
        self.config_name = config_name
        self.settings_file: Optional[Path] = None
        self._settings: dict[str, Any] = {}
        self._dirty = False
        self._loaded = False

    def _get_settings_path(self) -> Path:
        """Get platform-appropriate settings file path."""

        if self.settings_file is not None:
            return self.settings_file

        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA", "")
            settings_dir = Path(appdata) / self.app_name if appdata else Path.home() / ".config" / self.app_name
        elif sys.platform == "darwin":
            settings_dir = Path.home() / "Library" / "Application Support" / self.app_name
        else:
            settings_dir = Path.home() / ".config" / self.app_name

        self.settings_file = settings_dir / self.config_name
        return self.settings_file

    def _load_settings(self) -> None:
        """Load settings from file."""
        try:
            with self._get_settings_path().open(encoding="utf-8") as f:
                self._settings = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Could not load settings: {e}")
            self._settings = {}
        self._loaded = True

    def save_settings(self) -> None:
        """Save settings to file."""
        if not self._dirty:
            return
        try:
            self._get_settings_path().parent.mkdir(parents=True, exist_ok=True)
            with self._get_settings_path().open("w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
            self._dirty = False
        except OSError as e:
            print(f"Warning: Could not save settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get setting value using dot notation."""
        if not self._loaded:
            self._load_settings()

        keys = key.split(".")
        value = self._settings

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """Set setting value using dot notation."""
        if not self._loaded:
            self._load_settings()
        self._dirty = True
        keys = key.split(".")
        current = self._settings

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value
