"""
This module handles the transitions in the diagram.
"""

import canvas_editing
import canvas_modify_bindings
import transition
import undo_handling
import vector_handling
from project_manager import project_manager


def transition_start(event) -> None:
    [event_x, event_y] = canvas_editing.translate_window_event_coordinates_in_exact_canvas_coordinates(event)
    ids = project_manager.canvas.find_overlapping(event_x, event_y, event_x, event_y)
    if ids != ():
        for canvas_id in ids:
            element_type = project_manager.canvas.type(canvas_id)
            if _is_legal_start_point(canvas_id, element_type):
                line_start_x, line_start_y = _determine_transition_start_point(canvas_id, element_type)
                transition_id = project_manager.canvas.create_line(
                    [line_start_x, line_start_y, line_start_x, line_start_y],
                    arrow="last",
                    fill="blue",
                    smooth=True,
                )
                transition_draw_funcid = project_manager.canvas.bind(
                    "<Motion>",
                    lambda event, transition_id=transition_id: _transition_continue(event, transition_id),
                    add="+",
                )
                transition_start_object_tag = _get_tag_of_start_object(canvas_id)
                project_manager.canvas.bind(
                    "<Button-1>",
                    lambda event,
                    transition_id=transition_id,
                    canvas_id_of_start_item=canvas_id,
                    transition_draw_funcid=transition_draw_funcid,
                    transition_start_object_tag=transition_start_object_tag: _handle_next_added_transition_point(
                        event,
                        transition_id,
                        canvas_id_of_start_item,
                        transition_draw_funcid,
                        transition_start_object_tag,
                    ),
                )
                project_manager.root.bind_all(
                    "<Escape>",
                    lambda event,
                    transition_id=transition_id,
                    transition_draw_funcid=transition_draw_funcid: _end_inserting_transition(
                        transition_id, transition_draw_funcid
                    ),
                )


def _is_legal_start_point(canvas_id, element_type) -> bool:
    return (
        element_type == "oval"
        or (element_type == "polygon" and _reset_entry_has_no_transition(canvas_id))
        or (element_type == "rectangle" and project_manager.canvas.gettags(canvas_id)[0].startswith("connector"))
    )


def _determine_transition_start_point(canvas_id, element_type) -> tuple[float, float]:
    start_object_coords = project_manager.canvas.coords(canvas_id)
    if element_type in ["oval", "rectangle"]:
        line_start_x = start_object_coords[0] / 2 + start_object_coords[2] / 2
        line_start_y = start_object_coords[1] / 2 + start_object_coords[3] / 2
    else:  # polygon, this means reset-entry
        line_start_x = start_object_coords[4]
        line_start_y = start_object_coords[5]
    return line_start_x, line_start_y


def _get_tag_of_start_object(canvas_id):
    for tag in project_manager.canvas.gettags(canvas_id):
        if (
            (tag.startswith("state") and not tag.endswith("_comment_line_end"))
            or tag.startswith("connector")
            or tag.startswith("reset_entry")
        ):
            transition_start_object_tag = tag
            break
    return transition_start_object_tag


def _reset_entry_has_no_transition(canvas_id) -> bool:
    tags_of_reset_entry = project_manager.canvas.gettags(canvas_id)
    return all(not tag.startswith("transition") for tag in tags_of_reset_entry)


def _transition_continue(event, canvas_id) -> None:
    [event_x, event_y] = canvas_editing.translate_window_event_coordinates_in_exact_canvas_coordinates(event)
    coords_new = project_manager.canvas.coords(canvas_id)
    coords_new[-2] = event_x
    coords_new[-1] = event_y
    project_manager.canvas.coords(canvas_id, coords_new)


def _handle_next_added_transition_point(
    event, transition_id, start_state_canvas_id, transition_draw_funcid, transition_start_object_tag
) -> None:
    [event_x, event_y] = canvas_editing.translate_window_event_coordinates_in_exact_canvas_coordinates(event)
    transition_coords = project_manager.canvas.coords(transition_id)
    end_state_canvas_id = _get_canvas_id_of_state_or_connector_under_new_transition_point(event_x, event_y)
    transition_ends_at_connector = _check_if_transition_ends_at_connector(end_state_canvas_id)
    if end_state_canvas_id is None:
        if len(transition_coords) < 8:  # An additional intermediate point is added to the transition.
            _add_next_transition_point_(transition_id, transition_coords, event_x, event_y)
    elif transition_start_object_tag == "reset_entry" and transition_ends_at_connector is True:
        return
    elif end_state_canvas_id == start_state_canvas_id and len(transition_coords) == 4:
        # Going back to the start state with only 2 points cannot be drawn. The transition point is not accepted.
        return
    else:
        project_manager.canvas.addtag_withtag(  # Add tag to start object
            "transition" + str(transition.TransitionLine.transition_number) + "_start",
            start_state_canvas_id,
        )
        project_manager.canvas.addtag_withtag(  # Add tag to end object
            "transition" + str(transition.TransitionLine.transition_number) + "_end", end_state_canvas_id
        )
        # Create tags for line:
        end_state_tags = project_manager.canvas.gettags(end_state_canvas_id)
        for tag in end_state_tags:
            if (tag.startswith("state") and not tag.endswith("_comment_line_end")) or tag.startswith("connector"):
                end_state_tag = tag
                break
        tags = [
            "transition" + str(transition.TransitionLine.transition_number),
            "coming_from_" + transition_start_object_tag,
            "going_to_" + end_state_tag,
        ]
        transition_coords = _move_transition_end_point_to_the_middle_of_the_end_state(
            end_state_canvas_id, transition_id
        )
        transition_coords = _move_transition_start_and_end_point_to_the_edge_of_the_state_circle(
            start_state_canvas_id, end_state_canvas_id, transition_id
        )
        priority_dict = transition.TransitionLine.determine_priorities_of_outgoing_transitions(start_state_canvas_id)
        unused_priority = _get_unused_priority(priority_dict)
        _end_inserting_transition(transition_id, transition_draw_funcid)
        transition.TransitionLine(transition_coords, tags, unused_priority, new_transition=True)
        transition.TransitionLine.hide_priority_of_single_outgoing_transitions()
        undo_handling.design_has_changed()


