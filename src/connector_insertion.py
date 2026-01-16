"""
Module handling connectors on the canvas.
"""

import canvas_editing
import constants
import undo_handling
from project_manager import project_manager


class ConnectorInsertion:
    """
    For each connector on the canvas a ConnectorInsertion object is created.
    """

    connector_number = 0
    difference_x = 0
    difference_y = 0

    # def insert_connector(event) -> None:
    def __init__(self, event) -> None:
        # global connector_number
        ConnectorInsertion.connector_number += 1
        # Translate the window coordinate into the canvas coordinate (the Canvas is bigger than the window):
        event_x, event_y = canvas_editing.translate_window_event_coordinates_in_rounded_canvas_coordinates(event)
        overlapping_items = project_manager.canvas.find_overlapping(
            event_x - project_manager.state_radius / 2,
            event_y - project_manager.state_radius / 2,
            event_x + project_manager.state_radius / 2,
            event_y + project_manager.state_radius / 2,
        )
        for overlapping_item in overlapping_items:
            if "grid_line" not in project_manager.canvas.gettags(overlapping_item):
                return
        coords = (
            event_x - project_manager.state_radius / 4,
            event_y - project_manager.state_radius / 4,
            event_x + project_manager.state_radius / 4,
            event_y + project_manager.state_radius / 4,
        )
        tag = "connector" + str(ConnectorInsertion.connector_number)
        ConnectorInsertion.draw_connector(coords, tag)
        undo_handling.design_has_changed()

    @classmethod
    def draw_connector(cls, coords, tags):
        connector_id = project_manager.canvas.create_rectangle(coords, fill=constants.CONNECTOR_COLOR, tags=tags)
        project_manager.canvas.tag_bind(
            connector_id, "<Enter>", lambda event, id=connector_id: project_manager.canvas.itemconfig(id, width=2)
        )
        project_manager.canvas.tag_bind(
            connector_id, "<Leave>", lambda event, id=connector_id: project_manager.canvas.itemconfig(id, width=1)
        )
        return connector_id

    @classmethod
    def move_to(cls, event_x, event_y, rectangle_id, first, last) -> None:
        # global difference_x, difference_y
        if first is True:
            # Calculate the difference between the "anchor" point and the event:
            coords = project_manager.canvas.coords(rectangle_id)
            middle_point = ConnectorInsertion._calculate_middle_point(coords)
            cls.difference_x, cls.difference_y = -event_x + middle_point[0], -event_y + middle_point[1]
        # Keep the distance between event and anchor point constant (important for moving with connected transitions):
        event_x, event_y = event_x + cls.difference_x, event_y + cls.difference_y
        if last is True:
            event_x = project_manager.state_radius * round(event_x / project_manager.state_radius)
            event_y = project_manager.state_radius * round(event_y / project_manager.state_radius)
        edge_length = ConnectorInsertion._determine_edge_length_of_the_rectangle(rectangle_id)
        new_upper_left_corner = ConnectorInsertion._calculate_new_upper_left_corner_of_the_rectangle(
            event_x, event_y, edge_length
        )
        new_lower_right_corner = ConnectorInsertion._calculate_new_lower_right_corner_of_the_rectangle(
            event_x, event_y, edge_length
        )
        ConnectorInsertion._move_rectangle_in_canvas(rectangle_id, new_upper_left_corner, new_lower_right_corner)

    @classmethod
    def _calculate_middle_point(cls, coords) -> list:
        middle_x = (coords[0] + coords[2]) / 2
        middle_y = (coords[1] + coords[3]) / 2
        return [middle_x, middle_y]

    @classmethod
    def _determine_edge_length_of_the_rectangle(cls, rectangle_id):
        rectangle_coords = project_manager.canvas.coords(rectangle_id)
        edge_length = rectangle_coords[2] - rectangle_coords[0]
        return edge_length

    @classmethod
    def _calculate_new_upper_left_corner_of_the_rectangle(cls, event_x, event_y, edge_length) -> list:
        return [event_x - edge_length / 2, event_y - edge_length / 2]

    @classmethod
    def _calculate_new_lower_right_corner_of_the_rectangle(cls, event_x, event_y, edge_length) -> list:
        return [event_x + edge_length / 2, event_y + edge_length / 2]

    @classmethod
    def _move_rectangle_in_canvas(cls, rectangle_id, new_upper_left_corner, new_lower_right_corner) -> None:
        project_manager.canvas.coords(rectangle_id, *new_upper_left_corner, *new_lower_right_corner)
