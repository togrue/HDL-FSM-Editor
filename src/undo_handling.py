"""
This module contains all method to support "undo" and "redo".
"""

import os
import re
import tkinter as tk

import canvas_editing
import condition_action_handling
import connector_handling
import constants
import file_handling
import global_actions
import global_actions_combinatorial
import global_actions_handling
import main_window
import reset_entry_handling
import state_action_handling
import state_actions_default
import state_comment
import state_handling
import transition_handling
from project_manager import project_manager

stack: list[str] = []
stack_write_pointer: int = 0


def update_window_title() -> None:
    title = main_window.root.title()
    if title == "tk":
        main_window.root.title("unnamed")
    elif not title.endswith("*"):
        title += "*"
        main_window.root.title(title)


def design_has_changed() -> None:
    _add_changes_to_design_stack()
    update_window_title()
    if project_manager.current_file != "" and not main_window.root.title().startswith("unnamed"):
        # print("design_has_changed: tmp is created by =", inspect.stack()[1][3])
        file_handling.save_in_file_new(project_manager.current_file + ".tmp")


def undo() -> None:
    global stack_write_pointer
    # As <Control-z> is bound with the bind_all-command to the diagram, this binding must be ignored, when
    # the focus is on a customtext-widget: Then a Control-z must change the text and must not change the diagram.
    focus = str(main_window.canvas.focus_get())
    if "customtext" not in focus and stack_write_pointer > 1:
        # stack_write_pointer points at an empty place in stack.
        # stack_write_pointer-1 points at the version which contains the last change
        # stack_write_pointer-2 points at the version before the last change:
        stack_write_pointer -= 2
        _set_diagram_to_version_selected_by_stack_pointer()
        stack_write_pointer += 1
        if stack_write_pointer == 1:
            title = main_window.root.title()
            if title.endswith("*"):
                main_window.root.title(title[:-1])
        if (
            stack_write_pointer == 1
        ):  # 1 is the next free place in the stack, 0 is the empty design, so nothing to undo is left
            main_window.undo_button.config(state="disabled")
            if os.path.isfile(project_manager.current_file + ".tmp"):
                os.remove(project_manager.current_file + ".tmp")
        main_window.redo_button.config(state="enabled")


def redo() -> None:
    global stack_write_pointer
    # As <Control-Z> is bound with the bind_all-command to the diagram, this binding must be ignored, when
    # the focus is on the customtext-widget: Then a Control-Z must change the text and must not change the diagram.
    focus = str(main_window.canvas.focus_get())
    if "customtext" not in focus and stack_write_pointer < len(stack):
        _set_diagram_to_version_selected_by_stack_pointer()
        stack_write_pointer += 1
        main_window.undo_button.config(state="enabled")
    if stack_write_pointer == len(stack):
        main_window.redo_button.config(state="disabled")


def _add_changes_to_design_stack() -> None:
    global stack_write_pointer
    _remove_stack_entries_from_write_pointer_to_the_end_of_the_stack()
    new_design = _get_complete_design_as_text_object()
    stack.append(new_design)
    stack_write_pointer += 1
    if stack_write_pointer > 1:
        main_window.undo_button.config(state="enabled")
    main_window.redo_button.config(state="disabled")


def _remove_stack_entries_from_write_pointer_to_the_end_of_the_stack() -> None:
    if len(stack) > stack_write_pointer:
        del stack[stack_write_pointer:]


