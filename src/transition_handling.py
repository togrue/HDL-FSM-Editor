"""
This module handles the transitions in the diagram.
"""

import math
import tkinter as tk

import canvas_editing
import canvas_modify_bindings
import condition_action_handling
import constants
import main_window
import move_handling_initialization
import undo_handling
import vector_handling
from widgets.OptionMenu import OptionMenu

transition_number = 0
_difference_x = 0
_difference_y = 0


def move_to(event_x, event_y, transition_id, point, first, move_list, last) -> None:
    global _difference_x, _difference_y

    # Calculate movement offset
    _difference_x, _difference_y = _calculate_movement_offset(event_x, event_y, transition_id, point, first, move_list)

    # Apply offset and snap to grid
    event_x, event_y = event_x + _difference_x, event_y + _difference_y
    event_x, event_y = _snap_to_grid(event_x, event_y, last)

    # Get transition tag and manage layering
    transition_tag = _get_transition_tag_and_lower(transition_id)
    if not transition_tag:
        return

    # Update transition coordinates
    transition_coords = main_window.canvas.coords(transition_tag)
    _update_transition_coordinates(transition_tag, event_x, event_y, point)

    _manage_grid_layering(transition_tag)

    _update_priority_rectangle(transition_tag, event_x, event_y, point, transition_coords)


def _calculate_movement_offset(event_x, event_y, transition_id, point, first, move_list) -> tuple[int, int] | tuple:
    """Calculate the offset for moving transition points."""
    if main_window.canvas.type(move_list[0][0]) == "line" and (move_list[0][1] in ("start", "end")):
        middle_of_line_is_moved = False
    else:
        middle_of_line_is_moved = True

    if middle_of_line_is_moved is True and first is True:
        coords = main_window.canvas.coords(transition_id)
        if point == "start":
            point_to_move = [coords[0], coords[1]]
        elif point == "next_to_start":
            point_to_move = [coords[2], coords[3]]
        elif point == "next_to_end":
            point_to_move = [coords[-4], coords[-3]]
        elif point == "end":
            point_to_move = [coords[-2], coords[-1]]
        else:
            print("transition_handling: Fatal, unknown point =", point)
            return 0, 0
        return -event_x + point_to_move[0], -event_y + point_to_move[1]
    return 0, 0


def _snap_to_grid(event_x, event_y, last) -> tuple:
    """Snap coordinates to grid if this is the final move."""
    if last is True:
        event_x = canvas_editing.state_radius * round(event_x / canvas_editing.state_radius)
        event_y = canvas_editing.state_radius * round(event_y / canvas_editing.state_radius)
    return event_x, event_y


def _get_transition_tag_and_lower(transition_id) -> None:
    """Get the transition tag and lower it in the canvas stack."""
    all_transition_tags = main_window.canvas.gettags(transition_id)
    for single_transition_tag in all_transition_tags:
        if (
            single_transition_tag.startswith("transition")
            or single_transition_tag.startswith("connection")
            or single_transition_tag.endswith("comment_line")
        ):
            transition_tag = single_transition_tag
            main_window.canvas.tag_lower(transition_tag)
            return transition_tag
    return None


def _update_transition_coordinates(transition_tag, event_x, event_y, point) -> None:
    """Update the transition coordinates based on which point is being moved."""
    transition_coords = main_window.canvas.coords(transition_tag)
    if point == "start":
        main_window.canvas.coords(transition_tag, event_x, event_y, *transition_coords[2:])
    elif point == "next_to_start":
        main_window.canvas.coords(transition_tag, *transition_coords[0:2], event_x, event_y, *transition_coords[4:])
    elif point == "next_to_end":
        main_window.canvas.coords(transition_tag, *transition_coords[-8:-4], event_x, event_y, *transition_coords[-2:])
    elif point == "end":
        main_window.canvas.coords(transition_tag, *transition_coords[-8:-2], event_x, event_y)
    else:
        print("transition_handling: Fatal, unknown point =", point)


def _manage_grid_layering(transition_tag) -> None:
    """Ensure transition appears above grid lines if grid is shown."""
    if main_window.show_grid:
        list_of_grid_line_canvas_ids = main_window.canvas.find_withtag("grid_line")
        if list_of_grid_line_canvas_ids:
            main_window.canvas.tag_raise(transition_tag, "grid_line")


