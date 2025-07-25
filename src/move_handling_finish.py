"""
Includes all methods needed, when the moving objects ends.
"""

import tkinter as tk

import canvas_editing
import condition_action_handling
import main_window
import move_handling
import move_handling_initialization
import state_handling
import transition_handling
import undo_handling
import vector_handling


def move_finish(event, move_list, move_do_funcid) -> None:
    [event_x, event_y] = canvas_editing.translate_window_event_coordinates_in_exact_canvas_coordinates(event)

    item_ids_at_moving_end_location = _get_item_ids_at_moving_end_location(event_x, event_y, move_list)

    transition_start_or_end_point_is_moved = _check_if_only_transition_start_or_end_point_is_moved(move_list)
    if transition_start_or_end_point_is_moved and _moving_of_transition_start_or_end_point_ends_at_illegal_place(
        item_ids_at_moving_end_location, move_list
    ):
        return

    # Moving can be finished:
    move_handling.move_do(event, move_list, first=False)  # Move to the grid defined by state_radius.
    main_window.canvas.unbind("<ButtonRelease-1>")
    main_window.canvas.unbind(
        "<Motion>", move_do_funcid
    )  # unbinds motion completely, probably because of "lambda" use.
    main_window.canvas.bind("<Motion>", canvas_editing.store_mouse_position)
    main_window.canvas.bind("<Button-1>", move_handling_initialization.move_initialization)

    if transition_start_or_end_point_is_moved:
        transition_id = move_list[0][0]
        transition_point = move_list[0][1]
        _move_the_line_to_the_center_of_the_target(
            item_ids_at_moving_end_location, transition_id, transition_point, move_list
        )
        _update_the_tags_of_the_transition(item_ids_at_moving_end_location, transition_id, transition_point)
    _shorten_all_moved_transitions_to_the_state_borders(move_list)
    _move_all_ca_connection_end_points_to_the_new_transition_start_points(move_list)
    _hide_the_connection_line_of_moved_condition_action_window(
        move_list
    )  # needed when a condition_action_window is moved alone.
    main_window.canvas.tag_lower("grid_line")
    undo_handling.design_has_changed()


def _get_item_ids_at_moving_end_location(event_x, event_y, move_list) -> list:
    move_items = []
    for move_entry in move_list:
        move_items.append(move_entry[0])
        if main_window.canvas.type(move_entry[0]) == "oval":
            move_items.append(state_handling.get_canvas_id_of_state_name(move_entry[0]))
    overlapping_items = main_window.canvas.find_overlapping(event_x, event_y, event_x, event_y)
    item_ids_at_moving_end_location = []
    for item in overlapping_items:
        if item not in move_items:
            item_ids_at_moving_end_location.append(item)
    return item_ids_at_moving_end_location


def _check_if_only_transition_start_or_end_point_is_moved(move_list) -> bool:
    return main_window.canvas.type(move_list[0][0]) == "line" and move_list[0][1] in ["start", "end"]


def _moving_of_transition_start_or_end_point_ends_at_illegal_place(item_ids_at_moving_end_location, move_list) -> bool:
    if _a_line_is_moved_to_a_window(item_ids_at_moving_end_location):
        return True
    if _a_line_is_moved_to_a_priority_rectangle(item_ids_at_moving_end_location):
        return True
    if _a_line_start_or_end_point_is_moved_to_a_line(item_ids_at_moving_end_location):
        return True
    if _a_point_of_a_line_is_moved_illegally_to_a_reset_entry(item_ids_at_moving_end_location, move_list):
        return True
    if _start_or_end_of_a_line_was_moved_to_free_space(item_ids_at_moving_end_location):
        return True
    return bool(_transition_connects_reset_entry_and_connector(item_ids_at_moving_end_location, move_list))


