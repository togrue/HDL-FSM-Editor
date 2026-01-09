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

global_actions_clocked_number = 0
global_actions_combinatorial_number = 0
state_actions_default_number = 0


def insert_global_actions_clocked(event) -> None:
    global global_actions_clocked_number
    if global_actions_clocked_number == 0:  # Only 1 global action is allowed.
        project_manager.global_action_clocked_button.config(state=tk.DISABLED)
        global_actions_clocked_number += 1
        _insert_global_actions_clocked_in_canvas(event)
        undo_handling.design_has_changed()


def _insert_global_actions_clocked_in_canvas(event) -> None:
    canvas_grid_coordinates_of_the_event = (
        canvas_editing.translate_window_event_coordinates_in_rounded_canvas_coordinates(event)
    )
    _create_global_actions_clocked(canvas_grid_coordinates_of_the_event)


def _create_global_actions_clocked(canvas_grid_coordinates_of_the_event) -> None:
    ref = global_actions.GlobalActions(
        canvas_grid_coordinates_of_the_event[0], canvas_grid_coordinates_of_the_event[1], height=1, width=8, padding=1
    )
    ref.tag()


def insert_global_actions_combinatorial(event) -> None:
    global global_actions_combinatorial_number
    if global_actions_combinatorial_number == 0:  # Only 1 global action is allowed.
        project_manager.global_action_combinatorial_button.config(state=tk.DISABLED)
        global_actions_combinatorial_number += 1
        _insert_global_actions_combinatorial_in_canvas(event)
        undo_handling.design_has_changed()


def _insert_global_actions_combinatorial_in_canvas(event) -> None:
    canvas_grid_coordinates_of_the_event = (
        canvas_editing.translate_window_event_coordinates_in_rounded_canvas_coordinates(event)
    )
    _create_global_actions_combinatorial(canvas_grid_coordinates_of_the_event)


def _create_global_actions_combinatorial(canvas_grid_coordinates_of_the_event) -> None:
    ref = global_actions_combinatorial.GlobalActionsCombinatorial(
        canvas_grid_coordinates_of_the_event[0], canvas_grid_coordinates_of_the_event[1], height=1, width=8, padding=1
    )
    ref.tag()


def insert_state_actions_default(event) -> None:
    global state_actions_default_number
    if state_actions_default_number == 0:  # Only 1 global action is allowed.
        project_manager.state_action_default_button.config(state=tk.DISABLED)
        state_actions_default_number += 1
        _insert_state_actions_default_in_canvas(event)
        undo_handling.design_has_changed()


def _insert_state_actions_default_in_canvas(event) -> None:
    canvas_grid_coordinates_of_the_event = (
        canvas_editing.translate_window_event_coordinates_in_rounded_canvas_coordinates(event)
    )
    _create_state_actions_default(canvas_grid_coordinates_of_the_event)


def _create_state_actions_default(canvas_grid_coordinates_of_the_event) -> None:
    ref = state_actions_default.StateActionsDefault(
        canvas_grid_coordinates_of_the_event[0], canvas_grid_coordinates_of_the_event[1], height=1, width=8, padding=1
    )
    ref.tag()