def _update_priority_rectangle(transition_tag, event_x, event_y, point, transition_coords) -> None:
    """Update the position of the priority rectangle for transitions."""
    if not transition_tag.startswith("transition"):  # No priority rectangle for connections
        return

    start_state_coords = main_window.canvas.coords(transition_tag + "_start")

    if point == "start":
        if start_state_coords == [] or main_window.canvas.type(transition_tag + "_start") == "polygon":
            start_state_radius = 0
        else:
            start_state_radius = abs(start_state_coords[2] - start_state_coords[0]) / 2

        priority_middle_x, priority_middle_y, _, _ = vector_handling.shorten_vector(
            start_state_radius + canvas_editing.priority_distance,
            event_x,
            event_y,
            0,
            transition_coords[2],
            transition_coords[3],
            1,
            0,
        )
    else:
        start_state_radius = abs(start_state_coords[2] - start_state_coords[0]) / 2
        priority_middle_x, priority_middle_y, _, _ = vector_handling.shorten_vector(
            start_state_radius + canvas_editing.priority_distance,
            transition_coords[0],
            transition_coords[1],
            0,
            transition_coords[2],
            transition_coords[3],
            1,
            0,
        )

    rectangle_width_half, rectangle_height_half = _get_rectangle_dimensions(transition_tag + "rectangle")
    main_window.canvas.coords(
        transition_tag + "rectangle",
        priority_middle_x - rectangle_width_half,
        priority_middle_y - rectangle_height_half,
        priority_middle_x + rectangle_width_half,
        priority_middle_y + rectangle_height_half,
    )
    main_window.canvas.coords(transition_tag + "priority", priority_middle_x, priority_middle_y)
    main_window.canvas.tag_raise(transition_tag + "rectangle", transition_tag)
    main_window.canvas.tag_raise(transition_tag + "priority", transition_tag + "rectangle")


def _get_rectangle_dimensions(canvas_id) -> list:
    rectangle_coords = main_window.canvas.coords(canvas_id)
    rectangle_width_half = (rectangle_coords[2] - rectangle_coords[0]) / 2
    rectangle_height_half = (rectangle_coords[3] - rectangle_coords[1]) / 2
    return [rectangle_width_half, rectangle_height_half]


def extend_transition_to_state_middle_points(transition_tag) -> None:
    transition_coords = main_window.canvas.coords(transition_tag)
    end_state_coords = main_window.canvas.coords(transition_tag + "_end")
    if transition_tag.startswith(
        "transition"
    ):  # When transition_tag starts with "connection" no start point is needed.
        start_coords = main_window.canvas.coords(
            transition_tag + "_start"
        )  # Coords are from a circle (state) or from a connector (rectangle) or from the reset entry (polygon).
        if (
            main_window.canvas.type(transition_tag + "_start") != "polygon"
        ):  # At the reset entry the transition start point is not modified for moving.
            transition_coords[0] = (start_coords[0] + start_coords[2]) // 2
            transition_coords[1] = (start_coords[1] + start_coords[3]) // 2
    transition_coords[-2] = (end_state_coords[0] + end_state_coords[2]) // 2
    transition_coords[-1] = (end_state_coords[1] + end_state_coords[3]) // 2
    main_window.canvas.coords(transition_tag, *transition_coords)
    # Hide the line "under" the states:
    main_window.canvas.tag_lower(transition_tag, transition_tag + "_start")
    main_window.canvas.tag_lower(transition_tag, transition_tag + "_end")


# def distance_from_point_to_line(point_x, point_y, line):
#     # Gabi's solution:
#     # if (line[2] - line[0])==0: # line is vertical
#     #     distance = abs(point_x - line[0])
#     # else:
#     #     if (line[3] - line[1])==0: # line is horizontal
#     #         distance = abs(point_y - line[1])
#     #     else:
#     #         m_line = (line[3] - line[1])/(line[2] - line[0])
#     #         line_offset = line[1] - m_line * line[0]
#     #         m_distance_line = - 1/m_line
#     #         distance_line_offset = point_y - m_distance_line * point_x
#     #         x_cut = (distance_line_offset - line_offset)/(m_line - m_distance_line)
#     #         y_cut = m_line * x_cut + line_offset
#     #         distance = math.sqrt((point_x - x_cut)**2 + (point_y - y_cut)**2)
#     #return distance
#     length_of_triangle_side1 = math.sqrt((point_x-line[0])**2 + (point_y-line[1])**2)
#     length_of_triangle_side2 = math.sqrt((point_x-line[2])**2 + (point_y-line[3])**2)
#     length_of_triangle_side3 = math.sqrt((line[2]-line[0])**2 + (line[3]-line[1])**2)
#     half_circumference = (length_of_triangle_side1 + length_of_triangle_side2 + length_of_triangle_side3)/2
#     area_of_triangle = math.sqrt(half_circumference *
#                                  (half_circumference-length_of_triangle_side1) *
#                                  (half_circumference-length_of_triangle_side2) *
#                                  (half_circumference-length_of_triangle_side3))  # Heron's formula
#     if length_of_triangle_side3!=0: # This value is 0 when the 2 line points are identical.
#         height_of_triangle = 2*area_of_triangle/length_of_triangle_side3
#         return height_of_triangle
#     return length_of_triangle_side1


