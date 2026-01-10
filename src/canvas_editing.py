"""
This module contains method used when the user edits the diagram.
"""

import tkinter as tk
from tkinter import font, messagebox

import canvas_modify_bindings
import condition_action_handling
import constants
import global_actions
import global_actions_combinatorial
import move_handling_initialization
import state_action_handling
import state_actions_default
import state_comment
from project_manager import project_manager
from widgets.OptionMenu import OptionMenu

# import inspect


def create_font_for_state_names() -> None:  # Called once by create_diagram_notebook_tab().
    project_manager.state_name_font = font.Font(font="TkDefaultFont")
    project_manager.state_name_font.configure(size=int(project_manager.fontsize))


def translate_window_event_coordinates_in_rounded_canvas_coordinates(event) -> list:
    canvas_grid_x_coordinate = project_manager.canvas.canvasx(event.x, gridspacing=project_manager.state_radius)
    canvas_grid_y_coordinate = project_manager.canvas.canvasy(event.y, gridspacing=project_manager.state_radius)
    return [canvas_grid_x_coordinate, canvas_grid_y_coordinate]


def translate_window_event_coordinates_in_exact_canvas_coordinates(event) -> list:
    canvas_grid_x_coordinate, canvas_grid_y_coordinate = (
        project_manager.canvas.canvasx(event.x),
        project_manager.canvas.canvasy(event.y),
    )
    return [canvas_grid_x_coordinate, canvas_grid_y_coordinate]


def adapt_visibility_of_priority_rectangles_at_state(start_state) -> None:
    tags_of_start_state = project_manager.canvas.gettags(start_state)
    number_of_outgoing_transitions = 0
    tag_of_outgoing_transition = ""
    for start_state_tag in tags_of_start_state:
        if start_state_tag.startswith("transition") and start_state_tag.endswith("_start"):
            number_of_outgoing_transitions += 1
            tag_of_outgoing_transition = start_state_tag.replace("_start", "")
    if number_of_outgoing_transitions == 1:
        project_manager.canvas.itemconfigure(tag_of_outgoing_transition + "rectangle", state=tk.HIDDEN)
        project_manager.canvas.itemconfigure(tag_of_outgoing_transition + "priority", state=tk.HIDDEN)


def start_view_rectangle(event) -> None:
    [event_x, event_y] = translate_window_event_coordinates_in_exact_canvas_coordinates(event)
    rectangle_id = project_manager.canvas.create_rectangle(event_x, event_y, event_x, event_y, dash=(3, 5))
    project_manager.canvas.tag_raise(rectangle_id, "all")
    funcid_canvas_draw_view_rectangle = project_manager.canvas.bind(
        "<Motion>", lambda event: _draw_view_rectangle(event, rectangle_id), "+"
    )
    project_manager.canvas.bind(
        "<ButtonRelease-1>",
        lambda event: _view_area_after_button1_release(rectangle_id, funcid_canvas_draw_view_rectangle),
    )
    project_manager.canvas.bind(
        "<ButtonRelease-3>",
        lambda event: _view_area_after_button3_release(rectangle_id, funcid_canvas_draw_view_rectangle),
    )


def _draw_view_rectangle(event, rectangle_id) -> None:  # Called by Motion-event.
    [event_x, event_y] = translate_window_event_coordinates_in_exact_canvas_coordinates(event)
    rectangle_coords = project_manager.canvas.coords(rectangle_id)
    if event_x > rectangle_coords[0] and event_y > rectangle_coords[1]:
        project_manager.canvas.coords(rectangle_id, rectangle_coords[0], rectangle_coords[1], event_x, event_y)


def _view_area_after_button3_release(rectangle_id, funcid_canvas_draw_view_rectangle) -> None:
    rectangle_coords = project_manager.canvas.coords(rectangle_id)
    if rectangle_coords[0] != rectangle_coords[2] and rectangle_coords[1] != rectangle_coords[3]:
        _view_area_after_button1_release(rectangle_id, funcid_canvas_draw_view_rectangle)
    else:
        project_manager.canvas.delete(rectangle_id)
        overlapping_canvas_ids = project_manager.canvas.find_overlapping(
            rectangle_coords[0] - 5, rectangle_coords[1] - 5, rectangle_coords[0] + 5, rectangle_coords[1] + 5
        )
        item_found = False
        for canvas_id in overlapping_canvas_ids:
            tags = project_manager.canvas.gettags(canvas_id)
            if "grid_line" not in tags:
                item_found = True
        if not item_found:
            _show_canvas_background_menu(rectangle_coords)
        _restore_binding(funcid_canvas_draw_view_rectangle)


