"""
Application state for HDL-FSM-Editor.
This module contains the single state class that holds all application data.
"""

from dataclasses import dataclass


@dataclass
class Project:
    """Simple application state - everything in one place."""

    # Project settings
    module_name: str = ""
    language: str = "VHDL"
    generate_path: str = ""
    working_directory: str = ""
    file_count: int = 1
    reset_signal_name: str = "reset"
    clock_signal_name: str = "clk"
    compile_command: str = ""
    edit_command: str = ""

    # File management moved to StateManager