def get_point_to_move(item_id, event_x, event_y) -> str:
    # Determine which point of the transition is nearest to the event:
    transition_coords = main_window.canvas.coords(item_id)
    number_of_points = len(transition_coords) // 2
    distance_event_to_point = []
    distance_to_neighbour = []
    for i in range(number_of_points):
        distance_event_to_point.append(
            math.sqrt((event_x - transition_coords[2 * i]) ** 2 + (event_y - transition_coords[2 * i + 1]) ** 2)
        )
        if i < number_of_points - 1:
            distance_to_neighbour.append(
                math.sqrt(
                    (transition_coords[2 * i] - transition_coords[2 * i + 2]) ** 2
                    + (transition_coords[2 * i + 1] - transition_coords[2 * i + 3]) ** 2
                )
            )
    # if number_of_points==4:
    #     dist = []
    #     dist.append(distance_from_point_to_line(event_x, event_y, transition_coords[0:4]))
    #     dist.append(distance_from_point_to_line(event_x, event_y, transition_coords[2:6]))
    #     dist.append(distance_from_point_to_line(event_x, event_y, transition_coords[4:]))
    #     minimum = 0
    #     for i in range(1,3):
    #         if dist[i]<dist[minimum]:
    #             minimum = i
    #     if minimum==0:
    #         return "start"
    #     if minimum==1:
    #         distance_to_point1 = math.sqrt((event_x-transition_coords[2])**2 + (event_y-transition_coords[3])**2)
    #         distance_to_point2 = math.sqrt((event_x-transition_coords[4])**2 + (event_y-transition_coords[5])**2)
    #         if distance_to_point1<distance_to_point2:
    #             return "next_to_start"
    #         return "next_to_end"
    #     return 'end'
    if number_of_points == 4:
        return_value = ""
        if distance_event_to_point[0] < 2 * canvas_editing.state_radius:
            return_value = "start"
        if (
            distance_event_to_point[3] < 2 * canvas_editing.state_radius
            and distance_event_to_point[3] < distance_event_to_point[0]
        ):
            return_value = "end"
        if return_value == "":
            return_value = "next_to_start" if distance_event_to_point[1] < distance_event_to_point[2] else "next_to_end"
        return return_value
    elif number_of_points == 3:
        # if   distance_event_to_point[0]<distance_to_neighbour[0]/4:
        #     return "start"
        # if distance_event_to_point[0]<distance_to_neighbour[0]*3/4:
        #     main_window.canvas.coords(item_id, *transition_coords[0:2], event_x, event_y, *transition_coords[2:6]) # insert new point into transition
        #     return "next_to_start"
        # if distance_event_to_point[0]<distance_to_neighbour[0]:
        #     return "next_to_start"
        # if distance_event_to_point[1]<distance_to_neighbour[1]/4:
        #     return "next_to_start"
        # if distance_event_to_point[1]<distance_to_neighbour[1]*3/4:
        #     main_window.canvas.coords(item_id, *transition_coords[0:4], event_x, event_y, *transition_coords[4:6]) # insert new point into transition
        #     return "next_to_end"
        # return 'end'
        return_value = ""
        if distance_event_to_point[0] < 2 * canvas_editing.state_radius:
            return_value = "start"
        if (
            distance_event_to_point[2] < 2 * canvas_editing.state_radius
            and distance_event_to_point[2] < distance_event_to_point[0]
        ):
            return_value = "end"
        if return_value != "":
            return return_value
        ratio = distance_event_to_point[0] / distance_event_to_point[2]
        if 0.8 < ratio < 1.2:
            return "next_to_start"  # equal to "next_to_end" because no new point is inserted.
        if distance_event_to_point[2] < distance_event_to_point[0]:
            main_window.canvas.coords(
                item_id, *transition_coords[0:4], event_x, event_y, *transition_coords[4:6]
            )  # insert new point into transition
            return "next_to_end"
        else:
            main_window.canvas.coords(
                item_id, *transition_coords[0:2], event_x, event_y, *transition_coords[2:6]
            )  # insert new point into transition
            return "next_to_start"
    else:
        if distance_event_to_point[0] < distance_to_neighbour[0] / 3:
            return "start"
        if distance_event_to_point[0] < distance_to_neighbour[0] * 2 / 3:
            main_window.canvas.coords(item_id, *transition_coords[0:2], event_x, event_y, *transition_coords[2:4])
            return "next_to_start"
        return "end"


