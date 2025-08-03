"""
This module contains all methods needed for the reset-entry object.
"""

import tkinter as tk

import canvas_editing
import canvas_modify_bindings
import main_window
import undo_handling

reset_entry_number = 0
_difference_x: float = 0.0
_difference_y: float = 0.0


def insert_reset_entry(event) -> None:
    global reset_entry_number
    if reset_entry_number == 0:  # Only 1 reset entry is allowed.
        reset_entry_number += 1
        main_window.reset_entry_button.config(state=tk.DISABLED)
        _insert_reset_entry_in_canvas(event)
        undo_handling.design_has_changed()
        canvas_modify_bindings.switch_to_move_mode()


def _insert_reset_entry_in_canvas(event) -> None:
    canvas_grid_coordinates_of_the_event = (
        canvas_editing.translate_window_event_coordinates_in_rounded_canvas_coordinates(event)
    )
    _create_reset_entry(canvas_grid_coordinates_of_the_event)


def _create_reset_entry(canvas_grid_coordinates_of_the_event) -> None:
    reset_entry_polygon = _create_polygon_shape_for_reset_entry()
    reset_entry_polygon = _move_reset_entry_polygon_to_event(canvas_grid_coordinates_of_the_event, reset_entry_polygon)
    polygon_id = main_window.canvas.create_polygon(
        reset_entry_polygon, fill="red", outline="orange", tags="reset_entry"
    )

    assert canvas_editing.state_name_font is not None, "The font must have been set before calling this function."
    main_window.canvas.create_text(
        canvas_grid_coordinates_of_the_event[0] - 4 * canvas_editing.reset_entry_size / 5,
        canvas_grid_coordinates_of_the_event[1],
        text="Reset",
        tags="reset_text",
        font=canvas_editing.state_name_font,
    )
    main_window.canvas.tag_bind(
        polygon_id, "<Enter>", lambda event, id=polygon_id: main_window.canvas.itemconfig(id, width=2)
    )
    main_window.canvas.tag_bind(
        polygon_id, "<Leave>", lambda event, id=polygon_id: main_window.canvas.itemconfig(id, width=1)
    )


def _create_polygon_shape_for_reset_entry() -> list[list]:
    # upper_left_corner  = [-20,-12]
    # upper_right_corner = [+20,-12]
    # point_corner       = [+32, 0]   connect-point for transition
    # lower_right_corner = [+20,+12]
    # lower_left_corner  = [-20,+12]
    size = canvas_editing.reset_entry_size
    # Coordinates when the mouse-pointer is at point_corner of the polygon:
    upper_left_corner = [-size / 2 - 4 * size / 5, -3 * size / 10]
    upper_right_corner = [+size / 2 - 4 * size / 5, -3 * size / 10]
    point_corner = [0, 0]
    lower_right_corner = [+size / 2 - 4 * size / 5, +3 * size / 10]
    lower_left_corner = [-size / 2 - 4 * size / 5, +3 * size / 10]
    return [upper_left_corner, upper_right_corner, point_corner, lower_right_corner, lower_left_corner]


def _move_reset_entry_polygon_to_event(canvas_grid_coordinates_of_the_event, reset_entry_polygon):
    for p in reset_entry_polygon:
        p[0] += canvas_grid_coordinates_of_the_event[0]
        p[1] += canvas_grid_coordinates_of_the_event[1]
    return reset_entry_polygon


def move_to(event_x, event_y, polygon_id, first, last) -> None:
    global _difference_x, _difference_y
    if first is True:
        # Calculate the difference between the "anchor" point and the event:
        coords = main_window.canvas.coords(polygon_id)
        middle_point = [coords[4], coords[5]]
        _difference_x, _difference_y = -event_x + middle_point[0], -event_y + middle_point[1]
    # Keep the distance between event and anchor point constant:
    event_x, event_y = event_x + _difference_x, event_y + _difference_y
    if last is True:
        event_x = canvas_editing.state_radius * round(event_x / canvas_editing.state_radius)
        event_y = canvas_editing.state_radius * round(event_y / canvas_editing.state_radius)
    width = _determine_width_of_the_polygon(polygon_id)
    height = _determine_height_of_the_polygon(polygon_id)
    new_upper_left_corner = _calculate_new_upper_left_corner_of_the_polygon(event_x, event_y, width, height)
    new_upper_right_corner = _calculate_new_upper_right_corner_of_the_polygon(event_x, event_y, width, height)
    new_point_right_corner = [event_x, event_y]
    new_lower_right_corner = _calculate_new_lower_right_corner_of_the_polygon(event_x, event_y, width, height)
    new_lower_left_corner = _calculate_new_lower_left_corner_of_the_polygon(event_x, event_y, width, height)
    new_coords = [
        *new_upper_left_corner,
        *new_upper_right_corner,
        *new_point_right_corner,
        *new_lower_right_corner,
        *new_lower_left_corner,
    ]
    new_center = _calculate_new_center_of_the_polygon(event_x, event_y, width)
    _move_polygon_in_canvas(polygon_id, new_coords, new_center)


def _determine_width_of_the_polygon(polygon_id):
    polygon_coords = main_window.canvas.coords(polygon_id)
    return polygon_coords[2] - polygon_coords[0]


def _determine_height_of_the_polygon(polygon_id):
    polygon_coords = main_window.canvas.coords(polygon_id)
    return polygon_coords[9] - polygon_coords[1]


def _calculate_new_upper_left_corner_of_the_polygon(event_x, event_y, width, height) -> list:
    return [event_x - 13 * width / 10, event_y - height / 2]


def _calculate_new_upper_right_corner_of_the_polygon(event_x, event_y, width, height) -> list:
    return [event_x - 3 * width / 10, event_y - height / 2]


def _calculate_new_lower_right_corner_of_the_polygon(event_x, event_y, width, height) -> list:
    return [event_x - 3 * width / 10, event_y + height / 2]


def _calculate_new_lower_left_corner_of_the_polygon(event_x, event_y, width, height) -> list:
    return [event_x - 13 * width / 10, event_y + height / 2]


def _calculate_new_center_of_the_polygon(event_x, event_y, width) -> list:
    return [event_x - 4 * width / 5, event_y]


def _move_polygon_in_canvas(polygon_id, new_coords, new_center) -> None:
    main_window.canvas.coords(polygon_id, *new_coords)
    main_window.canvas.coords("reset_text", *new_center)