def _restore_binding(funcid_canvas_draw_view_rectangle):
    project_manager.canvas.unbind("<Motion>", funcid_canvas_draw_view_rectangle)
    project_manager.canvas.unbind("<ButtonRelease-1>")
    project_manager.canvas.unbind("<ButtonRelease-3>")
    # Restore the original binding (Button-1 is bound to start_view_rectangle(), when "view area"-Button was used):
    project_manager.canvas.bind("<Button-1>", move_handling_initialization.move_initialization)


def _view_area_after_button1_release(
    rectangle_id, funcid_canvas_draw_view_rectangle
) -> None:  # Called by Button-1("view area"-button) or Button-3(view area per right mouse-button)-Release-Event.
    project_manager.grid_drawer.remove_grid()
    complete_rectangle = project_manager.canvas.coords(rectangle_id)
    view_rectangle(complete_rectangle, check_fit=False)
    project_manager.canvas.delete(rectangle_id)
    _restore_binding(funcid_canvas_draw_view_rectangle)
    project_manager.grid_drawer.draw_grid()


def view_all() -> None:
    project_manager.grid_drawer.remove_grid()
    complete_rectangle = project_manager.canvas.bbox("all")
    if complete_rectangle is not None:
        view_rectangle(complete_rectangle, check_fit=True)
    project_manager.canvas.update_idletasks()  # helps to get "after_idle" in view_rectangle() ready?!
    project_manager.canvas.after_idle(
        project_manager.grid_drawer.draw_grid
    )  # "after_idle" is needed because view_rectangle calls decrement_font_size_if_window_is_too_wide after idle.


def view_rectangle(complete_rectangle, check_fit) -> None:
    if complete_rectangle[2] - complete_rectangle[0] != 0 and complete_rectangle[3] - complete_rectangle[1] != 0:
        visible_rectangle = [
            project_manager.canvas.canvasx(0),
            project_manager.canvas.canvasy(0),
            project_manager.canvas.canvasx(project_manager.canvas.winfo_width()),
            project_manager.canvas.canvasy(project_manager.canvas.winfo_height()),
        ]
        factor = _calculate_zoom_factor(complete_rectangle, visible_rectangle)
        too_big = False
        actual_rectangle = project_manager.canvas.bbox("all")
        for coord in actual_rectangle:
            # The Canvas which is used, has a scrollregion +/-100000, so here this limit
            # is checked (unclear if really necessary):
            if abs(coord) * factor > 100000:
                too_big = True
        if too_big is False:
            complete_center = _determine_center_of_rectangle(complete_rectangle)
            visible_center = _determine_center_of_rectangle(visible_rectangle)
            _move_canvas_point_from_to(complete_center, visible_center)
            canvas_zoom(complete_center, factor)
            if check_fit:
                project_manager.canvas.after_idle(_decrement_font_size_if_window_is_too_wide)
        else:
            messagebox.showerror("Fatal", "Zoom factor is too big.")
    canvas_modify_bindings.switch_to_move_mode()


def _decrement_font_size_if_window_is_too_wide() -> None:
    visible_rectangle = [
        project_manager.canvas.canvasx(0),
        project_manager.canvas.canvasy(0),
        project_manager.canvas.canvasx(project_manager.canvas.winfo_width()),
        project_manager.canvas.canvasy(project_manager.canvas.winfo_height()),
    ]
    complete_rectangle = project_manager.canvas.bbox("all")
    if (
        (
            complete_rectangle[0] < visible_rectangle[0]
            or complete_rectangle[1] < visible_rectangle[1]
            or complete_rectangle[2] > visible_rectangle[2]
            or complete_rectangle[3] > visible_rectangle[3]
        )
        and project_manager.fontsize != 1  # When fontsize==1 then zoom_factor calculates to 0, which makes no sense.
    ):
        complete_center = _determine_center_of_rectangle(complete_rectangle)
        visible_center = _determine_center_of_rectangle(visible_rectangle)
        _move_canvas_point_from_to(complete_center, visible_center)
        zoom_factor = (project_manager.fontsize - 1) / project_manager.fontsize
        canvas_zoom(complete_center, zoom_factor)
        project_manager.canvas.after_idle(_decrement_font_size_if_window_is_too_wide)


def _determine_center_of_rectangle(rectangle_coords) -> list:
    return [(rectangle_coords[0] + rectangle_coords[2]) / 2, (rectangle_coords[1] + rectangle_coords[3]) / 2]