# TODO: This should be the same as saving to a file.
# Maybe including some extra information as the zoom level.
def _get_complete_design_as_text_object() -> str:
    design = ""
    design += "modulename|" + main_window.module_name.get() + "\n"
    design += "language|" + main_window.language.get() + "\n"
    design += "generate_path|" + main_window.generate_path_value.get() + "\n"
    design += "additional_sources|" + main_window.additional_sources_value.get() + "\n"
    design += "working_directory|" + main_window.working_directory_value.get() + "\n"
    design += "number_of_files|" + str(main_window.select_file_number_text.get()) + "\n"
    design += "reset_signal_name|" + main_window.reset_signal_name.get() + "\n"
    design += "clock_signal_name|" + main_window.clock_signal_name.get() + "\n"
    design += "state_number|" + str(state_handling.state_number) + "\n"
    design += "transition_number|" + str(transition_handling.transition_number) + "\n"
    design += "connector_number|" + str(connector_handling.connector_number) + "\n"
    design += "reset_entry_number|" + str(reset_entry_handling.reset_entry_number) + "\n"
    design += "conditionaction_id|" + str(condition_action_handling.ConditionAction.conditionaction_id) + "\n"
    design += "mytext_id|" + str(state_action_handling.MyText.mytext_id) + "\n"
    design += "state_actions_default_number|" + str(global_actions_handling.state_actions_default_number) + "\n"
    design += "global_actions_number|" + str(global_actions_handling.global_actions_clocked_number) + "\n"
    design += (
        "global_actions_combinatorial_number|" + str(global_actions_handling.global_actions_combinatorial_number) + "\n"
    )
    design += "reset_entry_size|" + str(canvas_editing.reset_entry_size) + "\n"
    design += "state_radius|" + str(canvas_editing.state_radius) + "\n"
    design += "priority_distance|" + str(canvas_editing.priority_distance) + "\n"
    design += "fontsize|" + str(canvas_editing.fontsize) + "\n"
    design += "label_fontsize|" + str(canvas_editing.label_fontsize) + "\n"
    design += "visible_center|" + canvas_editing.get_visible_center_as_string() + "\n"
    design += "include_timestamp_in_output|" + str(main_window.include_timestamp_in_output.get()) + "\n"
    design += (
        "interface_package|"
        + str(len(main_window.interface_package_text.get("1.0", tk.END)) - 1)
        + "|"
        + main_window.interface_package_text.get("1.0", tk.END)
    )
    design += (
        "interface_generics|"
        + str(len(main_window.interface_generics_text.get("1.0", tk.END)) - 1)
        + "|"
        + main_window.interface_generics_text.get("1.0", tk.END)
    )
    design += (
        "interface_ports|"
        + str(len(main_window.interface_ports_text.get("1.0", tk.END)) - 1)
        + "|"
        + main_window.interface_ports_text.get("1.0", tk.END)
    )
    design += (
        "internals_package|"
        + str(len(main_window.internals_package_text.get("1.0", tk.END)) - 1)
        + "|"
        + main_window.internals_package_text.get("1.0", tk.END)
    )
    design += (
        "internals_architecture|"
        + str(len(main_window.internals_architecture_text.get("1.0", tk.END)) - 1)
        + "|"
        + main_window.internals_architecture_text.get("1.0", tk.END)
    )
    design += (
        "internals_process|"
        + str(len(main_window.internals_process_clocked_text.get("1.0", tk.END)) - 1)
        + "|"
        + main_window.internals_process_clocked_text.get("1.0", tk.END)
    )
    design += (
        "internals_process_combinatorial|"
        + str(len(main_window.internals_process_combinatorial_text.get("1.0", tk.END)) - 1)
        + "|"
        + main_window.internals_process_combinatorial_text.get("1.0", tk.END)
    )
    items = main_window.canvas.find_all()
    print_tags = False
    for i in items:
        if main_window.canvas.type(i) == "oval":
            design += "state|"
            design += _get_coords(i)
            design += _get_tags(i)
            design += _get_fill_color(i)
            design += "\n"
        elif main_window.canvas.type(i) == "text":
            design += "text|"
            design += _get_coords(i)
            design += main_window.canvas.itemcget(i, "text") + " "
            design += _get_tags(i)
            design += "\n"
        elif main_window.canvas.type(i) == "line" and "grid_line" not in main_window.canvas.gettags(i):
            design += "line|"
            design += _get_coords(i)
            design += _get_tags(i)
            design += "\n"
        elif main_window.canvas.type(i) == "polygon":
            design += "polygon|"
            design += _get_coords(i)
            design += _get_tags(i)
            design += "\n"
        elif main_window.canvas.type(i) == "rectangle":
            design += "rectangle|"
            design += _get_coords(i)
            design += _get_tags(i)
            design += "\n"
        elif main_window.canvas.type(i) == "window":
            if i in state_action_handling.MyText.mytext_dict:
                design += "window_state_action_block|"
                text = state_action_handling.MyText.mytext_dict[i].text_id.get("1.0", tk.END)
                design += str(len(text)) + "|"
                design += text
                design += _get_coords(i)
            elif i in state_comment.StateComment.dictionary:
                design += "window_state_comment|"
                text = state_comment.StateComment.dictionary[i].text_id.get("1.0", tk.END)
                design += str(len(text)) + "|"
                design += text
                design += _get_coords(i)
            elif i in condition_action_handling.ConditionAction.dictionary:
                design += "window_condition_action_block|"
                text = condition_action_handling.ConditionAction.dictionary[i].condition_id.get("1.0", tk.END)
                design += str(len(text)) + "|"
                design += text
                text = condition_action_handling.ConditionAction.dictionary[i].action_id.get("1.0", tk.END)
                design += str(len(text)) + "|"
                design += text
                design += _get_coords(i)
                print_tags = True
            elif i in global_actions.GlobalActions.dictionary:
                design += "window_global_actions|"
                text_before = global_actions.GlobalActions.dictionary[i].text_before_id.get("1.0", tk.END)
                design += str(len(text_before)) + "|"
                design += text_before
                text_after = global_actions.GlobalActions.dictionary[i].text_after_id.get("1.0", tk.END)
                design += str(len(text_after)) + "|"
                design += text_after
                design += _get_coords(i)
            elif i in global_actions_combinatorial.GlobalActionsCombinatorial.dictionary:
                design += "window_global_actions_combinatorial|"
                text = global_actions_combinatorial.GlobalActionsCombinatorial.dictionary[i].text_id.get("1.0", tk.END)
                design += str(len(text)) + "|"
                design += text
                design += _get_coords(i)
            elif i in state_actions_default.StateActionsDefault.dictionary:
                design += "window_state_actions_default|"
                text = state_actions_default.StateActionsDefault.dictionary[i].text_id.get("1.0", tk.END)
                design += str(len(text)) + "|"
                design += text
                design += _get_coords(i)
            else:
                print(
                    "get_complete_design_as_text_object: Fatal, unknown dictionary key ", i, main_window.canvas.type(i)
                )
            design += _get_tags(i)
            if print_tags is True:
                print_tags = False
            design += " \n"

    return design


