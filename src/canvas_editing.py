"""
This module contains method used when the user edits the diagram.
"""

import re
import tkinter as tk
from tkinter import font, messagebox

import canvas_modify_bindings
import condition_action_handling
import config
import custom_text
import global_actions
import global_actions_combinatorial
import global_actions_handling
import main_window
import move_handling_initialization
import reset_entry_handling
import state_action_handling
import state_actions_default
import state_comment
import undo_handling
from widgets.OptionMenu import OptionMenu

# import inspect

# Global variables:
state_radius = 20.0
priority_distance = 30
reset_entry_size = 40
canvas_x_coordinate = 0
canvas_y_coordinate = 0
windows_x_coordinate = 0
windows_y_coordinate = 0
windows_x_coordinate_old = 0
windows_y_coordinate_old = 0
fontsize = 10
label_fontsize = 8
state_name_font = None


def store_mouse_position(event):  # used by delete().
    global canvas_x_coordinate, canvas_y_coordinate
    global windows_x_coordinate, windows_y_coordinate
    global windows_x_coordinate_old, windows_y_coordinate_old
    windows_x_coordinate_old = windows_x_coordinate
    windows_y_coordinate_old = windows_y_coordinate
    windows_x_coordinate = event.x
    windows_y_coordinate = event.y
    [canvas_x_coordinate, canvas_y_coordinate] = translate_window_event_coordinates_in_exact_canvas_coordinates(event)


def create_font_for_state_names():  # Called once by create_diagram_notebook_tab().
    global state_name_font
    state_name_font = font.Font(font="TkDefaultFont")
    state_name_font.configure(size=int(fontsize))


def translate_window_event_coordinates_in_rounded_canvas_coordinates(event):
    canvas_grid_x_coordinate = main_window.canvas.canvasx(event.x, gridspacing=state_radius)
    canvas_grid_y_coordinate = main_window.canvas.canvasy(event.y, gridspacing=state_radius)
    return [canvas_grid_x_coordinate, canvas_grid_y_coordinate]


def translate_window_event_coordinates_in_exact_canvas_coordinates(event):
    canvas_grid_x_coordinate, canvas_grid_y_coordinate = (
        main_window.canvas.canvasx(event.x),
        main_window.canvas.canvasy(event.y),
    )
    return [canvas_grid_x_coordinate, canvas_grid_y_coordinate]