def shorten_to_state_border(transition_tag) -> None:
    transition_coords = main_window.canvas.coords(transition_tag)
    tag_list = main_window.canvas.gettags(transition_tag)
    connection = False
    start_state_tag = None
    end_state_tag = None
    for tag in tag_list:
        if tag.startswith("coming_from_"):
            start_state_tag = tag[12:]
        elif tag.startswith("going_to_"):
            end_state_tag = tag[9:]
        elif tag.startswith("connected_to_"):
            connection = True
            end_state_tag = tag[13:]
    if connection is False:
        start_state_coords = main_window.canvas.coords(start_state_tag)
        end_state_coords = main_window.canvas.coords(end_state_tag)
        if start_state_tag == "reset_entry":
            start_state_radius = 0
        else:
            start_state_radius = (start_state_coords[2] - start_state_coords[0]) / 2
        end_state_radius = (end_state_coords[2] - end_state_coords[0]) / 2
        transition_start_coords = vector_handling.shorten_vector(
            start_state_radius,
            transition_coords[0],
            transition_coords[1],
            0,
            transition_coords[2],
            transition_coords[3],
            1,
            0,
        )
        transition_end_coords = vector_handling.shorten_vector(
            0,
            transition_coords[-4],
            transition_coords[-3],
            end_state_radius,
            transition_coords[-2],
            transition_coords[-1],
            0,
            1,
        )
        transition_coords[0] = transition_start_coords[0]
        transition_coords[1] = transition_start_coords[1]
        transition_coords[-2] = transition_end_coords[-2]
        transition_coords[-1] = transition_end_coords[-1]
        transition_coords = _remove_duplicate_points(transition_coords)
        main_window.canvas.coords(transition_tag, transition_coords)
        main_window.canvas.tag_lower(transition_tag)
        # Move priority rectangle:
        start_state_radius = abs(start_state_coords[2] - start_state_coords[0]) / 2
        [priority_middle_x, priority_middle_y, _, _] = vector_handling.shorten_vector(
            0 + canvas_editing.priority_distance,
            transition_coords[0],
            transition_coords[1],
            0,
            transition_coords[2],
            transition_coords[3],
            1,
            0,
        )
        [rectangle_width_half, rectangle_height_half] = _get_rectangle_dimensions(transition_tag + "rectangle")
        main_window.canvas.coords(
            transition_tag + "rectangle",
            priority_middle_x - rectangle_width_half,
            priority_middle_y - rectangle_height_half,
            priority_middle_x + rectangle_width_half,
            priority_middle_y + rectangle_height_half,
        )
        main_window.canvas.coords(transition_tag + "priority", priority_middle_x, priority_middle_y)
        list_of_grid_line_canvas_ids = main_window.canvas.find_withtag("grid_line")
        if list_of_grid_line_canvas_ids:
            main_window.canvas.tag_raise(transition_tag, "grid_line")
    else:
        end_state_coords = main_window.canvas.coords(end_state_tag)
        end_state_radius = (end_state_coords[2] - end_state_coords[0]) / 2

        transition_end_coords = vector_handling.shorten_vector(
            0,
            transition_coords[-4],
            transition_coords[-3],
            end_state_radius,
            transition_coords[-2],
            transition_coords[-1],
            0,
            1,
        )
        transition_coords[-2] = transition_end_coords[-2]
        transition_coords[-1] = transition_end_coords[-1]
        main_window.canvas.coords(transition_tag, transition_coords)
        main_window.canvas.tag_lower(transition_tag)


def _remove_duplicate_points(transition_coords) -> list:
    new_transition_coords = []
    new_transition_coords.append(transition_coords[0])
    new_transition_coords.append(transition_coords[1])
    for i in range(int(len(transition_coords) / 2) - 1):
        if (
            transition_coords[2 * i] != transition_coords[2 * i + 2]
            or transition_coords[2 * i + 1] != transition_coords[2 * i + 3]
        ):
            new_transition_coords.append(transition_coords[2 * i + 2])
            new_transition_coords.append(transition_coords[2 * i + 3])
    return new_transition_coords