def _move_the_line_to_the_center_of_the_target(
    item_ids_at_moving_end_location, transition_id, transition_point, move_list
) -> None:
    for target in item_ids_at_moving_end_location:
        target_coords = main_window.canvas.coords(target)
        target_type = main_window.canvas.type(target)
        if target_type == "polygon":
            polygon_coords = main_window.canvas.coords(target)
            transition_handling.move_to(
                polygon_coords[4], polygon_coords[5], transition_id, transition_point, False, move_list, False
            )
        elif target_type in ["oval", "rectangle"]:
            state_middle_x = (target_coords[2] + target_coords[0]) / 2
            state_middle_y = (target_coords[3] + target_coords[1]) / 2
            transition_handling.move_to(
                state_middle_x, state_middle_y, transition_id, transition_point, False, move_list, False
            )


# def move_to(event_x, event_y, transition_id, point, first, move_list, last):
def _update_the_tags_of_the_transition(item_ids_at_moving_end_location, transition_id, transition_point) -> None:
    transition_tags = main_window.canvas.gettags(transition_id)
    transition_tag = ""
    condition_action_tag = ""
    ref = None
    for tag in transition_tags:
        if tag.startswith("transition"):
            transition_tag = tag
        elif tag.startswith("ca_connection"):
            condition_action_tag = tag[:-4]
            condition_action_window_id = main_window.canvas.find_withtag(condition_action_tag + "_anchor")[0]
            ref = condition_action_handling.ConditionAction.dictionary[condition_action_window_id]
    for target_id in item_ids_at_moving_end_location:
        if main_window.canvas.type(target_id) in ["oval", "rectangle", "polygon"]:
            target_tag = main_window.canvas.gettags(target_id)[
                0
            ]  # target_tag is equal to "state<n>" or "connector<n>" or "reset_entry"
            if transition_point == "start":
                main_window.canvas.addtag_withtag(
                    "coming_from_" + target_tag, transition_id
                )  # update tags of transition
                main_window.canvas.addtag_withtag(
                    transition_tag + "_start", target_id
                )  # update tags of the start object of the transition.
                if condition_action_tag != "":
                    if target_tag == "reset_entry":
                        main_window.canvas.addtag_withtag("connected_to_reset_transition", condition_action_tag)
                        ref.change_descriptor_to("Transition actions (asynchronous):")
                    else:
                        ref.change_descriptor_to("Transition actions (clocked):")
                priority_dict = transition_handling.determine_priorities_of_outgoing_transitions(target_id)
                transition_priority_visibility = tk.HIDDEN if len(priority_dict) == 1 else tk.NORMAL
                for outgoing_transition in priority_dict:
                    main_window.canvas.itemconfigure(
                        outgoing_transition + "priority", state=transition_priority_visibility
                    )
                    main_window.canvas.itemconfigure(
                        outgoing_transition + "rectangle", state=transition_priority_visibility
                    )
            elif transition_point == "end":
                main_window.canvas.addtag_withtag("going_to_" + target_tag, transition_id)  # update tags of transition
                main_window.canvas.addtag_withtag(
                    transition_tag + "_end", target_id
                )  # update tags of the end state of the transition.


def _shorten_all_moved_transitions_to_the_state_borders(move_list) -> None:
    done = []  # prevent transitions to be shortened twice (would happen at transitions that point from a state to the same state back).
    for move_list_entry in move_list:
        # print("move_list_entry =", move_list_entry)
        if move_list_entry[1] in ["start", "next_to_start", "next_to_end", "end"] and move_list_entry[0] not in done:
            tags_of_moved_object = main_window.canvas.gettags(move_list_entry[0])
            transition_tag = None
            for tag in tags_of_moved_object:
                if tag.startswith("transition"):
                    transition_tag = tag
            if transition_tag is not None:  # A "connection" or a "ca_connection"must not be shortened.
                transition_coords = vector_handling.try_to_convert_into_straight_line(
                    main_window.canvas.coords(transition_tag)
                )
                main_window.canvas.coords(transition_tag, transition_coords)
                transition_handling.shorten_to_state_border(transition_tag)
                done.append(move_list_entry[0])