def delete():
    # The event coordinates cannot be used, as the event is caused by pressing the delete-button and the delete-button "coordinates" are useless.
    # When moving the mouse into a window-canvas-item the mouse position in the canvas can not
    # detected anymore (only the mouse position in the window can be detected now).
    # So the last mouse position outside the window-canvas-item is the only available information.
    # But this position may be by 1 pixel outside the window-canvas-item.
    # So the area is increased here:
    ids = main_window.canvas.find_overlapping(
        canvas_x_coordinate - 2, canvas_y_coordinate - 2, canvas_x_coordinate + 2, canvas_y_coordinate + 2
    )
    for i in ids:
        tags_of_item_i = main_window.canvas.gettags(i)
        if main_window.canvas.type(i) is None:
            # This item i is a member of the list stored in ids but was already deleted,
            # when one of the items earlier in the list was deleted.
            pass
        elif main_window.canvas.type(i) == "polygon":  # Only the reset_entry is a polygon.
            for tag in tags_of_item_i:  # Remove reset entry and connected transition.
                if tag.startswith("reset_entry"):
                    main_window.canvas.delete(tag)  # delete polygon
                    main_window.canvas.delete("reset_text")  # delete text item
                    reset_entry_handling.reset_entry_number = 0
                    main_window.reset_entry_button.config(state=tk.NORMAL)
                elif tag.startswith("transition") and tag.endswith("_start"):  # transition<n>_start
                    transition = tag[0:-6]
                    transition_tags = main_window.canvas.gettags(transition)
                    for transition_tag in transition_tags:
                        if transition_tag.startswith("going_to_"):
                            state = transition_tag[9:]
                            main_window.canvas.dtag(state, transition + "_end")
                        elif transition_tag.startswith("ca_connection"):
                            condition_action_tag = transition_tag[:-4]
                            main_window.canvas.delete(condition_action_tag + "_anchor")
                    main_window.canvas.delete(transition)
                    main_window.canvas.delete(transition + "rectangle")  # delete priority rectangle
                    main_window.canvas.delete(transition + "priority")  # delete priority
            undo_handling.design_has_changed()
        elif main_window.canvas.type(i) == "window":
            # Delete the window and all tags which refer to this window:
            for tag in tags_of_item_i:
                item_id = main_window.canvas.find_withtag(tag)
                if tag.startswith("state_actions_default"):
                    ref = state_actions_default.StateActionsDefault.dictionary[item_id[0]]
                    del custom_text.CustomText.read_variables_of_all_windows[ref.text_id]
                    del custom_text.CustomText.written_variables_of_all_windows[ref.text_id]
                    main_window.canvas.delete(tag)  # delete window
                    global_actions_handling.state_actions_default_number = 0
                    main_window.state_action_default_button.config(state=tk.NORMAL)
                elif tag.startswith("state_action"):
                    ref = state_action_handling.MyText.mytext_dict[item_id[0]]
                    del custom_text.CustomText.read_variables_of_all_windows[ref.text_id]
                    del custom_text.CustomText.written_variables_of_all_windows[ref.text_id]
                    main_window.canvas.delete(tag)  # delete window
                elif tag.endswith("_comment"):
                    main_window.canvas.delete(tag)  # delete window
                    main_window.canvas.delete(tag + "_line")  # delete line to window
                    main_window.canvas.dtag(
                        tag.replace("_comment", ""), tag + "_line_end"
                    )  # delete at state: "state"<integer>"_comment_line_end"
                elif tag.startswith("condition_action"):
                    ref = condition_action_handling.ConditionAction.dictionary[item_id[0]]
                    del custom_text.CustomText.read_variables_of_all_windows[ref.condition_id]
                    del custom_text.CustomText.written_variables_of_all_windows[ref.condition_id]
                    del custom_text.CustomText.read_variables_of_all_windows[ref.action_id]
                    del custom_text.CustomText.written_variables_of_all_windows[ref.action_id]
                    main_window.canvas.delete(tag)  # delete window
                elif tag == "global_actions1":
                    ref = global_actions.GlobalActions.dictionary[item_id[0]]
                    del custom_text.CustomText.read_variables_of_all_windows[ref.text_before_id]
                    del custom_text.CustomText.written_variables_of_all_windows[ref.text_before_id]
                    del custom_text.CustomText.read_variables_of_all_windows[ref.text_after_id]
                    del custom_text.CustomText.written_variables_of_all_windows[ref.text_after_id]
                    main_window.canvas.delete(tag)  # delete window
                    global_actions_handling.global_actions_clocked_number = 0
                    main_window.global_action_clocked_button.config(state=tk.NORMAL)
                elif tag == "global_actions_combinatorial1":
                    ref = global_actions_combinatorial.GlobalActionsCombinatorial.dictionary[item_id[0]]
                    del custom_text.CustomText.read_variables_of_all_windows[ref.text_id]
                    del custom_text.CustomText.written_variables_of_all_windows[ref.text_id]
                    main_window.canvas.delete(tag)  # delete window
                    global_actions_handling.global_actions_combinatorial_number = 0
                    main_window.global_action_combinatorial_button.config(state=tk.NORMAL)
                elif tag.startswith("connection"):  # connection<n>_start
                    connection = tag[0:-6]
                    connection_tags = main_window.canvas.gettags(connection)
                    for connection_tag in connection_tags:
                        if connection_tag.startswith("connected_to_state"):
                            state = connection_tag[13:]
                    main_window.canvas.dtag(state, tag[0:-6] + "_end")  # delete tag "connection<n>_end" at state.
                    main_window.canvas.delete(tag[0:-6])  # delete connection
                elif tag.startswith("ca_connection"):  # ca_connection<n>_anchor
                    ca_connection = tag[0:-7]
                    ca_connection_tags = main_window.canvas.gettags(ca_connection)
                    for ca_connection_tag in ca_connection_tags:
                        if ca_connection_tag.startswith("connected_to_transition"):
                            transition = ca_connection_tag[13:]
                    main_window.canvas.dtag(
                        transition, tag[0:-7] + "_end"
                    )  # delete tag "ca_connection<n>_end" at state.
                    main_window.canvas.delete(tag[0:-7])  # delete connection
            undo_handling.design_has_changed()
        elif main_window.canvas.type(i) == "oval":
            for tag in tags_of_item_i:
                if tag.startswith("state") and not tag.endswith("_comment_line_end"):
                    main_window.canvas.delete(tag)  # delete state
                    main_window.canvas.delete(tag + "_name")  # delete state
                elif tag.startswith("connection") and tag.endswith("_end"):  # connection<n>_end
                    connection = tag[0:-4]
                    main_window.canvas.delete(connection)  # delete connection (line)
                    main_window.canvas.delete(connection + "_start")  # delete action window
                    main_window.canvas.dtag(i, connection + "_end")  # delete connection<n>_end tag from state
                elif tag.startswith("transition") and tag.endswith("_end"):  # transition<n>_end
                    transition = tag[0:-4]
                    transition_tags = main_window.canvas.gettags(transition)
                    for transition_tag in transition_tags:
                        if transition_tag.startswith("coming_from_"):
                            state = transition_tag[12:]
                            main_window.canvas.dtag(state, transition + "_start")
                            adapt_visibility_of_priority_rectangles_at_state(state)
                        elif transition_tag.startswith("ca_connection"):
                            condition_action_tag = transition_tag[:-4]
                            main_window.canvas.delete(condition_action_tag + "_anchor")  # delete the window
                            main_window.canvas.delete(condition_action_tag)  # delete the line to the window
                    main_window.canvas.delete(transition)
                    main_window.canvas.delete(transition + "rectangle")  # delete priority rectangle
                    main_window.canvas.delete(transition + "priority")  # delete priority
                elif tag.startswith("transition") and tag.endswith("_start"):  # transition<n>_start
                    transition = tag[0:-6]
                    transition_tags = main_window.canvas.gettags(transition)
                    for transition_tag in transition_tags:
                        if transition_tag.startswith("going_to_"):
                            state = transition_tag[9:]
                            main_window.canvas.dtag(state, transition + "_end")
                        elif transition_tag.startswith("ca_connection"):
                            condition_action_tag = transition_tag[:-4]
                            main_window.canvas.delete(condition_action_tag + "_anchor")
                    main_window.canvas.delete(transition)
                    main_window.canvas.delete(transition + "rectangle")  # delete priority rectangle
                    main_window.canvas.delete(transition + "priority")  # delete priority
                elif tag.endswith("comment_line_end"):
                    canvas_id_of_comment_line = tag[:-4]
                    canvas_id_of_comment = tag[:-9]
                    main_window.canvas.delete(canvas_id_of_comment_line)
                    main_window.canvas.delete(canvas_id_of_comment)
            undo_handling.design_has_changed()
        elif main_window.canvas.type(i) == "rectangle":
            for tag in tags_of_item_i:
                if tag.startswith("connector"):
                    main_window.canvas.delete(tag)  # delete connector
                elif tag.startswith("transition") and tag.endswith("_end"):  # transition<n>_end
                    transition = tag[0:-4]
                    transition_tags = main_window.canvas.gettags(transition)
                    for transition_tag in transition_tags:
                        if transition_tag.startswith("coming_from_"):
                            state = transition_tag[12:]
                            main_window.canvas.dtag(state, transition + "_start")
                            adapt_visibility_of_priority_rectangles_at_state(state)
                        elif transition_tag.startswith("ca_connection"):
                            condition_action_tag = transition_tag[:-4]
                            main_window.canvas.delete(condition_action_tag + "_anchor")
                    main_window.canvas.delete(transition)
                    main_window.canvas.delete(transition + "rectangle")  # delete priority rectangle
                    main_window.canvas.delete(transition + "priority")  # delete priority
                elif tag.startswith("transition") and tag.endswith("_start"):  # transition<n>_start
                    transition = tag[0:-6]
                    transition_tags = main_window.canvas.gettags(transition)
                    for transition_tag in transition_tags:
                        if transition_tag.startswith("going_to_"):
                            state = transition_tag[9:]
                            main_window.canvas.dtag(state, transition + "_end")
                        elif transition_tag.startswith("ca_connection"):
                            condition_action_tag = transition_tag[:-4]
                            main_window.canvas.delete(condition_action_tag + "_anchor")
                    main_window.canvas.delete(transition)
                    main_window.canvas.delete(transition + "rectangle")  # delete priority rectangle
                    main_window.canvas.delete(transition + "priority")  # delete priority
            undo_handling.design_has_changed()
        elif main_window.canvas.type(i) == "line" and "grid_line" not in main_window.canvas.gettags(
            i
        ):  # transition (can be deleted) or connection (cannot be deleted)
            # Remove transition-line, transition-priority, condition-action-block:
            for tag in tags_of_item_i:
                if tag.startswith("transition"):
                    main_window.canvas.delete(tag)  # delete transition
                    main_window.canvas.delete(tag + "rectangle")  # delete priority rectangle
                    main_window.canvas.delete(tag + "priority")  # delete priority
                    transition = tag  # carries "transition<n>"
                elif tag.startswith("ca_connection"):  # Line to condition-action block
                    condition_action_tag = tag[:-4]
                    main_window.canvas.delete(condition_action_tag + "_anchor")
            # Now the tag of the transition is known and the tags of the start- and end-state can be adapted:
            for tag in tags_of_item_i:
                if tag.startswith("coming_from_"):
                    start_state = tag[12:]
                    main_window.canvas.dtag(start_state, transition + "_start")
                elif tag.startswith("going_to_"):
                    end_state = tag[9:]
                    main_window.canvas.dtag(end_state, transition + "_end")
            adapt_visibility_of_priority_rectangles_at_state(start_state)
            undo_handling.design_has_changed()
        elif main_window.canvas.type(i) == "line" and "grid_line" in main_window.canvas.gettags(
            i
        ):  # grid line cannot be deleted.
            pass
        else:
            messagebox.showerror(
                "Delete",
                "Fatal, cannot delete canvas_type "
                + str(main_window.canvas.type(i))
                + " with tags "
                + str(main_window.canvas.gettags(i)),
            )


