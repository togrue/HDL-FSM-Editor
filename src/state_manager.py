"""
State manager for HDL-FSM-Editor.
This module provides a simple way to access application state throughout the application.
"""

from project import Project


class StateManager:
    """Simple state manager - just holds the state and provides access."""

    def __init__(self):
        self._project = Project()

    @property
    def project(self) -> Project:
        """Direct access to the project state."""
        return self._project

    def get(self, attr_name: str, default=None):
        """Get a state attribute."""
        return getattr(self._project, attr_name, default)

    def set(self, attr_name: str, value):
        """Set a state attribute."""
        setattr(self._project, attr_name, value)

    def update(self, **kwargs):
        """Update multiple state attributes."""
        for key, value in kwargs.items():
            self.set(key, value)

    def reset(self):
        """Reset state to initial values."""
        self._project = Project()


# Global instance (only global variable we keep)
state_manager = StateManager()