def _get_coords(canvas_id: int) -> str:
    coords = main_window.canvas.coords(canvas_id)
    coords_string = ""
    for c in coords:
        coords_string += str(c) + " "
    return coords_string


def _get_tags(canvas_id: int) -> str:
    tags = main_window.canvas.gettags(canvas_id)
    tags_string = ""
    for t in tags:
        if t != "current":
            tags_string += str(t) + " "
    return tags_string


def _get_fill_color(canvas_id: int) -> str:
    color = main_window.canvas.itemcget(canvas_id, "fill")
    assert isinstance(color, str)
    return "fill=" + color + " "


_line_index = 0


def _set_diagram_to_version_selected_by_stack_pointer() -> None:
    global _line_index
    # Remove the old design:
    state_action_handling.MyText.mytext_dict = {}
    condition_action_handling.ConditionAction.dictionary = {}
    state_comment.StateComment.dictionary = {}
    main_window.canvas.delete("all")
    # Bring the notebook tab with the diagram into the foreground:
    notebook_ids = main_window.notebook.tabs()
    for notebook_id in notebook_ids:
        if main_window.notebook.tab(notebook_id, option="text") == "Graph":
            main_window.notebook.select(notebook_id)
    # Read the design from the stack:
    design = stack[stack_write_pointer]
    # Convert the string stored in "design" into a list (but provide a return at each line end,
    # to have the same format as when reading from a file):
    lines_without_return = design.split("\n")
    lines = []
    for line in lines_without_return:
        lines.append(line + "\n")
    # Build the new design:
    _line_index = 0
    list_of_states = []
    while _line_index < len(lines):
        tags: list[str] = []
        if lines[_line_index].startswith("state_number|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "state_number|")
            state_handling.state_number = int(rest_of_line)
        elif lines[_line_index].startswith("transition_number|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "transition_number|")
            transition_handling.transition_number = int(rest_of_line)
        elif lines[_line_index].startswith("reset_entry_number|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "reset_entry_number|")
            reset_entry_handling.reset_entry_number = int(rest_of_line)
            if reset_entry_handling.reset_entry_number == 0:
                main_window.reset_entry_button.config(state=tk.NORMAL)
            else:
                main_window.reset_entry_button.config(state=tk.DISABLED)
        elif lines[_line_index].startswith("connector_number|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "connector_number|")
            connector_handling.connector_number = int(rest_of_line)
        elif lines[_line_index].startswith("conditionaction_id|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "conditionaction_id|")
            condition_action_handling.ConditionAction.conditionaction_id = int(rest_of_line)
        elif lines[_line_index].startswith("mytext_id|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "mytext_id|")
            state_action_handling.MyText.mytext_id = int(rest_of_line)
        elif lines[_line_index].startswith("state_actions_default_number|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "state_actions_default_number|")
            global_actions_handling.state_actions_default_number = int(rest_of_line)
            if global_actions_handling.state_actions_default_number == 0:
                main_window.state_action_default_button.config(state=tk.NORMAL)
            else:
                main_window.state_action_default_button.config(state=tk.DISABLED)
        elif lines[_line_index].startswith("global_actions_number|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "global_actions_number|")
            global_actions_handling.global_actions_clocked_number = int(rest_of_line)
            if global_actions_handling.global_actions_clocked_number == 0:
                main_window.global_action_clocked_button.config(state=tk.NORMAL)
            else:
                main_window.global_action_clocked_button.config(state=tk.DISABLED)
        elif lines[_line_index].startswith("global_actions_combinatorial_number|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "global_actions_combinatorial_number|")
            global_actions_handling.global_actions_combinatorial_number = int(rest_of_line)
            if global_actions_handling.global_actions_combinatorial_number == 0:
                main_window.global_action_combinatorial_button.config(state=tk.NORMAL)
            else:
                main_window.global_action_combinatorial_button.config(state=tk.DISABLED)
        elif lines[_line_index].startswith("state_radius|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "state_radius|")
            canvas_editing.state_radius = float(rest_of_line)
        elif lines[_line_index].startswith("reset_entry_size|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "reset_entry_size|")
            canvas_editing.reset_entry_size = int(float(rest_of_line))
        elif lines[_line_index].startswith("priority_distance|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "priority_distance|")
            canvas_editing.priority_distance = int(float(rest_of_line))
        elif lines[_line_index].startswith("fontsize|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "fontsize|")
            fontsize = float(rest_of_line)
            canvas_editing.fontsize = fontsize
            assert canvas_editing.state_name_font is not None
            canvas_editing.state_name_font.configure(size=int(fontsize))
        elif lines[_line_index].startswith("label_fontsize|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "label_fontsize|")
            canvas_editing.label_fontsize = float(rest_of_line)
        elif lines[_line_index].startswith("visible_center|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "visible_center|")
            canvas_editing.shift_visible_center_to_window_center(rest_of_line)
        elif lines[_line_index].startswith("state|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "state|")
            coords = []
            fill_color = constants.STATE_COLOR
            entries = rest_of_line.split()
            for e in entries:
                try:
                    v = float(e)
                    coords.append(v)
                except ValueError:
                    if "fill=" in e:
                        fill_color = e.replace("fill=", "")
                    else:
                        tags.append(e)
            state_id = state_handling.draw_state_circle(coords, fill_color, tags)
            list_of_states.append(state_id)
        elif lines[_line_index].startswith("polygon|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "polygon|")
            coords = []
            entries = rest_of_line.split()
            for e in entries:
                try:
                    v = float(e)
                    coords.append(v)
                except ValueError:
                    tags.append(e)
            poly_points = list(zip(coords[::2], coords[1::2]))
            reset_entry_handling.draw_reset_entry(poly_points, tags)
        elif lines[_line_index].startswith("text|"):  # This is a state-name or a priority-number.
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "text|")
            entries = rest_of_line.split()
            coords = []
            coords.append(float(entries[0]))
            coords.append(float(entries[1]))
            text = entries[2]
            for e in entries[3:]:
                tags.append(e)
            text_is_state_name = False
            text_is_reset_text = False
            for t in tags:
                if t.startswith("state"):  # state<nr>_name
                    text_is_state_name = True
                elif t.startswith("reset_text"):
                    text_is_reset_text = True
            if text_is_state_name:
                state_handling.draw_state_name(coords[0], coords[1], text, tags)
            elif text_is_reset_text:
                reset_entry_handling.draw_reset_entry_text(coords[0], coords[1], text, tags)
            else:
                # assert canvas_editing.state_name_font is not None
                # text_id = main_window.canvas.create_text(
                #     coords, text=text, tags=tags, font=canvas_editing.state_name_font
                # )
                for t in tags:
                    if t.startswith("transition"):
                        transition_tag = t[:-8]
                        transition_handling.draw_priority_number(coords, text, tags, transition_tag)
        elif lines[_line_index].startswith("line|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "line|")
            coords = []
            entries = rest_of_line.split()
            for e in entries:
                try:
                    v = float(e)
                    coords.append(v)
                except ValueError:
                    tags.append(e)
            for t in tags:
                if t.startswith("connected_to_transition"):  # line to condition&action block
                    trans_id = main_window.canvas.create_line(
                        coords, dash=(2, 2), fill="black", tags=tags, state=tk.HIDDEN
                    )
                    break
                if t.startswith("connected_to_state") or t.endswith("_comment_line"):  # line to state action/comment
                    trans_id = main_window.canvas.create_line(coords, dash=(2, 2), fill="black", tags=tags)
                    break
                if t.startswith("transition"):
                    trans_id = transition_handling.draw_transition(coords, tags)
                    main_window.canvas.tag_lower(trans_id)
                    break
            main_window.canvas.tag_lower(trans_id)  # Lines are always "under" anything else.
        elif lines[_line_index].startswith("rectangle|"):  # Used as connector or as priority entry.
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "rectangle|")
            coords = []
            entries = rest_of_line.split()
            for e in entries:
                try:
                    v = float(e)
                    coords.append(v)
                except ValueError:
                    tags.append(e)
            is_priority_rectangle = True
            for t in tags:
                if t.startswith("connector"):
                    is_priority_rectangle = False
            rect_coords = tuple(coords)
            assert len(rect_coords) == 4
            if is_priority_rectangle:
                rectangle_id = main_window.canvas.create_rectangle(rect_coords, tags=tags, fill=constants.STATE_COLOR)
            else:
                rectangle_id = connector_handling.draw_connector(rect_coords, tags)
            main_window.canvas.tag_raise(rectangle_id)  # priority rectangles are always in "foreground"
        elif lines[_line_index].startswith("window_state_action_block|"):  # state_action
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "window_state_action_block|")
            text = _get_data(rest_of_line, lines)
            coords = []
            _line_index += 1
            last_line = lines[_line_index]
            entries = last_line.split()
            for e in entries:
                try:
                    v = float(e)
                    coords.append(v)
                except ValueError:
                    tags.append(e)
            action_ref: state_action_handling.MyText = state_action_handling.MyText(
                coords[0] - 100, coords[1], height=1, width=8, padding=1, increment=False
            )
            action_ref.text_id.insert("1.0", text)
            action_ref.text_id.format()
            main_window.canvas.itemconfigure(action_ref.window_id, tags=tags)
        elif lines[_line_index].startswith("window_state_comment|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "window_state_comment|")
            text = _get_data(rest_of_line, lines)
            coords = []
            _line_index += 1
            last_line = lines[_line_index]
            entries = last_line.split()
            for e in entries:
                try:
                    v = float(e)
                    coords.append(v)
                except ValueError:
                    tags.append(e)
            comment_ref = state_comment.StateComment(coords[0] - 100, coords[1], height=1, width=8, padding=1)
            comment_ref.text_id.insert("1.0", text)
            comment_ref.text_id.format()
            main_window.canvas.itemconfigure(comment_ref.window_id, tags=tags)
        elif lines[_line_index].startswith("window_condition_action_block|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "window_condition_action_block|")
            condition = _get_data(rest_of_line, lines)
            _line_index += 1
            next_line = lines[_line_index]
            action = _get_data(next_line, lines)
            coords = []
            _line_index += 1
            last_line = lines[_line_index]
            entries = last_line.split()
            for e in entries:
                try:
                    v = float(e)
                    coords.append(v)
                except ValueError:
                    tags.append(e)
            connected_to_reset_entry = False
            for t in tags:
                if t == "connected_to_reset_transition":
                    connected_to_reset_entry = True
            condition_action_ref = condition_action_handling.ConditionAction(
                coords[0], coords[1], connected_to_reset_entry, height=1, width=8, padding=1, increment=False
            )
            condition_action_ref.condition_id.insert("1.0", condition)
            condition_action_ref.condition_id.format()
            condition_action_ref.action_id.insert("1.0", action)
            condition_action_ref.action_id.format()
            if (
                condition_action_ref.condition_id.get("1.0", tk.END) == "\n"
                and condition_action_ref.action_id.get("1.0", tk.END) != "\n"
            ):
                condition_action_ref.condition_label.grid_forget()
                condition_action_ref.condition_id.grid_forget()
            if (
                condition_action_ref.condition_id.get("1.0", tk.END) != "\n"
                and condition_action_ref.action_id.get("1.0", tk.END) == "\n"
            ):
                condition_action_ref.action_label.grid_forget()
                condition_action_ref.action_id.grid_forget()
            main_window.canvas.itemconfigure(condition_action_ref.window_id, tags=tags)
        elif lines[_line_index].startswith("window_global_actions|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "window_global_actions|")
            text_before = _get_data(rest_of_line, lines)
            _line_index += 1
            next_line = lines[_line_index]
            text_after = _get_data(next_line, lines)
            coords = []
            _line_index += 1
            last_line = lines[_line_index]
            entries = last_line.split()
            for e in entries:
                try:
                    v = float(e)
                    coords.append(v)
                except ValueError:
                    tags.append(e)
            global_actions_ref = global_actions.GlobalActions(coords[0], coords[1], height=1, width=8, padding=1)
            global_actions_ref.text_before_id.insert("1.0", text_before)
            global_actions_ref.text_before_id.format()
            global_actions_ref.text_after_id.insert("1.0", text_after)
            global_actions_ref.text_after_id.format()
            main_window.canvas.itemconfigure(global_actions_ref.window_id, tags=tags)
        elif lines[_line_index].startswith("window_global_actions_combinatorial|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "window_global_actions_combinatorial|")
            text = _get_data(rest_of_line, lines)
            coords = []
            _line_index += 1
            last_line = lines[_line_index]
            entries = last_line.split()
            for e in entries:
                try:
                    v = float(e)
                    coords.append(v)
                except ValueError:
                    tags.append(e)
            gac_action_ref = global_actions_combinatorial.GlobalActionsCombinatorial(
                coords[0], coords[1], height=1, width=8, padding=1
            )
            gac_action_ref.text_id.insert("1.0", text)
            gac_action_ref.text_id.format()
            main_window.canvas.itemconfigure(gac_action_ref.window_id, tags=tags)
        elif lines[_line_index].startswith("window_state_actions_default|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "window_state_actions_default|")
            text = _get_data(rest_of_line, lines)
            coords = []
            _line_index += 1
            last_line = lines[_line_index]
            entries = last_line.split()
            for e in entries:
                try:
                    v = float(e)
                    coords.append(v)
                except ValueError:
                    tags.append(e)
            sad_action_ref = state_actions_default.StateActionsDefault(
                coords[0], coords[1], height=1, width=8, padding=1
            )
            sad_action_ref.text_id.insert("1.0", text)
            sad_action_ref.text_id.format()
            main_window.canvas.itemconfigure(sad_action_ref.window_id, tags=tags)

        elif lines[_line_index].startswith("interface_package|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "interface_package|")
            data = _get_data(rest_of_line, lines)
            main_window.interface_package_text.delete("1.0", tk.END)
            main_window.interface_package_text.insert("1.0", data)
            main_window.interface_package_text.update_highlight_tags(
                10, ["not_read", "not_written", "control", "datatype", "function", "comment"]
            )
        elif lines[_line_index].startswith("interface_generics|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "interface_generics|")
            data = _get_data(rest_of_line, lines)
            main_window.interface_generics_text.delete("1.0", tk.END)
            main_window.interface_generics_text.insert("1.0", data)
            main_window.interface_generics_text.update_highlight_tags(
                10, ["not_read", "not_written", "control", "datatype", "function", "comment"]
            )
            main_window.interface_generics_text.update_custom_text_class_generics_list()
        elif lines[_line_index].startswith("interface_ports|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "interface_ports|")
            data = _get_data(rest_of_line, lines)
            main_window.interface_ports_text.delete("1.0", tk.END)
            main_window.interface_ports_text.insert("1.0", data)
            main_window.interface_ports_text.update_highlight_tags(
                10, ["not_read", "not_written", "control", "datatype", "function", "comment"]
            )
            main_window.interface_ports_text.update_custom_text_class_ports_list()
        elif lines[_line_index].startswith("internals_package|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "internals_package|")
            data = _get_data(rest_of_line, lines)
            main_window.internals_package_text.delete("1.0", tk.END)
            main_window.internals_package_text.insert("1.0", data)
            main_window.internals_package_text.update_highlight_tags(
                10, ["not_read", "not_written", "control", "datatype", "function", "comment"]
            )
        elif lines[_line_index].startswith("internals_architecture|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "internals_architecture|")
            data = _get_data(rest_of_line, lines)
            main_window.internals_architecture_text.delete("1.0", tk.END)
            main_window.internals_architecture_text.insert("1.0", data)
            main_window.internals_architecture_text.update_highlight_tags(
                10, ["not_read", "not_written", "control", "datatype", "function", "comment"]
            )
            main_window.internals_architecture_text.update_custom_text_class_signals_list()
        elif lines[_line_index].startswith("internals_process|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "internals_process|")
            data = _get_data(rest_of_line, lines)
            main_window.internals_process_clocked_text.delete("1.0", tk.END)
            main_window.internals_process_clocked_text.insert("1.0", data)
            main_window.internals_process_clocked_text.update_highlight_tags(
                10, ["not_read", "not_written", "control", "datatype", "function", "comment"]
            )
            main_window.internals_process_clocked_text.update_custom_text_class_signals_list()
        elif lines[_line_index].startswith("internals_process_combinatorial|"):
            rest_of_line = _remove_keyword_from_line(lines[_line_index], "internals_process_combinatorial|")
            data = _get_data(rest_of_line, lines)
            main_window.internals_process_combinatorial_text.delete("1.0", tk.END)
            main_window.internals_process_combinatorial_text.insert("1.0", data)
            main_window.internals_process_combinatorial_text.update_highlight_tags(
                10, ["not_read", "not_written", "control", "datatype", "function", "comment"]
            )
            main_window.internals_process_combinatorial_text.update_custom_text_class_signals_list()
        _line_index += 1
    for state in list_of_states:
        canvas_editing.adapt_visibility_of_priority_rectangles_at_state(state)
    main_window.grid_drawer.draw_grid()


def _remove_keyword_from_line(line: str, keyword: str) -> str:
    return line[len(keyword) :]


def _get_data(rest_of_line: str, lines: list[str]) -> str:
    length_of_data = _get_length_info_from_line(rest_of_line)
    first_data = _remove_length_info(rest_of_line)
    data = _get_remaining_data(lines, length_of_data, first_data)
    return data


def _get_length_info_from_line(rest_of_line: str) -> int:
    return int(re.sub(r"\|.*", "", rest_of_line))


def _remove_length_info(rest_of_line: str) -> str:
    return re.sub(r".*\|", "", rest_of_line)


def _get_remaining_data(lines: list[str], length_of_data: int, first_data: str) -> str:
    global _line_index
    data = first_data
    while len(data) < length_of_data:
        _line_index += 1
        data = data + lines[_line_index]
    return data[:-1]
