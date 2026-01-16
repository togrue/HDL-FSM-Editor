"""
This module contains all methods for inserting states.
"""

from tkinter import messagebox

import canvas_editing
import constants
import state
import undo_handling
from project_manager import project_manager


def insert_state(event) -> None:
    event_x, event_y = canvas_editing.translate_window_event_coordinates_in_rounded_canvas_coordinates(event)
    if state_overlaps(event_x, event_y):
        messagebox.showwarning(
            "Warning in HDL-FSM-Editor",
            "The state could not be inserted, because it\nwas positioned too close to another object.\nTry again",
        )
        return
    coords = [
        event_x - project_manager.state_radius,
        event_y - project_manager.state_radius,
        event_x + project_manager.state_radius,
        event_y + project_manager.state_radius,
    ]
    state.States(
        coords,
        tags=["state" + str(state.States.state_number + 1)],
        text="S" + str(state.States.state_number + 1),
        fill_color=constants.STATE_COLOR,
        new_state=True,
    )
    # design_has_changed cannot be called by state.States, because state.States must be called
    # when an Undo is performed, which shall not create a new entry in the Undo-Stack.
    undo_handling.design_has_changed()


def state_overlaps(event_x, event_y) -> bool:
    overlapping_items = project_manager.canvas.find_overlapping(
        event_x - project_manager.state_radius,
        event_y - project_manager.state_radius,
        event_x + project_manager.state_radius,
        event_y + project_manager.state_radius,
    )
    for overlapping_item in overlapping_items:
        if "grid_line" not in project_manager.canvas.gettags(overlapping_item):
            return True
    return False