def _move_canvas_point_from_to(complete_center, visible_center) -> None:
    project_manager.canvas.scan_mark(int(complete_center[0]), int(complete_center[1]))
    project_manager.canvas.scan_dragto(int(visible_center[0]), int(visible_center[1]), gain=1)


def _calculate_zoom_factor(complete_rectangle, visible_rectangle):
    complete_width = complete_rectangle[2] - complete_rectangle[0]
    complete_height = complete_rectangle[3] - complete_rectangle[1]
    visible_width = visible_rectangle[2] - visible_rectangle[0]
    visible_height = visible_rectangle[3] - visible_rectangle[1]
    scale_x = visible_width / complete_width
    scale_y = visible_height / complete_height
    factor = min(scale_x, scale_y)
    return factor


def zoom_wheel(event) -> None:
    project_manager.canvas.grid_remove()  # Make the grid invisible, but remember all options for the the next grid() call.
    project_manager.grid_drawer.remove_grid()
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
    project_manager.grid_drawer.draw_grid()
    canvas_modify_bindings.switch_to_move_mode()
    project_manager.canvas.grid()


def zoom_plus() -> None:
    project_manager.canvas.grid_remove()  # Make the canvas invisible.
    project_manager.grid_drawer.remove_grid()
    factor = 1.1
    visible_rectangle = [
        project_manager.canvas.canvasx(0),
        project_manager.canvas.canvasy(0),
        project_manager.canvas.canvasx(project_manager.canvas.winfo_width()),
        project_manager.canvas.canvasy(project_manager.canvas.winfo_height()),
    ]
    visible_center = _determine_center_of_rectangle(visible_rectangle)
    canvas_zoom(visible_center, factor)
    project_manager.grid_drawer.draw_grid()
    project_manager.canvas.grid()


def zoom_minus() -> None:
    project_manager.canvas.grid_remove()  # Make the canvas invisible.
    project_manager.grid_drawer.remove_grid()
    factor = 1 / 1.1
    visible_rectangle = [
        project_manager.canvas.canvasx(0),
        project_manager.canvas.canvasy(0),
        project_manager.canvas.canvasx(project_manager.canvas.winfo_width()),
        project_manager.canvas.canvasy(project_manager.canvas.winfo_height()),
    ]
    visible_center = _determine_center_of_rectangle(visible_rectangle)
    canvas_zoom(visible_center, factor)
    project_manager.grid_drawer.draw_grid()
    project_manager.canvas.grid()


def canvas_zoom(zoom_center, zoom_factor) -> None:
    # Modify factor, so that fontsize is always an integer:
    fontsize_rounded_down = int(project_manager.fontsize * zoom_factor)
    if zoom_factor > 1 and fontsize_rounded_down == project_manager.fontsize:
        fontsize_rounded_down += 1
    if fontsize_rounded_down != 0:
        zoom_factor = fontsize_rounded_down / project_manager.fontsize
        project_manager.canvas.scale(
            "all", 0, 0, zoom_factor, zoom_factor
        )  # Scaling must use xoffset=0 and yoffset=0 to preserve the gridspacing of state_radius.
        _scroll_canvas_to_show_the_zoom_center(zoom_center, zoom_factor)
        _adapt_scroll_bars(zoom_factor)
        _adapt_global_size_variables(zoom_factor)


def _scroll_canvas_to_show_the_zoom_center(zoom_center, zoom_factor) -> None:
    new_position_of_zoom_center = [coord * zoom_factor for coord in zoom_center]
    project_manager.canvas.scan_mark(
        int(new_position_of_zoom_center[0]), int(new_position_of_zoom_center[1])
    )  # Mark the point of the canvas, which serves as anchor for the shift.
    project_manager.canvas.scan_dragto(int(zoom_center[0]), int(zoom_center[1]), gain=1)


def _adapt_scroll_bars(factor) -> None:
    scrollregion_strings = project_manager.canvas.cget("scrollregion").split()
    scrollregion_scaled = [int(float(x) * factor) for x in scrollregion_strings]
    project_manager.canvas.configure(scrollregion=scrollregion_scaled)


def _adapt_global_size_variables(factor) -> None:
    project_manager.state_radius = factor * project_manager.state_radius  # publish new state radius
    project_manager.priority_distance = factor * project_manager.priority_distance
    project_manager.reset_entry_size = factor * project_manager.reset_entry_size
    _modify_font_sizes_of_all_canvas_items(factor)


