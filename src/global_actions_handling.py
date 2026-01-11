"""
All methods to handle the global actions block in the diagram.
"""

import tkinter as tk

import canvas_editing
import global_actions
import global_actions_combinatorial
import state_actions_default
import undo_handling
from project_manager import project_manager


def insert_global_actions_clocked(event) -> None:
    project_manager.global_action_clocked_button.config(state=tk.DISABLED)
    canvas_grid_coordinates_of_the_event = (
        canvas_editing.translate_window_event_coordinates_in_exact_canvas_coordinates(event)
    )
    global_actions.GlobalActions(
        canvas_grid_coordinates_of_the_event[0],
        canvas_grid_coordinates_of_the_event[1],
        height=1,
        width=8,
        padding=1,
        tags=("global_actions1",),
    )
    undo_handling.design_has_changed()


def insert_global_actions_combinatorial(event) -> None:
    project_manager.global_action_combinatorial_button.config(state=tk.DISABLED)
    canvas_grid_coordinates_of_the_event = (
        canvas_editing.translate_window_event_coordinates_in_exact_canvas_coordinates(event)
    )
    global_actions_combinatorial.GlobalActionsCombinatorial(
        canvas_grid_coordinates_of_the_event[0],
        canvas_grid_coordinates_of_the_event[1],
        height=1,
        width=8,
        padding=1,
        tags=("global_actions_combinatorial1"),
    )
    undo_handling.design_has_changed()


def insert_state_actions_default(event) -> None:
    project_manager.state_action_default_button.config(state=tk.DISABLED)
    canvas_grid_coordinates_of_the_event = (
        canvas_editing.translate_window_event_coordinates_in_exact_canvas_coordinates(event)
    )
    state_actions_default.StateActionsDefault(
        canvas_grid_coordinates_of_the_event[0],
        canvas_grid_coordinates_of_the_event[1],
        height=1,
        width=8,
        padding=1,
        tags=("state_actions_default",),
    )
    undo_handling.design_has_changed()