def transition_start(event) -> None:
    [event_x, event_y] = canvas_editing.translate_window_event_coordinates_in_exact_canvas_coordinates(event)
    ids = main_window.canvas.find_overlapping(event_x, event_y, event_x, event_y)
    if ids != ():
        for canvas_id in ids:
            element_type = main_window.canvas.type(canvas_id)
            if (
                element_type == "oval"
                or (element_type == "polygon" and _reset_entry_has_no_transition(canvas_id))
                or (element_type == "rectangle" and main_window.canvas.gettags(canvas_id)[0].startswith("connector"))
            ):
                for tag in main_window.canvas.gettags(canvas_id):
                    if (
                        (tag.startswith("state") and not tag.endswith("_comment_line_end"))
                        or tag.startswith("connector")
                        or tag.startswith("reset_entry")
                    ):
                        tag_of_object_where_transition_starts = tag
                        main_window.canvas.addtag_withtag(
                            "transition" + str(transition_number) + "_start", tag_of_object_where_transition_starts
                        )
                start_object_coords = main_window.canvas.coords(tag_of_object_where_transition_starts)
                if element_type in ["oval", "rectangle"]:
                    line_start_x = start_object_coords[0] / 2 + start_object_coords[2] / 2
                    line_start_y = start_object_coords[1] / 2 + start_object_coords[3] / 2
                else:  # polygon, this means reset-entry
                    line_start_x = start_object_coords[4]
                    line_start_y = start_object_coords[5]
                # Create first a line with length 0:
                transition_id = main_window.canvas.create_line(
                    line_start_x,
                    line_start_y,
                    line_start_x,
                    line_start_y,
                    arrow="last",
                    fill="blue",
                    smooth=True,
                    tags=(
                        "transition" + str(transition_number),
                        "coming_from_" + tag_of_object_where_transition_starts,
                    ),
                )
                main_window.canvas.tag_bind(
                    transition_id,
                    "<Enter>",
                    lambda event, transition_id=transition_id: main_window.canvas.itemconfig(transition_id, width=3),
                )
                main_window.canvas.tag_bind(
                    transition_id,
                    "<Leave>",
                    lambda event, transition_id=transition_id: main_window.canvas.itemconfig(transition_id, width=1),
                )
                main_window.canvas.tag_bind(
                    transition_id,
                    "<Button-3>",
                    lambda event, transition_id=transition_id: show_menu(event, transition_id),
                )
                main_window.root.unbind_all("<Escape>")
                transition_draw_funcid = main_window.canvas.bind(
                    "<Motion>",
                    lambda event, transition_id=transition_id: _transition_draw(event, transition_id),
                    add="+",
                )
                main_window.canvas.bind(
                    "<Button-1>",
                    lambda event,
                    transition_id=transition_id,
                    start_state=canvas_id,
                    transition_draw_funcid=transition_draw_funcid: _handle_next_added_transition_point(
                        event, transition_id, start_state, transition_draw_funcid
                    ),
                )
                main_window.root.bind_all(
                    "<Escape  >",
                    lambda event,
                    transition_id=transition_id,
                    transition_draw_funcid=transition_draw_funcid,
                    tag_of_object_where_transition_starts=tag_of_object_where_transition_starts,
                    tag_to_delete="transition" + str(transition_number) + "_start": _abort_inserting_transition(
                        transition_id, transition_draw_funcid, tag_of_object_where_transition_starts, tag_to_delete
                    ),
                )


def _reset_entry_has_no_transition(canvas_id) -> bool:
    tags_of_reset_entry = main_window.canvas.gettags(canvas_id)
    return all(not tag.startswith("transition") for tag in tags_of_reset_entry)


def _transition_draw(event, canvas_id) -> None:
    [event_x, event_y] = canvas_editing.translate_window_event_coordinates_in_exact_canvas_coordinates(event)
    coords_new = main_window.canvas.coords(canvas_id)
    coords_new[-2] = event_x
    coords_new[-1] = event_y
    main_window.canvas.coords(canvas_id, coords_new)