def scroll_start(event) -> None:
    project_manager.grid_drawer.remove_grid()
    project_manager.canvas.scan_mark(event.x, event.y)


def scroll_move(event) -> None:
    project_manager.canvas.scan_dragto(event.x, event.y, gain=1)


def scroll_end(event) -> None:
    project_manager.grid_drawer.draw_grid()


def scroll_wheel(event) -> None:
    project_manager.grid_drawer.remove_grid()
    project_manager.canvas.scan_mark(event.x, event.y)
    delta_y = 0
    if event.num == 5 or event.delta < 0:  # scroll down
        delta_y = -10
    elif event.num == 4 or event.delta >= 0:  # scroll up
        delta_y = +10
    project_manager.canvas.scan_dragto(event.x, event.y + delta_y, gain=1)
    project_manager.grid_drawer.draw_grid()


def _modify_font_sizes_of_all_canvas_items(factor) -> None:
    project_manager.fontsize *= factor
    project_manager.label_fontsize *= factor
    used_label_fontsize = max(project_manager.label_fontsize, 1)
    project_manager.state_name_font.configure(size=int(project_manager.fontsize))
    canvas_ids = project_manager.canvas.find_all()
    for i in canvas_ids:
        if project_manager.canvas.type(i) == "window":
            if i in state_action_handling.MyText.mytext_dict:
                state_action_handling.MyText.mytext_dict[i].label_id.configure(font=("Arial", int(used_label_fontsize)))
                state_action_handling.MyText.mytext_dict[i].text_id.configure(
                    font=("Courier", int(project_manager.fontsize))
                )
                for highlight_tag_name in constants.VHDL_HIGHLIGHT_PATTERN_DICT:
                    state_action_handling.MyText.mytext_dict[i].text_id.tag_configure(
                        highlight_tag_name,
                        font=("Courier", int(project_manager.fontsize), "normal"),
                    )
            elif i in state_comment.StateComment.dictionary:
                state_comment.StateComment.dictionary[i].label_id.configure(font=("Arial", int(used_label_fontsize)))
                state_comment.StateComment.dictionary[i].text_id.configure(
                    font=("Courier", int(project_manager.fontsize))
                )
                for highlight_tag_name in constants.VHDL_HIGHLIGHT_PATTERN_DICT:
                    state_comment.StateComment.dictionary[i].text_id.tag_configure(
                        highlight_tag_name,
                        font=("Courier", int(project_manager.fontsize), "normal"),
                    )
            elif i in condition_action_handling.ConditionAction.dictionary:
                condition_action_handling.ConditionAction.dictionary[i].condition_label.configure(
                    font=("Arial", int(used_label_fontsize))
                )
                condition_action_handling.ConditionAction.dictionary[i].action_label.configure(
                    font=("Arial", int(used_label_fontsize))
                )
                condition_action_handling.ConditionAction.dictionary[i].condition_id.configure(
                    font=("Courier", int(project_manager.fontsize))
                )
                condition_action_handling.ConditionAction.dictionary[i].action_id.configure(
                    font=("Courier", int(project_manager.fontsize))
                )
                for highlight_tag_name in constants.VHDL_HIGHLIGHT_PATTERN_DICT:
                    condition_action_handling.ConditionAction.dictionary[i].condition_id.tag_configure(
                        highlight_tag_name,
                        font=("Courier", int(project_manager.fontsize), "normal"),
                    )
                    condition_action_handling.ConditionAction.dictionary[i].action_id.tag_configure(
                        highlight_tag_name,
                        font=("Courier", int(project_manager.fontsize), "normal"),
                    )
            elif i in global_actions.GlobalActions.dictionary:
                global_actions.GlobalActions.dictionary[i].label_before.configure(
                    font=("Arial", int(used_label_fontsize))
                )
                global_actions.GlobalActions.dictionary[i].label_after.configure(
                    font=("Arial", int(used_label_fontsize))
                )
                global_actions.GlobalActions.dictionary[i].text_before_id.configure(
                    font=("Courier", int(project_manager.fontsize))
                )
                global_actions.GlobalActions.dictionary[i].text_after_id.configure(
                    font=("Courier", int(project_manager.fontsize))
                )
                for highlight_tag_name in constants.VHDL_HIGHLIGHT_PATTERN_DICT:
                    global_actions.GlobalActions.dictionary[i].text_before_id.tag_configure(
                        highlight_tag_name,
                        font=("Courier", int(project_manager.fontsize), "normal"),
                    )
                    global_actions.GlobalActions.dictionary[i].text_after_id.tag_configure(
                        highlight_tag_name,
                        font=("Courier", int(project_manager.fontsize), "normal"),
                    )
            elif i in global_actions_combinatorial.GlobalActionsCombinatorial.dictionary:
                global_actions_combinatorial.GlobalActionsCombinatorial.dictionary[i].label.configure(
                    font=("Arial", int(used_label_fontsize))
                )
                global_actions_combinatorial.GlobalActionsCombinatorial.dictionary[i].text_id.configure(
                    font=("Courier", int(project_manager.fontsize))
                )
                for highlight_tag_name in constants.VHDL_HIGHLIGHT_PATTERN_DICT:
                    global_actions_combinatorial.GlobalActionsCombinatorial.dictionary[i].text_id.tag_configure(
                        highlight_tag_name,
                        font=("Courier", int(project_manager.fontsize), "normal"),
                    )
            elif i in state_actions_default.StateActionsDefault.dictionary:
                state_actions_default.StateActionsDefault.dictionary[i].label.configure(
                    font=("Arial", int(used_label_fontsize))
                )
                state_actions_default.StateActionsDefault.dictionary[i].text_id.configure(
                    font=("Courier", int(project_manager.fontsize))
                )
                for highlight_tag_name in constants.VHDL_HIGHLIGHT_PATTERN_DICT:
                    state_actions_default.StateActionsDefault.dictionary[i].text_id.tag_configure(
                        highlight_tag_name,
                        font=("Courier", int(project_manager.fontsize), "normal"),
                    )
            else:
                print("canvas_editing: Fatal, unknown dictionary key ", i)