def adapt_visibility_of_priority_rectangles_at_state(start_state):
    tags_of_start_state = main_window.canvas.gettags(start_state)
    number_of_outgoing_transitions = 0
    tag_of_outgoing_transition = ""
    for start_state_tag in tags_of_start_state:
        if start_state_tag.startswith("transition") and start_state_tag.endswith("_start"):
            number_of_outgoing_transitions += 1
            tag_of_outgoing_transition = start_state_tag.replace("_start", "")
    if number_of_outgoing_transitions == 1:
        main_window.canvas.itemconfigure(tag_of_outgoing_transition + "rectangle", state=tk.HIDDEN)
        main_window.canvas.itemconfigure(tag_of_outgoing_transition + "priority", state=tk.HIDDEN)


def start_view_rectangle(event):
    [event_x, event_y] = translate_window_event_coordinates_in_exact_canvas_coordinates(event)
    rectangle_id = main_window.canvas.create_rectangle(event_x, event_y, event_x, event_y, dash=(3, 5))
    main_window.canvas.tag_raise(rectangle_id, "all")
    main_window.canvas.bind("<Motion>", lambda event: draw_view_rectangle(event, rectangle_id))
    main_window.canvas.bind("<ButtonRelease-1>", lambda event: view_area(rectangle_id))
    main_window.canvas.bind("<ButtonRelease-3>", lambda event: view_area_by_button3(rectangle_id))


def draw_view_rectangle(event, rectangle_id):  # Called by Motion-event.
    [event_x, event_y] = translate_window_event_coordinates_in_exact_canvas_coordinates(event)
    rectangle_coords = main_window.canvas.coords(rectangle_id)
    if event_x > rectangle_coords[0] and event_y > rectangle_coords[1]:
        main_window.canvas.coords(rectangle_id, rectangle_coords[0], rectangle_coords[1], event_x, event_y)


