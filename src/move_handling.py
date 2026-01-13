"""
This module contains a method to decide which graphical object must be moved.
"""

import canvas_editing
import condition_action
import connector_insertion
import constants
import global_actions_clocked
import global_actions_combinatorial
import reset_entry
import state
import state_action
import state_actions_default
import state_comment
import transition_handling
from project_manager import project_manager


def move_do(event, move_list, first, move_to_grid=False) -> None:
    # move_to_grid = bool(event.type == "5")
    [event_x, event_y] = canvas_editing.translate_window_event_coordinates_in_exact_canvas_coordinates(event)
    move_to_coordinates(event_x, event_y, move_list, first, move_to_grid)


def move_to_coordinates(event_x, event_y, move_list, first, move_to_grid):
    if _state_is_moved_to_near_to_state_or_connector(move_list, event_x, event_y):
        return
    if _connector_moved_too_close_to_other_object(move_list, event_x, event_y):
        return
    for entry in move_list:
        item_id = entry[0]
        item_point_to_move = entry[1]
        item_type = project_manager.canvas.type(item_id)
        if item_type == "oval":
            ref = state.States.state_dict[item_id]
            ref.move_to(event_x, event_y, item_id, first, move_to_grid)
        elif item_type == "polygon":
            reset_entry.ResetEntry.move_to(event_x, event_y, item_id, first, move_to_grid)
        elif item_type == "line":
            transition_handling.move_to(event_x, event_y, item_id, item_point_to_move, first, move_list, move_to_grid)
        elif item_type == "rectangle":
            connector_insertion.ConnectorInsertion.move_to(event_x, event_y, item_id, first, move_to_grid)
        elif item_type == "window":
            if item_id in state_action.StateAction.mytext_dict:
                ref = state_action.StateAction.mytext_dict[item_id]
            elif item_id in state_comment.StateComment.dictionary:
                ref = state_comment.StateComment.dictionary[item_id]
            elif item_id in state_actions_default.StateActionsDefault.dictionary:
                ref = state_actions_default.StateActionsDefault.dictionary[item_id]
            elif item_id in global_actions_clocked.GlobalActionsClocked.dictionary:
                ref = global_actions_clocked.GlobalActionsClocked.dictionary[item_id]
            elif item_id in global_actions_combinatorial.GlobalActionsCombinatorial.dictionary:
                ref = global_actions_combinatorial.GlobalActionsCombinatorial.dictionary[item_id]
            else:
                ref = condition_action.ConditionAction.dictionary[item_id]
            ref.move_to(event_x, event_y, first)
        else:
            print("move: Fatal, unknown canvas type", "|" + item_type + "|")


def _state_is_moved_to_near_to_state_or_connector(move_list, event_x, event_y) -> bool:
    for entry in move_list:
        moved_item_id = entry[0]
        if project_manager.canvas.type(moved_item_id) == "oval":
            ref = state.States.state_dict[moved_item_id]
            # Keep the distance between event and anchor point constant:
            event_x_mod, event_y_mod = event_x + ref.difference_x, event_y + ref.difference_y
            event_x_mod = project_manager.state_radius * round(event_x_mod / project_manager.state_radius)
            event_y_mod = project_manager.state_radius * round(event_y_mod / project_manager.state_radius)
            state_coords = project_manager.canvas.coords(moved_item_id)
            state_radius = (state_coords[2] - state_coords[0]) // 2
            moved_state_coords = (
                event_x_mod - state_radius,
                event_y_mod - state_radius,
                event_x_mod + state_radius,
                event_y_mod + state_radius,
            )
            overlapping_list = project_manager.canvas.find_overlapping(
                moved_state_coords[0] - project_manager.state_radius / 2,
                moved_state_coords[1] - project_manager.state_radius / 2,
                moved_state_coords[2] + project_manager.state_radius / 2,
                moved_state_coords[3] + project_manager.state_radius / 2,
            )
            for overlapping_item in overlapping_list:
                overlapping_with_connector = False
                tags = project_manager.canvas.gettags(overlapping_item)
                for tag in tags:
                    if tag.startswith("connector"):
                        overlapping_with_connector = True
                if overlapping_item != moved_item_id and (
                    project_manager.canvas.type(overlapping_item) == "oval" or overlapping_with_connector
                ):
                    return True
    return False


def _connector_moved_too_close_to_other_object(move_list, event_x, event_y) -> bool:
    for entry in move_list:
        moved_item_id = entry[0]
        if (
            project_manager.canvas.type(moved_item_id) == "rectangle"
            and project_manager.canvas.itemcget(moved_item_id, "fill") == constants.CONNECTOR_COLOR
        ):
            # Keep the distance between event and anchor point constant:
            event_x_mod, event_y_mod = (
                event_x + connector_insertion.ConnectorInsertion.difference_x,
                event_y + connector_insertion.ConnectorInsertion.difference_y,
            )
            event_x_mod = project_manager.state_radius * round(
                event_x_mod / project_manager.state_radius
            )  # move event_x to grid.
            event_y_mod = project_manager.state_radius * round(
                event_y_mod / project_manager.state_radius
            )  # move event_y to grid.
            connector_coords = project_manager.canvas.coords(moved_item_id)
            edge_length = connector_coords[2] - connector_coords[0]
            new_upper_left_corner = [event_x_mod - edge_length / 2, event_y_mod - edge_length / 2]
            new_lower_right_corner = [event_x_mod + edge_length / 2, event_y_mod + edge_length / 2]
            moved_connector_coords = [*new_upper_left_corner, *new_lower_right_corner]
            overlapping_list = project_manager.canvas.find_overlapping(
                moved_connector_coords[0] - project_manager.state_radius / 2,
                moved_connector_coords[1] - project_manager.state_radius / 2,
                moved_connector_coords[2] + project_manager.state_radius / 2,
                moved_connector_coords[3] + project_manager.state_radius / 2,
            )
            for overlapping_item in overlapping_list:
                if overlapping_item != moved_item_id and (
                    project_manager.canvas.type(overlapping_item) == "oval"
                    or (
                        project_manager.canvas.type(overlapping_item) == "rectangle"
                        and project_manager.canvas.itemcget(overlapping_item, "fill") == constants.CONNECTOR_COLOR
                    )
                ):
                    return True
    return False
