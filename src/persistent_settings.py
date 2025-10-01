"""
Application settings management.

Simple interface for managing persistent application settings.
"""

from typing import Union

from settings_storage import SettingsStorage


class AppSettings:
    """High-level settings for the application."""

    def __init__(self, app_name: str = "HDL-FSM-Editor"):
        self._storage = SettingsStorage(app_name)

    def save_settings(self) -> None:
        """Save settings to file."""
        self._storage.save_settings()

    def set_main_window_state(self, state: dict[str, str]) -> None:
        """Save main window geometry to settings."""
        self._storage.set("main_window.state", state)

    def get_main_window_state(self) -> Union[dict[str, str], None]:
        """Load main window geometry from persistent settings."""
        state = self._storage.get("main_window.state")
        if not state:
            return None

        # Check if state is a dict and all keys and values are str
        if not (isinstance(state, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in state.items())):
            print("ERROR: main_window.state is not a dict[str, str] can't restore the window state")
            return None

        return state


# Global instance for convenience
app_settings = AppSettings()