def view_area_by_button3(rectangle_id):
    rectangle_coords = main_window.canvas.coords(rectangle_id)
    if rectangle_coords[0] != rectangle_coords[2] and rectangle_coords[1] != rectangle_coords[3]:
        view_area(rectangle_id)
    else:
        main_window.canvas.delete(rectangle_id)
        overlapping_canvas_ids = main_window.canvas.find_overlapping(
            rectangle_coords[0] - 5, rectangle_coords[1] - 5, rectangle_coords[0] + 5, rectangle_coords[1] + 5
        )
        item_found = False
        for canvas_id in overlapping_canvas_ids:
            tags = main_window.canvas.gettags(canvas_id)
            if "grid_line" not in tags:
                item_found = True
        if not item_found:
            __show_menu(rectangle_coords)
        main_window.canvas.unbind("<Motion>")
        main_window.canvas.unbind("<ButtonRelease-1>")
        main_window.canvas.unbind("<ButtonRelease-3>")
        # Restore the original binding (Button-1 is bound to start_view_rectangle(), when "view area"-Button was used):
        main_window.canvas.bind("<Button-1>", move_handling_initialization.move_initialization)
        main_window.canvas.bind("<Motion>", store_mouse_position)


def view_area(
    rectangle_id,
):  # Called by Button-1("view area"-button)/Button-3(view area per right mouse-button)-Release-Event.
    main_window.grid_drawer.remove_grid()
    complete_rectangle = main_window.canvas.coords(rectangle_id)
    view_rectangle(complete_rectangle, check_fit=False)
    main_window.canvas.delete(rectangle_id)
    main_window.canvas.unbind("<Motion>")
    main_window.canvas.unbind("<ButtonRelease-1>")
    main_window.canvas.unbind("<ButtonRelease-3>")
    # Restore the original binding (Button-1 is bound to start_view_rectangle(), when "view area"-Button was used):
    main_window.canvas.bind("<Button-1>", move_handling_initialization.move_initialization)
    main_window.canvas.bind("<Motion>", store_mouse_position)
    main_window.grid_drawer.draw_grid()


def view_all():
    main_window.grid_drawer.remove_grid()
    complete_rectangle = main_window.canvas.bbox("all")
    if complete_rectangle is not None:
        view_rectangle(complete_rectangle, check_fit=True)
    main_window.canvas.update_idletasks()  # helps to get "after_idle" in view_rectangle() ready?!
    main_window.canvas.after_idle(
        main_window.grid_drawer.draw_grid
    )  # "after_idle" is needed because view_rectangle calls decrement_font_size_if_window_is_too_wide after idle.


def view_rectangle(complete_rectangle, check_fit):
    if complete_rectangle[2] - complete_rectangle[0] != 0 and complete_rectangle[3] - complete_rectangle[1] != 0:
        visible_rectangle = [
            main_window.canvas.canvasx(0),
            main_window.canvas.canvasy(0),
            main_window.canvas.canvasx(main_window.canvas.winfo_width()),
            main_window.canvas.canvasy(main_window.canvas.winfo_height()),
        ]
        factor = calculate_zoom_factor(complete_rectangle, visible_rectangle)
        too_big = False
        actual_rectangle = main_window.canvas.bbox("all")
        for coord in actual_rectangle:
            if (
                abs(coord) * factor > 100000
            ):  # The Canvas which is used, has a scrollregion +/-100000, so here this limit is checked (unclear if really necessary).
                too_big = True
        if too_big is False:
            complete_center = determine_center_of_rectangle(complete_rectangle)
            visible_center = determine_center_of_rectangle(visible_rectangle)
            move_canvas_point_from_to(complete_center, visible_center)
            canvas_zoom(complete_center, factor)
            if check_fit:
                main_window.canvas.after_idle(decrement_font_size_if_window_is_too_wide)
        else:
            messagebox.showerror("Fatal", "Zoom factor is too big.")
    canvas_modify_bindings.switch_to_move_mode()


def decrement_font_size_if_window_is_too_wide():
    visible_rectangle = [
        main_window.canvas.canvasx(0),
        main_window.canvas.canvasy(0),
        main_window.canvas.canvasx(main_window.canvas.winfo_width()),
        main_window.canvas.canvasy(main_window.canvas.winfo_height()),
    ]
    complete_rectangle = main_window.canvas.bbox("all")
    if (
        (
            complete_rectangle[0] < visible_rectangle[0]
            or complete_rectangle[1] < visible_rectangle[1]
            or complete_rectangle[2] > visible_rectangle[2]
            or complete_rectangle[3] > visible_rectangle[3]
        )
        and fontsize != 1  # When fontsize==1 then zoom_factor calculates to 0, which makes no sense.
    ):
        complete_center = determine_center_of_rectangle(complete_rectangle)
        visible_center = determine_center_of_rectangle(visible_rectangle)
        move_canvas_point_from_to(complete_center, visible_center)
        zoom_factor = (fontsize - 1) / fontsize
        canvas_zoom(complete_center, zoom_factor)
        main_window.canvas.after_idle(decrement_font_size_if_window_is_too_wide)


def determine_center_of_rectangle(rectangle_coords):
    return [(rectangle_coords[0] + rectangle_coords[2]) / 2, (rectangle_coords[1] + rectangle_coords[3]) / 2]


def move_canvas_point_from_to(complete_center, visible_center):
    main_window.canvas.scan_mark(int(complete_center[0]), int(complete_center[1]))
    main_window.canvas.scan_dragto(int(visible_center[0]), int(visible_center[1]), gain=1)


def calculate_zoom_factor(complete_rectangle, visible_rectangle):
    complete_width = complete_rectangle[2] - complete_rectangle[0]
    complete_height = complete_rectangle[3] - complete_rectangle[1]
    visible_width = visible_rectangle[2] - visible_rectangle[0]
    visible_height = visible_rectangle[3] - visible_rectangle[1]
    scale_x = visible_width / complete_width
    scale_y = visible_height / complete_height
    factor = min(scale_x, scale_y)
    return factor


