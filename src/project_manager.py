"""
State manager for HDL-FSM-Editor.
This module provides a simple way to access application state throughout the application.
"""

from project import Project


class ProjectManager:
    """Simple project manager - just holds the state and provides access."""

    def __init__(self) -> None:
        self._project = Project()
        # File management
        self._current_file: str = ""
        self._previous_file: str = ""
        self._entry_widgets: list = []  # To store references to entry widgets

    @property
    def entry_widgets(self) -> list:
        """Get the list of entry widgets."""
        return self._entry_widgets

    @entry_widgets.setter
    def entry_widgets(self, value: list) -> None:
        """Set the list of entry widgets."""
        self._entry_widgets = value

    # @property
    # def project(self) -> Project:
    #     """Direct access to the project state."""
    #     return self._project

    @property
    def current_file(self) -> str:
        """Get the current file path."""
        return self._current_file

    @current_file.setter
    def current_file(self, value: str) -> str:
        """Set the current file path."""
        self._current_file = value

    @property
    def previous_file(self) -> str:
        """Get the previous file path."""
        return self._previous_file

    @previous_file.setter
    def previous_file(self, value: str) -> str:
        """Set the previous file path."""
        self._previous_file = value

    def get(self, attr_name: str, default=None):
        """Get a state attribute."""
        return getattr(self._project, attr_name, default)

    def set(self, attr_name: str, value) -> None:
        """Set a state attribute."""
        setattr(self._project, attr_name, value)

    def update(self, **kwargs) -> None:
        """Update multiple state attributes."""
        for key, value in kwargs.items():
            self.set(key, value)

    def reset(self) -> None:
        """Reset state to initial values."""
        self._project = Project()
        self._current_file = ""
        self._previous_file = ""


project_manager = ProjectManager()