def _handle_next_added_transition_point(event, transition_id, start_state_canvas_id, transition_draw_funcid) -> None:
    global transition_number
    [event_x, event_y] = canvas_editing.translate_window_event_coordinates_in_exact_canvas_coordinates(event)
    transition_coords = main_window.canvas.coords(transition_id)
    transition_tags = main_window.canvas.gettags(transition_id)
    end_state_canvas_id = _get_canvas_id_of_state_or_connector_under_new_transition_point(event_x, event_y)
    transition_ends_at_connector = _check_if_transition_ends_at_connector(end_state_canvas_id)
    if end_state_canvas_id is None:
        if len(transition_coords) < 8:  # An additional intermediate point is added to the transition.
            _duplicate_last_transition_point_for_continuing_the_drawing_of_the_transition(
                transition_id, transition_coords, event_x, event_y
            )
    elif "coming_from_reset_entry" in transition_tags and transition_ends_at_connector is True:
        return
    elif end_state_canvas_id == start_state_canvas_id and len(transition_coords) == 4:
        # Going back to the start state with only 2 points cannot be drawn. The transition point is not accepted.
        return
    else:
        _end_transition_insertion_by_modifying_bindings(transition_draw_funcid)
        _add_tags_to_end_state_and_transition(end_state_canvas_id)
        transition_coords = _move_transition_end_point_to_the_middle_of_the_end_state(
            end_state_canvas_id, transition_id
        )
        transition_coords = _move_transition_start_and_end_point_to_the_edge_of_the_state_circle(
            start_state_canvas_id, end_state_canvas_id, transition_coords, transition_id
        )
        _add_priority_rectangle_to_the_new_transition(transition_coords, start_state_canvas_id)
        transition_number += 1
        undo_handling.design_has_changed()


def _check_if_transition_ends_at_connector(end_state_canvas_id) -> bool:
    if end_state_canvas_id is not None:
        end_state_tags = main_window.canvas.gettags(end_state_canvas_id)
        for tag in end_state_tags:
            if tag.startswith("connector"):
                return True
    return False


def _get_canvas_id_of_state_or_connector_under_new_transition_point(event_x, event_y) -> None:
    for canvas_id in main_window.canvas.find_overlapping(event_x, event_y, event_x, event_y):
        element_type = main_window.canvas.type(canvas_id)
        if (element_type == "oval") or (
            element_type == "rectangle" and main_window.canvas.gettags(canvas_id)[0].startswith("connector")
        ):
            return canvas_id
    return None


def _duplicate_last_transition_point_for_continuing_the_drawing_of_the_transition(
    transition_id, coords, event_x, event_y
) -> None:
    coords.append(event_x)
    coords.append(event_y)
    main_window.canvas.coords(transition_id, coords)


def _add_tags_to_end_state_and_transition(end_state_canvas_id) -> None:
    main_window.canvas.addtag_withtag("transition" + str(transition_number) + "_end", end_state_canvas_id)
    state_tags = main_window.canvas.gettags(end_state_canvas_id)
    for tag in state_tags:
        if (tag.startswith("state") and not tag.endswith("_comment_line_end")) or tag.startswith("connector"):
            end_state_tag = tag
            break
    main_window.canvas.addtag_withtag("going_to_" + end_state_tag, "transition" + str(transition_number))


def _move_transition_end_point_to_the_middle_of_the_end_state(end_state_canvas_id, transition_id):
    end_state_coords = main_window.canvas.coords(end_state_canvas_id)
    end_state_middle_x = end_state_coords[0] / 2 + end_state_coords[2] / 2
    end_state_middle_y = end_state_coords[1] / 2 + end_state_coords[3] / 2
    transition_coords = main_window.canvas.coords(transition_id)
    transition_coords[-2] = end_state_middle_x
    transition_coords[-1] = end_state_middle_y
    main_window.canvas.coords(transition_id, transition_coords)
    return transition_coords


def _abort_inserting_transition(
    transition_id, transition_draw_funcid, tag_of_object_where_transition_starts, tag_to_delete
) -> None:
    main_window.canvas.dtag(tag_of_object_where_transition_starts, tag_to_delete)
    main_window.canvas.delete(transition_id)
    _end_transition_insertion_by_modifying_bindings(transition_draw_funcid)


def _end_transition_insertion_by_modifying_bindings(transition_draw_funcid) -> None:
    # Restore bindings:
    main_window.root.unbind_all("<Escape>")
    main_window.canvas.unbind("<Motion>", transition_draw_funcid)
    main_window.canvas.bind("<Motion>", canvas_editing.store_mouse_position)
    main_window.canvas.bind("<Button-1>", transition_start)
    main_window.root.bind_all("<Escape>", lambda event: canvas_modify_bindings.switch_to_move_mode())


def _move_transition_start_and_end_point_to_the_edge_of_the_state_circle(
    start_state_canvas_id, end_state_canvas_id, transition_coords, transition_id
):
    start_object_coords = main_window.canvas.coords(start_state_canvas_id)
    end_state_coords = main_window.canvas.coords(end_state_canvas_id)
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
    main_window.canvas.coords(transition_id, transition_coords)
    return transition_coords