def zoom_wheel(event):
    main_window.canvas.grid_remove()  # Make the canvas invisible, but remember all options for the the next grid() call.
    main_window.grid_drawer.remove_grid()
    # event.delta: attribute of the mouse wheel under Windows and MacOs.
    # One "felt step" at the mouse wheel gives this value:
    # Windows: delta=+/-120 ; MacOS: delta=+/-1 ; Linux: delta=0
    # num: attribute of the the mouse wheel under Linux  ("scroll-up=5" and "scroll-down=4").
    factor = 1
    if event.num == 5 or event.delta < 0:  # scroll down
        factor = 1 / 1.1
    elif event.num == 4 or event.delta >= 0:  # scroll up
        factor = 1.1
    zoom_center = translate_window_event_coordinates_in_exact_canvas_coordinates(event)
    canvas_zoom(zoom_center, factor)
    main_window.grid_drawer.draw_grid()
    canvas_modify_bindings.switch_to_move_mode()
    main_window.canvas.grid()


def zoom_plus():
    main_window.canvas.grid_remove()  # Make the canvas invisible.
    main_window.grid_drawer.remove_grid()
    factor = 1.1
    visible_rectangle = [
        main_window.canvas.canvasx(0),
        main_window.canvas.canvasy(0),
        main_window.canvas.canvasx(main_window.canvas.winfo_width()),
        main_window.canvas.canvasy(main_window.canvas.winfo_height()),
    ]
    visible_center = determine_center_of_rectangle(visible_rectangle)
    canvas_zoom(visible_center, factor)
    main_window.grid_drawer.draw_grid()
    main_window.canvas.grid()


def zoom_minus():
    main_window.canvas.grid_remove()  # Make the canvas invisible.
    main_window.grid_drawer.remove_grid()
    factor = 1 / 1.1
    visible_rectangle = [
        main_window.canvas.canvasx(0),
        main_window.canvas.canvasy(0),
        main_window.canvas.canvasx(main_window.canvas.winfo_width()),
        main_window.canvas.canvasy(main_window.canvas.winfo_height()),
    ]
    visible_center = determine_center_of_rectangle(visible_rectangle)
    canvas_zoom(visible_center, factor)
    main_window.grid_drawer.draw_grid()
    main_window.canvas.grid()


def canvas_zoom(zoom_center, zoom_factor):
    # Modify factor, so that fontsize is always an integer:
    fontsize_rounded_down = int(fontsize * zoom_factor)
    if zoom_factor > 1 and fontsize_rounded_down == fontsize:
        fontsize_rounded_down += 1
    if fontsize_rounded_down != 0:
        zoom_factor = fontsize_rounded_down / fontsize
        main_window.canvas.scale(
            "all", 0, 0, zoom_factor, zoom_factor
        )  # Scaling must use xoffset=0 and yoffset=0 to preserve the gridspacing of state_radius.
        scroll_canvas_to_show_the_zoom_center(zoom_center, zoom_factor)
        adapt_scroll_bars(zoom_factor)
        adapt_global_size_variables(zoom_factor)


def scroll_canvas_to_show_the_zoom_center(zoom_center, zoom_factor):
    new_position_of_zoom_center = [coord * zoom_factor for coord in zoom_center]
    main_window.canvas.scan_mark(
        int(new_position_of_zoom_center[0]), int(new_position_of_zoom_center[1])
    )  # Mark the point of the canvas, which serves as anchor for the shift.
    main_window.canvas.scan_dragto(int(zoom_center[0]), int(zoom_center[1]), gain=1)


def adapt_scroll_bars(factor):
    scrollregion_strings = main_window.canvas.cget("scrollregion").split()
    scrollregion_scaled = [int(float(x) * factor) for x in scrollregion_strings]
    main_window.canvas.configure(scrollregion=scrollregion_scaled)


def adapt_global_size_variables(factor):
    global state_radius
    global priority_distance
    global reset_entry_size
    state_radius = factor * state_radius  # publish new state radius
    priority_distance = factor * priority_distance
    reset_entry_size = factor * reset_entry_size
    modify_font_sizes_of_all_canvas_items(factor)


def scroll_start(event):
    main_window.grid_drawer.remove_grid()
    main_window.canvas.scan_mark(event.x, event.y)


def scroll_move(event):
    main_window.canvas.scan_dragto(event.x, event.y, gain=1)


def scroll_end(event):
    main_window.grid_drawer.draw_grid()


def scroll_wheel(event):
    main_window.grid_drawer.remove_grid()
    main_window.canvas.scan_mark(event.x, event.y)
    delta_y = 0
    if event.num == 5 or event.delta < 0:  # scroll down
        delta_y = -10
    elif event.num == 4 or event.delta >= 0:  # scroll up
        delta_y = +10
    main_window.canvas.scan_dragto(event.x, event.y + delta_y, gain=1)
    main_window.grid_drawer.draw_grid()


