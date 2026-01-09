"""
Methods for the handling of the connectors
"""

import canvas_editing
import constants
import undo_handling
from project_manager import project_manager

connector_number = 0
difference_x = 0
difference_y = 0


def insert_connector(event) -> None:
    global connector_number
    connector_number += 1
    # Translate the window coordinate into the canvas coordinate (the Canvas is bigger than the window):
    event_x, event_y = canvas_editing.translate_window_event_coordinates_in_rounded_canvas_coordinates(event)
    overlapping_items = project_manager.canvas.find_overlapping(
        event_x - canvas_editing.state_radius / 2,
        event_y - canvas_editing.state_radius / 2,
        event_x + canvas_editing.state_radius / 2,
        event_y + canvas_editing.state_radius / 2,
    )
    for overlapping_item in overlapping_items:
        if "grid_line" not in project_manager.canvas.gettags(overlapping_item):
            return
    coords = (
        event_x - canvas_editing.state_radius / 4,
        event_y - canvas_editing.state_radius / 4,
        event_x + canvas_editing.state_radius / 4,
        event_y + canvas_editing.state_radius / 4,
    )
    tag = "connector" + str(connector_number)
    draw_connector(coords, tag)
    undo_handling.design_has_changed()


def draw_connector(coords, tags):
    connector_id = project_manager.canvas.create_rectangle(coords, fill=constants.CONNECTOR_COLOR, tags=tags)
    project_manager.canvas.tag_bind(
        connector_id, "<Enter>", lambda event, id=connector_id: project_manager.canvas.itemconfig(id, width=2)
    )
    project_manager.canvas.tag_bind(
        connector_id, "<Leave>", lambda event, id=connector_id: project_manager.canvas.itemconfig(id, width=1)
    )
    return connector_id


def move_to(event_x, event_y, rectangle_id, first, last) -> None:
    global difference_x, difference_y
    if first is True:
        # Calculate the difference between the "anchor" point and the event:
        coords = project_manager.canvas.coords(rectangle_id)
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


def _calculate_middle_point(coords) -> list:
    middle_x = (coords[0] + coords[2]) / 2
    middle_y = (coords[1] + coords[3]) / 2
    return [middle_x, middle_y]


def _determine_edge_length_of_the_rectangle(rectangle_id):
    rectangle_coords = project_manager.canvas.coords(rectangle_id)
    edge_length = rectangle_coords[2] - rectangle_coords[0]
    return edge_length


def _calculate_new_upper_left_corner_of_the_rectangle(event_x, event_y, edge_length) -> list:
    return [event_x - edge_length / 2, event_y - edge_length / 2]


def _calculate_new_lower_right_corner_of_the_rectangle(event_x, event_y, edge_length) -> list:
    return [event_x + edge_length / 2, event_y + edge_length / 2]


def _move_rectangle_in_canvas(rectangle_id, new_upper_left_corner, new_lower_right_corner) -> None:
    project_manager.canvas.coords(rectangle_id, *new_upper_left_corner, *new_lower_right_corner)