def _add_priority_rectangle_to_the_new_transition(transition_coords, start_state_canvas_id) -> None:
    priority_dict = determine_priorities_of_outgoing_transitions(start_state_canvas_id)
    if len(priority_dict) == 1:
        transition_priority_visibility = tk.HIDDEN
    else:
        transition_priority_visibility = tk.NORMAL
        for outgoing_transition in priority_dict:
            main_window.canvas.itemconfigure(outgoing_transition + "priority", state=tk.NORMAL)
            main_window.canvas.itemconfigure(outgoing_transition + "rectangle", state=tk.NORMAL)
    transition_priority = _get_unused_priority(priority_dict)
    # Determine middle of the priority rectangle position by calculating a shortened transition:
    [priority_middle_x, priority_middle_y, _, _] = vector_handling.shorten_vector(
        canvas_editing.priority_distance,
        transition_coords[0],
        transition_coords[1],
        0,
        transition_coords[2],
        transition_coords[3],
        1,
        0,
    )
    tag_of_new_transition = "transition" + str(transition_number)
    main_window.canvas.create_text(
        priority_middle_x,
        priority_middle_y,
        text=transition_priority,
        tag=(tag_of_new_transition + "priority"),
        font=canvas_editing.state_name_font,
    )
    text_rectangle = main_window.canvas.bbox(tag_of_new_transition + "priority")
    main_window.canvas.itemconfigure(tag_of_new_transition + "priority", state=transition_priority_visibility)
    main_window.canvas.create_rectangle(
        text_rectangle,
        tag=(tag_of_new_transition + "rectangle"),
        fill=constants.STATE_COLOR,
        state=transition_priority_visibility,
    )
    main_window.canvas.tag_raise(tag_of_new_transition + "priority")
    main_window.canvas.tag_bind(
        tag_of_new_transition + "priority",
        "<Double-Button-1>",
        lambda event, transition_tag=tag_of_new_transition: edit_priority(event, transition_tag),
    )


def determine_priorities_of_outgoing_transitions(start_state_canvas_id) -> dict:
    priority_dict = {}
    all_tags = main_window.canvas.gettags(start_state_canvas_id)
    for tag in all_tags:
        if tag.startswith("transition") and tag.endswith("_start"):
            transition_tag = tag.replace("_start", "")
            priority_dict[transition_tag] = main_window.canvas.itemcget(transition_tag + "priority", "text")
    return priority_dict


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


def edit_priority(event, transition_tag) -> None:
    main_window.canvas.unbind("<Button-1>")
    main_window.canvas.unbind_all("<Delete>")
    priority_tag = transition_tag + "priority"
    old_text = main_window.canvas.itemcget(priority_tag, "text")
    text_box = tk.Entry(main_window.canvas, width=10, justify=tk.CENTER)
    text_box.insert(tk.END, old_text)
    text_box.select_range(0, tk.END)
    text_box.bind(
        "<Return>",
        lambda event, transition_tag=transition_tag, text_box=text_box: _update_priority(transition_tag, text_box),
    )
    text_box.bind(
        "<Escape>",
        lambda event, transition_tag=transition_tag, text_box=text_box, old_text=old_text: _abort_edit_text(
            transition_tag, text_box, old_text
        ),
    )
    [event_x, event_y] = canvas_editing.translate_window_event_coordinates_in_exact_canvas_coordinates(event)
    main_window.canvas.create_window(event_x, event_y, window=text_box, tag="entry-window")
    text_box.focus_set()


def _update_priority(transition_tag, text_box) -> None:
    main_window.canvas.delete("entry-window")
    main_window.canvas.itemconfig(transition_tag + "priority", text=text_box.get())
    text_rectangle = main_window.canvas.bbox(transition_tag + "priority")
    main_window.canvas.coords(transition_tag + "rectangle", text_rectangle)
    text_box.destroy()
    main_window.canvas.tag_raise(transition_tag + "rectangle", transition_tag)
    main_window.canvas.tag_raise(transition_tag + "priority", transition_tag + "rectangle")
    undo_handling.design_has_changed()
    main_window.canvas.bind("<Button-1>", move_handling_initialization.move_initialization)
    main_window.canvas.bind_all("<Delete>", lambda event: canvas_editing.delete())


def _abort_edit_text(transition_tag, text_box, old_text) -> None:
    main_window.canvas.delete("entry-window")
    main_window.canvas.itemconfig(transition_tag + "priority", text=old_text)
    text_box.destroy()
    main_window.canvas.tag_raise(transition_tag + "rectangle", transition_tag)
    main_window.canvas.tag_raise(transition_tag + "priority", transition_tag + "rectangle")
    main_window.canvas.bind("<Button-1>", move_handling_initialization.move_initialization)
    main_window.canvas.bind_all("<Delete>", lambda event: canvas_editing.delete())