def modify_font_sizes_of_all_canvas_items(factor):
    global fontsize
    global label_fontsize
    global state_name_font
    fontsize *= factor
    label_fontsize *= factor
    used_label_fontsize = max(label_fontsize, 1)
    state_name_font.configure(size=int(fontsize))
    canvas_ids = main_window.canvas.find_all()
    for i in canvas_ids:
        if main_window.canvas.type(i) == "window":
            if i in state_action_handling.MyText.mytext_dict:
                state_action_handling.MyText.mytext_dict[i].label_id.configure(font=("Arial", int(used_label_fontsize)))
                state_action_handling.MyText.mytext_dict[i].text_id.configure(font=("Courier", int(fontsize)))
                for keyword in main_window.keywords:
                    state_action_handling.MyText.mytext_dict[i].text_id.tag_configure(
                        keyword, foreground=config.KEYWORD_COLORS[keyword], font=("Courier", int(fontsize), "normal")
                    )
            elif i in state_comment.StateComment.dictionary:
                state_comment.StateComment.dictionary[i].label_id.configure(font=("Arial", int(used_label_fontsize)))
                state_comment.StateComment.dictionary[i].text_id.configure(font=("Courier", int(fontsize)))
                for keyword in main_window.keywords:
                    state_comment.StateComment.dictionary[i].text_id.tag_configure(
                        keyword, foreground=config.KEYWORD_COLORS[keyword], font=("Courier", int(fontsize), "normal")
                    )
            elif i in condition_action_handling.ConditionAction.dictionary:
                condition_action_handling.ConditionAction.dictionary[i].condition_label.configure(
                    font=("Arial", int(used_label_fontsize))
                )
                condition_action_handling.ConditionAction.dictionary[i].action_label.configure(
                    font=("Arial", int(used_label_fontsize))
                )
                condition_action_handling.ConditionAction.dictionary[i].condition_id.configure(
                    font=("Courier", int(fontsize))
                )
                condition_action_handling.ConditionAction.dictionary[i].action_id.configure(
                    font=("Courier", int(fontsize))
                )
                for keyword in main_window.keywords:
                    condition_action_handling.ConditionAction.dictionary[i].condition_id.tag_configure(
                        keyword, foreground=config.KEYWORD_COLORS[keyword], font=("Courier", int(fontsize), "normal")
                    )
                    condition_action_handling.ConditionAction.dictionary[i].action_id.tag_configure(
                        keyword, foreground=config.KEYWORD_COLORS[keyword], font=("Courier", int(fontsize), "normal")
                    )
            elif i in global_actions.GlobalActions.dictionary:
                global_actions.GlobalActions.dictionary[i].label_before.configure(
                    font=("Arial", int(used_label_fontsize))
                )
                global_actions.GlobalActions.dictionary[i].label_after.configure(
                    font=("Arial", int(used_label_fontsize))
                )
                global_actions.GlobalActions.dictionary[i].text_before_id.configure(font=("Courier", int(fontsize)))
                global_actions.GlobalActions.dictionary[i].text_after_id.configure(font=("Courier", int(fontsize)))
                for keyword in main_window.keywords:
                    global_actions.GlobalActions.dictionary[i].text_before_id.tag_configure(
                        keyword, foreground=config.KEYWORD_COLORS[keyword], font=("Courier", int(fontsize), "normal")
                    )
                    global_actions.GlobalActions.dictionary[i].text_after_id.tag_configure(
                        keyword, foreground=config.KEYWORD_COLORS[keyword], font=("Courier", int(fontsize), "normal")
                    )
            elif i in global_actions_combinatorial.GlobalActionsCombinatorial.dictionary:
                global_actions_combinatorial.GlobalActionsCombinatorial.dictionary[i].label.configure(
                    font=("Arial", int(used_label_fontsize))
                )
                global_actions_combinatorial.GlobalActionsCombinatorial.dictionary[i].text_id.configure(
                    font=("Courier", int(fontsize))
                )
                for keyword in main_window.keywords:
                    global_actions_combinatorial.GlobalActionsCombinatorial.dictionary[i].text_id.tag_configure(
                        keyword, foreground=config.KEYWORD_COLORS[keyword], font=("Courier", int(fontsize), "normal")
                    )
            elif i in state_actions_default.StateActionsDefault.dictionary:
                state_actions_default.StateActionsDefault.dictionary[i].label.configure(
                    font=("Arial", int(used_label_fontsize))
                )
                state_actions_default.StateActionsDefault.dictionary[i].text_id.configure(
                    font=("Courier", int(fontsize))
                )
                for keyword in main_window.keywords:
                    state_actions_default.StateActionsDefault.dictionary[i].text_id.tag_configure(
                        keyword, foreground=config.KEYWORD_COLORS[keyword], font=("Courier", int(fontsize), "normal")
                    )
            else:
                print("canvas_editing: Fatal, unknown dictionary key ", i)


def get_visible_center_as_string():
    visible_rectangle = [
        main_window.canvas.canvasx(0),
        main_window.canvas.canvasy(0),
        main_window.canvas.canvasx(main_window.canvas.winfo_width()),
        main_window.canvas.canvasy(main_window.canvas.winfo_height()),
    ]
    visible_center = determine_center_of_rectangle(visible_rectangle)
    visible_center_string = ""
    for value in visible_center:
        visible_center_string += str(value) + " "
    return visible_center_string


def shift_visible_center_to_window_center(new_visible_center_string):
    new_visible_center = []
    new_visible_center_string_array = new_visible_center_string.split()
    for entry in new_visible_center_string_array:
        new_visible_center.append(float(entry))
    actual_visible_rectangle = [
        main_window.canvas.canvasx(0),
        main_window.canvas.canvasy(0),
        main_window.canvas.canvasx(main_window.canvas.winfo_width()),
        main_window.canvas.canvasy(main_window.canvas.winfo_height()),
    ]
    actual_visible_center = determine_center_of_rectangle(actual_visible_rectangle)
    move_canvas_point_from_to(new_visible_center, actual_visible_center)