def get_visible_center_as_string() -> str:
    visible_rectangle = [
        project_manager.canvas.canvasx(0),
        project_manager.canvas.canvasy(0),
        project_manager.canvas.canvasx(project_manager.canvas.winfo_width()),
        project_manager.canvas.canvasy(project_manager.canvas.winfo_height()),
    ]
    visible_center = _determine_center_of_rectangle(visible_rectangle)
    visible_center_string = ""
    for value in visible_center:
        visible_center_string += str(value) + " "
    return visible_center_string


def shift_visible_center_to_window_center(new_visible_center_string) -> None:
    new_visible_center = []
    new_visible_center_string_array = new_visible_center_string.split()
    for entry in new_visible_center_string_array:
        new_visible_center.append(float(entry))
    actual_visible_rectangle = [
        project_manager.canvas.canvasx(0),
        project_manager.canvas.canvasy(0),
        project_manager.canvas.canvasx(project_manager.canvas.winfo_width()),
        project_manager.canvas.canvasy(project_manager.canvas.winfo_height()),
    ]
    actual_visible_center = _determine_center_of_rectangle(actual_visible_rectangle)
    _move_canvas_point_from_to(new_visible_center, actual_visible_center)


def _show_canvas_background_menu(zoom_coords) -> None:
    canvas_menue_entries_list_with_hide = ["Change background color", "Hide grid"]
    canvas_menue_entries_list_with_show = ["Change background color", "Show grid"]
    if project_manager.grid_drawer.show_grid is True:
        canvas_menue_entries_list = canvas_menue_entries_list_with_hide
    else:
        canvas_menue_entries_list = canvas_menue_entries_list_with_show
    menu = OptionMenu(
        project_manager.canvas,
        canvas_menue_entries_list,
        height=2,
        bg="lightgrey",
        width=25,
        activestyle="dotbox",
        relief=tk.RAISED,
    )
    menue_window = project_manager.canvas.create_window(zoom_coords[0], zoom_coords[1], window=menu)
    menu.bind("<Button-1>", lambda event: __evaluate_menu(menue_window, menu))
    menu.bind("<Leave>", lambda event: __close_menu(menue_window, menu))


def __evaluate_menu(menue_window, menu) -> None:
    selected_entry = menu.get(menu.curselection()[0])
    if "Change background color" in selected_entry:
        project_manager.tab_control_ref.choose_bg_color()
    elif "Hide grid" in selected_entry:
        project_manager.grid_drawer.show_grid = False
        project_manager.grid_drawer.remove_grid()
    elif "Show grid" in selected_entry:
        project_manager.grid_drawer.show_grid = True
        project_manager.grid_drawer.draw_grid()
    __close_menu(menue_window, menu)


def __close_menu(menue_window, menu) -> None:
    menu.destroy()
    project_manager.canvas.delete(menue_window)
