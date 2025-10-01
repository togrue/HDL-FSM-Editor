"""
Window geometry utilities.

Simple utilities for window geometry and state handling.
"""

import tkinter as tk
from typing import Union


def restore_window_state(window: tk.Tk, state: Union[dict[str, str], None]) -> bool:
    """Restore window geometry and state from settings."""
    if not state:
        return False

    # Check if saved geometry would be visible
    if "geometry" in state and not _is_geometry_visible(state["geometry"]):
        print("Warning: Saved window position would not be visible on current screen setup")
        return False

    return _apply_window_state(window, state)


def get_window_state(window: tk.Tk) -> Union[dict[str, str], None]:
    """Get window geometry and state as strings."""
    try:
        return {"geometry": window.geometry(), "state": window.state()}
    except Exception:
        return None


def _apply_window_state(window: tk.Tk, state: dict[str, str]) -> bool:
    """Apply saved window geometry and state."""
    try:
        if "geometry" in state:
            window.geometry(state["geometry"])
        if "state" in state and state["state"] in ["zoomed", "iconic"]:
            window.state(state["state"])
        return True
    except Exception:
        return False


def _is_geometry_visible(geometry_str: str) -> bool:
    """Check if geometry string would be visible on current screen."""
    try:
        # Parse geometry to get position
        parts = geometry_str.split("+")
        if len(parts) < 2:
            return True  # Assume visible if we can't parse

        x = int(parts[1])
        y = int(parts[2]) if len(parts) > 2 else 0

        # Get virtual screen dimensions (includes all monitors)
        root = tk.Tk()
        root.withdraw()
        vroot_x = root.winfo_vrootx()
        vroot_y = root.winfo_vrooty()
        vroot_width = root.winfo_vrootwidth()
        vroot_height = root.winfo_vrootheight()
        root.destroy()

        # Check if position is within virtual screen bounds
        # This works for multi-monitor setups where coordinates can be negative
        # or extend beyond the primary monitor dimensions
        return vroot_x <= x < vroot_x + vroot_width and vroot_y <= y < vroot_y + vroot_height
    except Exception:
        return True  # Assume visible if we can't determine