def show_menu(event, transition_id) -> None:
    listbox = OptionMenu(
        main_window.canvas,
        ["add condition&action", "straighten shape"],
        height=2,
        bg="lightgrey",
        width=21,
        activestyle="dotbox",
        relief=tk.RAISED,
    )
    [event_x, event_y] = canvas_editing.translate_window_event_coordinates_in_exact_canvas_coordinates(event)
    window = main_window.canvas.create_window(event_x + 40, event_y, window=listbox)
    listbox.bind(
        "<Button-1>",
        lambda event,
        window=window,
        listbox=listbox,
        menu_x=event_x,
        menu_y=event_y,
        transition_id=transition_id: _evaluate_menu(event, window, listbox, menu_x, menu_y, transition_id),
    )
    listbox.bind("<Leave>", lambda event, window=window, listbox=listbox: _close_menu(event, window, listbox))


def _evaluate_menu(event, window, listbox, menu_x, menu_y, transition_id) -> None:
    design_was_changed = False
    selected_entry = listbox.get(listbox.curselection())
    if selected_entry == "add condition&action":
        transition_tags = main_window.canvas.gettags(transition_id)
        has_condition_action = False
        connected_to_reset_entry = False
        for tag in transition_tags:
            if tag.startswith("ca_connection"):
                has_condition_action = True
            elif tag == "coming_from_reset_entry":
                connected_to_reset_entry = True
        if has_condition_action is False:
            condition_action_ref = condition_action_handling.ConditionAction(
                menu_x, menu_y, connected_to_reset_entry, height=1, width=8, padding=3, increment=True
            )
            condition_action_ref.tag(connected_to_reset_entry)
            condition_action_ref.draw_line(transition_id, menu_x, menu_y)
            condition_action_ref.condition_id.focus()  # Puts the text input cursor into the text box.
            design_was_changed = True
    elif selected_entry == "straighten shape":
        transition_tags = main_window.canvas.gettags(transition_id)
        start_state_radius = 0
        end_state_radius = 0
        for tag in transition_tags:
            if tag.startswith("transition"):
                transition_tag = tag
                extend_transition_to_state_middle_points(transition_tag)
            elif tag.startswith("coming_from_"):
                start_state = tag.replace("coming_from_", "")
                if start_state == "reset_entry":
                    start_state_radius = 0
                else:
                    start_state_coords = main_window.canvas.coords(start_state)
                    start_state_radius = abs(start_state_coords[2] - start_state_coords[0]) / 2
            elif tag.startswith("going_to_"):
                end_state = tag.replace("going_to_", "")
                end_state_coords = main_window.canvas.coords(end_state)
                end_state_radius = abs(end_state_coords[2] - end_state_coords[0]) / 2
        old_coords = main_window.canvas.coords(transition_id)
        new_coords = []
        new_coords.append(old_coords[0])
        new_coords.append(old_coords[1])
        new_coords.append(old_coords[-2])
        new_coords.append(old_coords[-1])
        new_coords = vector_handling.shorten_vector(
            start_state_radius, new_coords[0], new_coords[1], end_state_radius, new_coords[2], new_coords[3], 1, 1
        )
        main_window.canvas.coords(transition_id, new_coords)
        # Calculates the position of the priority rectangle by shortening the distance between the first point of transition and the second point of the transition.
        [priority_middle_x, priority_middle_y, _, _] = vector_handling.shorten_vector(
            canvas_editing.priority_distance, new_coords[0], new_coords[1], 0, new_coords[2], new_coords[3], 1, 0
        )
        [rectangle_width_half, rectangle_height_half] = _get_rectangle_dimensions(transition_tag + "rectangle")
        main_window.canvas.coords(
            transition_tag + "rectangle",
            priority_middle_x - rectangle_width_half,
            priority_middle_y - rectangle_height_half,
            priority_middle_x + rectangle_width_half,
            priority_middle_y + rectangle_height_half,
        )
        main_window.canvas.coords(transition_tag + "priority", priority_middle_x, priority_middle_y)
        main_window.canvas.tag_raise(transition_tag + "rectangle", transition_tag)
        main_window.canvas.tag_raise(transition_tag + "priority", transition_tag + "rectangle")
        design_was_changed = True
    listbox.destroy()
    main_window.canvas.delete(window)
    if design_was_changed:
        undo_handling.design_has_changed()  # It must be waited until the window for the menu is deleted.


def _close_menu(event, window, listbox) -> None:
    listbox.destroy()
    main_window.canvas.delete(window)