def find(search_string, replace_string, replace):
    # search_in_canvas_text() uses <string>.find() and re.findall() and re.sub().
    # All other search-methods use text_widget.search() for find and replace.
    # In order to have identical behaviour, in search_in_canvas_text() the search_string and replace_string are "escaped".
    search_pattern = search_string.get()
    if search_pattern == "":
        messagebox.showinfo("HDL-FSM-Editor", "Search is aborted as you search for an empty string.")
        return
    replace_pattern = replace_string.get()
    number_of_hits_all = 0
    all_canvas_items = main_window.canvas.find_all()
    continue_search = True
    for item in all_canvas_items:
        if main_window.canvas.type(item) == "window":
            text_ids = get_text_ids_of_canvas_window(item)
            number_of_hits = search_in_text_fields_of_canvas_window(
                search_pattern, item, text_ids, replace, replace_pattern
            )
            if number_of_hits == -1:
                continue_search = False
            else:
                number_of_hits_all += number_of_hits
        elif main_window.canvas.type(item) == "text":
            number_of_hits = search_in_canvas_text(item, search_pattern, replace, replace_pattern)
            if number_of_hits == -1:
                continue_search = False
            else:
                number_of_hits_all += number_of_hits
        if continue_search is False:
            break
    if continue_search:
        interface_text_fields = [main_window.interface_generics_text]
        number_of_hits = search_in_text_fields_of_a_tab(
            "Interface", "Generics", search_pattern, interface_text_fields, replace, replace_pattern
        )
        if number_of_hits == -1:
            continue_search = False
        else:
            number_of_hits_all += number_of_hits
    if continue_search:
        if main_window.language.get() == "VHDL":
            interface_text_fields = [main_window.interface_ports_text, main_window.interface_package_text]
        else:
            interface_text_fields = [main_window.interface_ports_text]
        number_of_hits = search_in_text_fields_of_a_tab(
            "Interface", "Ports", search_pattern, interface_text_fields, replace, replace_pattern
        )
        if number_of_hits == -1:
            continue_search = False
        else:
            number_of_hits_all += number_of_hits
    if continue_search:
        if main_window.language.get() == "VHDL":
            internals_text_fields = [
                main_window.internals_package_text,
                main_window.internals_architecture_text,
                main_window.internals_process_clocked_text,
                main_window.internals_process_combinatorial_text,
            ]
        else:
            internals_text_fields = [
                main_window.internals_architecture_text,
                main_window.internals_process_clocked_text,
                main_window.internals_process_combinatorial_text,
            ]
        number_of_hits = search_in_text_fields_of_a_tab(
            "Internals", "", search_pattern, internals_text_fields, replace, replace_pattern
        )
        if number_of_hits == -1:
            continue_search = False
        else:
            number_of_hits_all += number_of_hits
    if continue_search:
        number_of_hits = search_in_text_fields_of_a_tab(
            "generated HDL", "", search_pattern, [main_window.hdl_frame_text], replace, replace_pattern
        )
        if number_of_hits == -1:
            continue_search = False
        else:
            number_of_hits_all += number_of_hits
    if continue_search:
        if replace:
            undo_handling.design_has_changed()
            messagebox.showinfo("HDL-FSM-Editor", "Number of replacements = " + str(number_of_hits_all))
        else:
            messagebox.showinfo("HDL-FSM-Editor", "Number of hits = " + str(number_of_hits_all))


def get_text_ids_of_canvas_window(item):
    text_ids = []
    if item in state_action_handling.MyText.mytext_dict:
        text_ids.append(state_action_handling.MyText.mytext_dict[item].text_id)
    elif item in condition_action_handling.ConditionAction.dictionary:
        text_ids.append(condition_action_handling.ConditionAction.dictionary[item].condition_id)
        text_ids.append(condition_action_handling.ConditionAction.dictionary[item].action_id)
    elif item in global_actions.GlobalActions.dictionary:
        text_ids.append(global_actions.GlobalActions.dictionary[item].text_before_id)
        text_ids.append(global_actions.GlobalActions.dictionary[item].text_after_id)
    elif item in global_actions_combinatorial.GlobalActionsCombinatorial.dictionary:
        text_ids.append(global_actions_combinatorial.GlobalActionsCombinatorial.dictionary[item].text_id)
    elif item in state_actions_default.StateActionsDefault.dictionary:
        text_ids.append(state_actions_default.StateActionsDefault.dictionary[item].text_id)
    elif item in state_comment.StateComment.dictionary:
        text_ids.append(state_comment.StateComment.dictionary[item].text_id)
    return text_ids


def search_in_text_fields_of_canvas_window(
    search_pattern, canvas_window, text_ids_of_actions, replace, replace_pattern
):
    number_of_hits_all = 0
    count = tk.IntVar()
    for text_id in text_ids_of_actions:
        number_of_hits = search_in_text_widget(text_id, search_pattern, count, canvas_window, replace, replace_pattern)
        if number_of_hits == -1:
            number_of_hits_all = -1
            break
        number_of_hits_all += number_of_hits
    return number_of_hits_all


def search_in_text_widget(text_id, search_pattern, count, canvas_window, replace, replace_pattern):
    start = "1.0"
    number_of_hits = 0
    while True:
        index = text_id.search(
            search_pattern, start, tk.END, count=count, regexp=True, nocase=1
        )  # index = "line.column"
        if index == "" or count.get() == 0:
            break
        number_of_hits += 1
        if replace:
            end_index = index + "+" + str(len(search_pattern)) + " chars"
            text_id.delete(index, end_index)
            text_id.insert(index, replace_pattern)
            text_id.format_after_idle()
            start = index + "+" + str(len(replace_pattern)) + " chars"
        else:
            move_in_foreground("Diagram")
            text_id.tag_add("hit", index, index + " + " + str(count.get()) + " chars")
            text_id.tag_configure("hit", background="blue")
            object_coords = main_window.canvas.bbox(canvas_window)
            view_rectangle(object_coords, check_fit=False)
            continue_search = messagebox.askyesno("Continue", "Find next")
            text_id.tag_remove("hit", index, index + " + " + str(count.get()) + " chars")
            if continue_search is False:
                number_of_hits = -1
                break
            start = index + " + " + str(count.get()) + " chars"
        if start == index:
            messagebox.showinfo(
                "HDL-FSM-Editor", "Search in text widgets is aborted as for unknown reason no progress happens."
            )
            break
    return number_of_hits


