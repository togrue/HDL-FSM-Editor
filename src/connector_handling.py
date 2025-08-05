"""
Methods for the handling of the connectors
"""

import tkinter as tk

import canvas_editing
import constants
import main_window
import undo_handling

connector_number = 0
difference_x: float = 0.0
difference_y: float = 0.0


def insert_connector(event: tk.Event) -> None:
    global connector_number
    connector_number += 1
    # Translate the window coordinate into the canvas coordinate (the Canvas is bigger than the window):
    event_x, event_y = canvas_editing.translate_window_event_coordinates_in_rounded_canvas_coordinates(event)
    overlapping_items = main_window.canvas.find_overlapping(
        event_x - canvas_editing.state_radius / 2,
        event_y - canvas_editing.state_radius / 2,
        event_x + canvas_editing.state_radius / 2,
        event_y + canvas_editing.state_radius / 2,
    )
    for overlapping_item in overlapping_items:
        if "grid_line" not in main_window.canvas.gettags(overlapping_item):
            return
    connector_id = main_window.canvas.create_rectangle(
        event_x - canvas_editing.state_radius / 4,
        event_y - canvas_editing.state_radius / 4,
        event_x + canvas_editing.state_radius / 4,
        event_y + canvas_editing.state_radius / 4,
        fill=constants.CONNECTOR_COLOR,
        tags=f"connector{connector_number}",
    )
    main_window.canvas.tag_bind(
        connector_id, "<Enter>", lambda event, id=connector_id: main_window.canvas.itemconfig(id, width=2)
    )
    main_window.canvas.tag_bind(
        connector_id, "<Leave>", lambda event, id=connector_id: main_window.canvas.itemconfig(id, width=1)
    )
    undo_handling.design_has_changed()


def move_to(event_x: float, event_y: float, rectangle_id: int, first: bool, last: bool) -> None:
    global difference_x, difference_y
    if first is True:
        # Calculate the difference between the "anchor" point and the event:
        coords = main_window.canvas.coords(rectangle_id)
        middle_point = _calculate_middle_point(coords)
        difference_x, difference_y = -event_x + middle_point[0], -event_y + middle_point[1]
    # Keep the distance between event and anchor point constant:
    event_x, event_y = event_x + difference_x, event_y + difference_y
    if last is True:
        event_x = canvas_editing.state_radius * round(event_x / canvas_editing.state_radius)
        event_y = canvas_editing.state_radius * round(event_y / canvas_editing.state_radius)
    edge_length = _determine_edge_length_of_the_rectangle(rectangle_id)
    new_upper_left_corner = _calculate_new_upper_left_corner_of_the_rectangle(event_x, event_y, edge_length)
    new_lower_right_corner = _calculate_new_lower_right_corner_of_the_rectangle(event_x, event_y, edge_length)
    _move_rectangle_in_canvas(rectangle_id, new_upper_left_corner, new_lower_right_corner)


def _calculate_middle_point(coords: list[float]) -> list[float]:
    middle_x = (coords[0] + coords[2]) / 2
    middle_y = (coords[1] + coords[3]) / 2
    return [middle_x, middle_y]


def _determine_edge_length_of_the_rectangle(rectangle_id: int) -> float:
    rectangle_coords = main_window.canvas.coords(rectangle_id)
    edge_length = rectangle_coords[2] - rectangle_coords[0]
    return edge_length


def _calculate_new_upper_left_corner_of_the_rectangle(event_x: float, event_y: float, edge_length: float) -> list[float]:
    return [event_x - edge_length / 2, event_y - edge_length / 2]


def _calculate_new_lower_right_corner_of_the_rectangle(
    event_x: float, event_y: float, edge_length: float
) -> list[float]:
    return [event_x + edge_length / 2, event_y + edge_length / 2]


def _move_rectangle_in_canvas(
    rectangle_id: int, new_upper_left_corner: list[float], new_lower_right_corner: list[float]
) -> None:
    main_window.canvas.coords(rectangle_id, *new_upper_left_corner, *new_lower_right_corner)