def _move_all_ca_connection_end_points_to_the_new_transition_start_points(move_list) -> None:
    for move_list_entry in move_list:
        if (
            main_window.canvas.type(move_list_entry[0]) == "line"
        ):  # and move_list[n][1]=="start": # Only transition-lines are stored in move_list.
            tags_of_moved_object = main_window.canvas.gettags(move_list_entry[0])
            for tag in tags_of_moved_object:
                if tag.startswith("ca_connection"):
                    ca_connection_tag = tag[:-4]
                    ca_connection_coords = main_window.canvas.coords(ca_connection_tag)
                    transition_coords = main_window.canvas.coords(move_list_entry[0])
                    main_window.canvas.coords(
                        ca_connection_tag,
                        ca_connection_coords[0],
                        ca_connection_coords[1],
                        transition_coords[0],
                        transition_coords[1],
                    )


def _hide_the_connection_line_of_moved_condition_action_window(move_list) -> None:
    for move_list_entry in move_list:
        if main_window.canvas.type(move_list_entry[0]) == "window":
            tags = main_window.canvas.gettags(move_list_entry[0])
            for t in tags:
                if t.startswith("condition_action"):
                    ref = condition_action_handling.ConditionAction.dictionary[move_list_entry[0]]
                    ref.hide_line()


def _a_line_is_moved_to_a_window(item_ids_at_moving_end_location) -> bool:
    return any(main_window.canvas.type(target) == "window" for target in item_ids_at_moving_end_location)


def _a_line_is_moved_to_a_priority_rectangle(item_ids_at_moving_end_location) -> bool:
    for target in item_ids_at_moving_end_location:
        # if main_window.canvas.type(target)=="rectangle" and main_window.canvas.gettags(target)[0].endswith("rectangle"):
        if main_window.canvas.type(target) == "rectangle" and main_window.canvas.gettags(target)[0].startswith(
            "transition"
        ):
            return True
    return False


def _a_line_start_or_end_point_is_moved_to_a_line(item_ids_at_moving_end_location) -> bool:
    target_is_a_line = True
    for target in item_ids_at_moving_end_location:
        if main_window.canvas.type(target) in ["oval", "rectangle", "polygon"]:
            target_is_a_line = False
    if target_is_a_line is True:
        for target in item_ids_at_moving_end_location:
            if main_window.canvas.type(target) == "line":
                return True
    return False


def _a_point_of_a_line_is_moved_illegally_to_a_reset_entry(item_ids_at_moving_end_location, move_list) -> bool:
    for target in item_ids_at_moving_end_location:
        if main_window.canvas.type(target) == "polygon":
            for move_list_entry in move_list:
                if move_list_entry[1] == "end" and main_window.canvas.gettags(move_list_entry[0])[0].startswith(
                    "transition"
                ):
                    # print("a_point_of_a_line_is_moved_illegally_to_a_reset_entry: user tried to connect end point of a transition to a reset entry.")
                    return True
                elif move_list_entry[1] == "start":
                    reset_entry_tags = main_window.canvas.gettags(target)
                    for reset_entry_tag in reset_entry_tags:
                        if reset_entry_tag.startswith("transition"):
                            connected_transition_tag = reset_entry_tag[0:-6]
                            moved_transition_tags = main_window.canvas.gettags(move_list_entry[0])
                            for tag in moved_transition_tags:
                                if tag.startswith("transition"):
                                    if connected_transition_tag != tag:
                                        # print("user tried to connect start point of a transition to a already connected reset entry.")
                                        return True
    return False


def _start_or_end_of_a_line_was_moved_to_free_space(item_ids_at_moving_end_location) -> bool:
    return item_ids_at_moving_end_location == []


def _transition_connects_reset_entry_and_connector(item_ids_at_moving_end_location, move_list) -> bool:
    for target in item_ids_at_moving_end_location:
        if main_window.canvas.type(target) == "rectangle":
            for move_list_entry in move_list:
                moved_object_tags = main_window.canvas.gettags(move_list_entry[0])
                if "coming_from_reset_entry" in moved_object_tags:
                    return True
    return False