def _end_inserting_transition(transition_id, transition_draw_funcid) -> None:
    project_manager.canvas.delete(transition_id)
    # Restore bindings:
    project_manager.canvas.unbind("<Motion>", transition_draw_funcid)
    project_manager.canvas.bind("<Button-1>", transition_start)
    project_manager.root.bind_all("<Escape>", lambda event: canvas_modify_bindings.switch_to_move_mode())


def _get_canvas_id_of_state_or_connector_under_new_transition_point(event_x, event_y) -> None:
    for canvas_id in project_manager.canvas.find_overlapping(event_x, event_y, event_x, event_y):
        element_type = project_manager.canvas.type(canvas_id)
        if (element_type == "oval") or (
            element_type == "rectangle" and project_manager.canvas.gettags(canvas_id)[0].startswith("connector")
        ):
            return canvas_id
    return None


def _check_if_transition_ends_at_connector(end_state_canvas_id) -> bool:
    if end_state_canvas_id is not None:
        end_state_tags = project_manager.canvas.gettags(end_state_canvas_id)
        for tag in end_state_tags:
            if tag.startswith("connector"):
                return True
    return False


def _add_next_transition_point_(transition_id, coords, event_x, event_y) -> None:
    coords.append(event_x)
    coords.append(event_y)
    project_manager.canvas.coords(transition_id, coords)


def _move_transition_end_point_to_the_middle_of_the_end_state(end_state_canvas_id, transition_id):
    end_state_coords = project_manager.canvas.coords(end_state_canvas_id)
    end_state_middle_x = end_state_coords[0] / 2 + end_state_coords[2] / 2
    end_state_middle_y = end_state_coords[1] / 2 + end_state_coords[3] / 2
    transition_coords = project_manager.canvas.coords(transition_id)
    transition_coords[-2] = end_state_middle_x
    transition_coords[-1] = end_state_middle_y
    project_manager.canvas.coords(transition_id, transition_coords)
    return transition_coords


def _move_transition_start_and_end_point_to_the_edge_of_the_state_circle(
    start_state_canvas_id, end_state_canvas_id, transition_id
):
    start_object_coords = project_manager.canvas.coords(start_state_canvas_id)
    transition_coords = project_manager.canvas.coords(transition_id)
    end_state_coords = project_manager.canvas.coords(end_state_canvas_id)
    start_state_radius = abs(start_object_coords[2] - start_object_coords[0]) // 2
    end_state_radius = abs(end_state_coords[2] - end_state_coords[0]) // 2
    if len(start_object_coords) == 10:  # start-state is reset-entry
        start_state_radius = 0
    if len(transition_coords) == 4:
        vector1 = vector_handling.shorten_vector(
            start_state_radius,
            transition_coords[0],
            transition_coords[1],
            end_state_radius,
            transition_coords[-2],
            transition_coords[-1],
            1,
            1,
        )
        vector2 = vector1
    elif len(transition_coords) == 6:
        vector1 = vector_handling.shorten_vector(
            start_state_radius,
            transition_coords[0],
            transition_coords[1],
            end_state_radius,
            transition_coords[2],
            transition_coords[3],
            1,
            0,
        )
        vector2 = vector_handling.shorten_vector(
            start_state_radius,
            transition_coords[2],
            transition_coords[3],
            end_state_radius,
            transition_coords[-2],
            transition_coords[-1],
            0,
            1,
        )
    else:  # len(transition_coords)==8
        vector1 = vector_handling.shorten_vector(
            start_state_radius,
            transition_coords[0],
            transition_coords[1],
            end_state_radius,
            transition_coords[2],
            transition_coords[3],
            1,
            0,
        )
        vector2 = vector_handling.shorten_vector(
            start_state_radius,
            transition_coords[4],
            transition_coords[5],
            end_state_radius,
            transition_coords[-2],
            transition_coords[-1],
            0,
            1,
        )
    transition_coords[0] = vector1[0]
    transition_coords[1] = vector1[1]
    transition_coords[-2] = vector2[2]
    transition_coords[-1] = vector2[3]
    project_manager.canvas.coords(transition_id, transition_coords)
    return transition_coords


def _get_unused_priority(priority_dict) -> str:
    priority_of_new_transition = "1"
    used_priorities = []
    for key in priority_dict:
        used_priorities.append(priority_dict[key])
    while True:
        if priority_of_new_transition in used_priorities:
            priority_of_new_transition = str(int(priority_of_new_transition) + 1)
        else:
            return priority_of_new_transition
