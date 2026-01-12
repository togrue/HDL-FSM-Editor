"""
This module contains all methods needed for inserting a reset-entry object.
"""

import tkinter as tk

import canvas_editing
import canvas_modify_bindings
import reset_entry
import undo_handling
from project_manager import project_manager


def insert_reset_entry(event) -> None:
    project_manager.reset_entry_button.config(state=tk.DISABLED)
    canvas_grid_coordinates_of_the_event = (
        canvas_editing.translate_window_event_coordinates_in_rounded_canvas_coordinates(event)
    )
    reset_entry_polygon_coords = _create_polygon_shape_for_reset_entry()
    reset_entry_polygon_coords = _move_reset_entry_polygon_to_event(
        canvas_grid_coordinates_of_the_event, reset_entry_polygon_coords
    )
    reset_entry.ResetEntry(reset_entry_polygon_coords, tags=("reset_entry",))
    undo_handling.design_has_changed()
    canvas_modify_bindings.switch_to_move_mode()


def _create_polygon_shape_for_reset_entry() -> list:
    # upper_left_corner  = [-20,-12]
    # upper_right_corner = [+20,-12]
    # point_corner       = [+32, 0]   connect-point for transition
    # lower_right_corner = [+20,+12]
    # lower_left_corner  = [-20,+12]
    size = project_manager.reset_entry_size
    # Coordinates when the mouse-pointer is at point_corner of the polygon:
    upper_left_corner = [-size / 2 - 4 * size / 5, -3 * size / 10]
    upper_right_corner = [+size / 2 - 4 * size / 5, -3 * size / 10]
    point_corner = [0, 0]
    lower_right_corner = [+size / 2 - 4 * size / 5, +3 * size / 10]
    lower_left_corner = [-size / 2 - 4 * size / 5, +3 * size / 10]
    coords = []
    coords.extend(upper_left_corner)
    coords.extend(upper_right_corner)
    coords.extend(point_corner)
    coords.extend(lower_right_corner)
    coords.extend(lower_left_corner)
    return coords


def _move_reset_entry_polygon_to_event(canvas_grid_coordinates_of_the_event, reset_entry_polygon):
    reset_entry_polygon = [
        p + canvas_grid_coordinates_of_the_event[0] if i % 2 == 0 else p + canvas_grid_coordinates_of_the_event[1]
        for i, p in enumerate(reset_entry_polygon)
    ]
    return reset_entry_polygon