def search_in_canvas_text(item, search_pattern, replace, replace_pattern):
    text = main_window.canvas.itemcget(item, "text")
    start = 0
    number_of_hits = 0
    while True:
        hit_begin = text.find(search_pattern, start, len(text))
        if hit_begin == -1:
            break
        if replace:
            search_pattern = re.escape(search_pattern)
            replace_pattern = re.escape(replace_pattern)
            number_of_hits = len(re.findall(search_pattern, text, flags=re.IGNORECASE))
            text = re.sub(search_pattern, replace_pattern, text, flags=re.IGNORECASE)
            main_window.canvas.itemconfigure(item, text=text)
            start = len(text)  # The search-pattern cannot be found again in the next loop.
        else:
            number_of_hits += 1
            move_in_foreground("Diagram")
            main_window.canvas.select_from(item, hit_begin)
            main_window.canvas.select_to(item, hit_begin + len(search_pattern) - 1)
            object_coords = main_window.canvas.bbox(item)
            view_rectangle(object_coords, check_fit=False)
            object_center = main_window.canvas.coords(item)
            canvas_zoom(object_center, 0.25)
            continue_search = messagebox.askyesno("Continue", "Find next")
            if continue_search is False:
                number_of_hits = -1
                break
            start = hit_begin + len(search_pattern)
        if start == hit_begin:
            messagebox.showinfo(
                "HDL-FSM-Editor", "Search in canvas text is aborted as for unknown reason no progress happens."
            )
            break
    return number_of_hits


def search_in_text_fields_of_a_tab(tab, kind, search_pattern, interface_text_fields, replace, replace_pattern):
    count = tk.IntVar()
    number_of_hits = 0
    for text_id in interface_text_fields:
        start = "1.0"
        while True:
            index = text_id.search(
                search_pattern, start, tk.END, count=count, regexp=True, nocase=1
            )  # index = "line.column"
            if index == "" or count.get() == 0:
                break
            number_of_hits += 1
            if replace:
                end_index = index + "+" + str(len(search_pattern)) + " chars"
                text_id.delete(index, end_index)
                text_id.insert(index, replace_pattern)
                if tab == "Interface":
                    if kind == "Generics":
                        text_id.update_custom_text_class_generics_list()
                    else:  # kind=="ports"
                        text_id.update_custom_text_class_ports_list()
                elif tab == "Internals":
                    text_id.update_custom_text_class_signals_list()
                else:  # tab="generated HDL"
                    pass
                start = index + "+" + str(len(replace_pattern)) + " chars"
                if text_id.cget("state") == tk.DISABLED:
                    number_of_hits -= 1
            else:
                move_in_foreground(tab)
                text_id.tag_add("hit", index, index + " + " + str(count.get()) + " chars")
                text_id.tag_configure("hit", background="blue")
                text_id.see(index)
                answer = messagebox.askyesno("Continue", "Find next")
                text_id.tag_remove("hit", index, index + " + " + str(count.get()) + " chars")
                if answer is False:
                    return -1
                start = index + " + " + str(count.get()) + " chars"
            if start == index:
                messagebox.showinfo(
                    "HDL-FSM-Editor", "Search in tab text fields is aborted as for unknown reason no progress happens."
                )
                break
    return number_of_hits


def move_in_foreground(tab):
    notebook_ids = main_window.notebook.tabs()
    for notebook_id in notebook_ids:
        if main_window.notebook.tab(notebook_id, option="text") == tab:
            main_window.notebook.select(notebook_id)


def __show_menu(zoom_coords):
    canvas_menue_entries_list_with_hide = ["Change background color", "Hide grid"]
    canvas_menue_entries_list_with_show = ["Change background color", "Show grid"]
    if main_window.show_grid is True:
        canvas_menue_entries_list = canvas_menue_entries_list_with_hide
    else:
        canvas_menue_entries_list = canvas_menue_entries_list_with_show
    menu = OptionMenu(
        main_window.canvas,
        canvas_menue_entries_list,
        height=2,
        bg="lightgrey",
        width=25,
        activestyle="dotbox",
        relief=tk.RAISED,
    )
    menue_window = main_window.canvas.create_window(zoom_coords[0], zoom_coords[1], window=menu)
    menu.bind("<Button-1>", lambda event: __evaluate_menu(menue_window, menu))
    menu.bind("<Leave>", lambda event: __close_menu(menue_window, menu))


def __evaluate_menu(menue_window, menu):
    selected_entry = menu.get(menu.curselection()[0])
    if "Change background color" in selected_entry:
        main_window.choose_bg_color()
    elif "Hide grid" in selected_entry:
        main_window.show_grid = False
        main_window.grid_drawer.remove_grid()
    elif "Show grid" in selected_entry:
        main_window.show_grid = True
        main_window.grid_drawer.draw_grid()
    __close_menu(menue_window, menu)


def __close_menu(menue_window, menu):
    menu.destroy()
    main_window.canvas.delete(menue_window)
