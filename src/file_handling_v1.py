"""
This module contains methods for reading HDL-FSM-Editor version 1 files.
Version 1 files use a text-based format with line-by-line parsing.
"""

import os
import re
import tkinter as tk

import canvas_editing
import condition_action_handling
import connector_handling
import constants
import custom_text
import global_actions
import global_actions_combinatorial
import global_actions_handling
import main_window
import reset_entry_handling
import state_action_handling
import state_actions_default
import state_handling
import transition_handling
import undo_handling
from constants import GuiTab

# Canvas drawing constants
CANVAS_STATE_WIDTH_NORMAL = 2
CANVAS_STATE_WIDTH_HOVER = 4
CANVAS_POLYGON_WIDTH_NORMAL = 1
CANVAS_POLYGON_WIDTH_HOVER = 2
CANVAS_LINE_WIDTH_NORMAL = 1
CANVAS_LINE_WIDTH_HOVER = 3

# Text widget constants
TEXT_WIDGET_HEIGHT = 1
TEXT_WIDGET_WIDTH = 8
TEXT_WIDGET_PADDING = 1
HIGHLIGHT_TAG_FONT_SIZE = 10

# Dash pattern for dashed lines
DASH_PATTERN = (2, 2)


def open_v1_file_with_name(read_filename) -> None:
    """
    Opens and loads a version 1 HDL-FSM-Editor file.
    Version 1 files use a text-based format with line-by-line parsing.
    """
    custom_text.CustomText.read_variables_of_all_windows.clear()
    custom_text.CustomText.written_variables_of_all_windows.clear()
    # Bring the notebook tab with the graphic into the foreground:
    notebook_ids = main_window.notebook.tabs()
    for notebook_id in notebook_ids:
        if main_window.notebook.tab(notebook_id, option="text") == GuiTab.DIAGRAM:
            main_window.notebook.select(notebook_id)
    # Read the design from the file:
    with open(read_filename, encoding="utf-8") as fileobject:
        for line in fileobject:
            tags: tuple[str, ...]

            if line.startswith("modulename|"):
                main_window.module_name.set(line[11:-1])
            elif line.startswith("language|"):
                LANGUAGE_PREFIX_LENGTH = 9
                old_language = main_window.language.get()
                main_window.language.set(line[LANGUAGE_PREFIX_LENGTH:-1])
                if line[LANGUAGE_PREFIX_LENGTH:1] != old_language:
                    main_window.switch_language_mode()
            elif line.startswith("generate_path|"):
                GENERATE_PATH_PREFIX_LENGTH = 14
                main_window.generate_path_value.set(line[GENERATE_PATH_PREFIX_LENGTH:-1])
            elif line.startswith("working_directory|"):
                WORKING_DIRECTORY_PREFIX_LENGTH = 18
                main_window.working_directory_value.set(line[WORKING_DIRECTORY_PREFIX_LENGTH:-1])
            elif line.startswith("number_of_files|"):
                NUMBER_OF_FILES_PREFIX_LENGTH = 16
                main_window.select_file_number_text.set(int(line[NUMBER_OF_FILES_PREFIX_LENGTH:-1]))
            elif line.startswith("reset_signal_name|"):
                RESET_SIGNAL_PREFIX_LENGTH = 18
                main_window.reset_signal_name.set(line[RESET_SIGNAL_PREFIX_LENGTH:-1])
            elif line.startswith("clock_signal_name|"):
                CLOCK_SIGNAL_PREFIX_LENGTH = 18
                main_window.clock_signal_name.set(line[CLOCK_SIGNAL_PREFIX_LENGTH:-1])
            elif line.startswith("compile_cmd|"):
                COMPILE_CMD_PREFIX_LENGTH = 12
                main_window.compile_cmd.set(line[COMPILE_CMD_PREFIX_LENGTH:-1])
            elif line.startswith("edit_cmd|"):
                EDIT_CMD_PREFIX_LENGTH = 9
                main_window.edit_cmd.set(line[EDIT_CMD_PREFIX_LENGTH:-1])
            elif line.startswith("interface_package|"):
                rest_of_line = _remove_keyword_from_line(line, "interface_package|")
                data = _get_data(rest_of_line, fileobject)
                main_window.interface_package_text.insert("1.0", data)
                main_window.interface_package_text.update_highlight_tags(
                    HIGHLIGHT_TAG_FONT_SIZE, ["not_read", "not_written", "control", "datatype", "function", "comment"]
                )
            elif line.startswith("interface_generics|"):
                rest_of_line = _remove_keyword_from_line(line, "interface_generics|")
                data = _get_data(rest_of_line, fileobject)
                main_window.interface_generics_text.insert("1.0", data)
                main_window.interface_generics_text.update_highlight_tags(
                    HIGHLIGHT_TAG_FONT_SIZE, ["not_read", "not_written", "control", "datatype", "function", "comment"]
                )
                main_window.interface_generics_text.update_custom_text_class_generics_list()
            elif line.startswith("interface_ports|"):
                rest_of_line = _remove_keyword_from_line(line, "interface_ports|")
                data = _get_data(rest_of_line, fileobject)
                main_window.interface_ports_text.insert("1.0", data)
                main_window.interface_ports_text.update_highlight_tags(
                    HIGHLIGHT_TAG_FONT_SIZE, ["not_read", "not_written", "control", "datatype", "function", "comment"]
                )
                main_window.interface_ports_text.update_custom_text_class_ports_list()
            elif line.startswith("internals_package|"):
                rest_of_line = _remove_keyword_from_line(line, "internals_package|")
                data = _get_data(rest_of_line, fileobject)
                main_window.internals_package_text.insert("1.0", data)
                main_window.internals_package_text.update_highlight_tags(
                    HIGHLIGHT_TAG_FONT_SIZE, ["not_read", "not_written", "control", "datatype", "function", "comment"]
                )
            elif line.startswith("internals_architecture|"):
                rest_of_line = _remove_keyword_from_line(line, "internals_architecture|")
                data = _get_data(rest_of_line, fileobject)
                main_window.internals_architecture_text.insert("1.0", data)
                main_window.internals_architecture_text.update_highlight_tags(
                    HIGHLIGHT_TAG_FONT_SIZE, ["not_read", "not_written", "control", "datatype", "function", "comment"]
                )
                main_window.internals_architecture_text.update_custom_text_class_signals_list()
            elif line.startswith("internals_process|"):
                rest_of_line = _remove_keyword_from_line(line, "internals_process|")
                data = _get_data(rest_of_line, fileobject)
                main_window.internals_process_clocked_text.insert("1.0", data)
                main_window.internals_process_clocked_text.update_highlight_tags(
                    HIGHLIGHT_TAG_FONT_SIZE, ["not_read", "not_written", "control", "datatype", "function", "comment"]
                )
                main_window.internals_process_clocked_text.update_custom_text_class_signals_list()
            elif line.startswith("internals_process_combinatorial|"):
                rest_of_line = _remove_keyword_from_line(line, "internals_process_combinatorial|")
                data = _get_data(rest_of_line, fileobject)
                main_window.internals_process_combinatorial_text.insert("1.0", data)
                main_window.internals_process_combinatorial_text.update_highlight_tags(
                    HIGHLIGHT_TAG_FONT_SIZE, ["not_read", "not_written", "control", "datatype", "function", "comment"]
                )
                main_window.internals_process_combinatorial_text.update_custom_text_class_signals_list()
            elif line.startswith(
                "state_number|"
            ):  # The state_number (as transition_number, connector_number, ...) must be restored,
                rest_of_line = _remove_keyword_from_line(
                    line, "state_number|"
                )  # otherwise it could happen, that 2 states get both the tag "state1".
                state_handling.state_number = int(rest_of_line)
            elif line.startswith("transition_number|"):
                rest_of_line = _remove_keyword_from_line(line, "transition_number|")
                transition_handling.transition_number = int(rest_of_line)
            elif line.startswith("reset_entry_number|"):
                rest_of_line = _remove_keyword_from_line(line, "reset_entry_number|")
                reset_entry_handling.reset_entry_number = int(rest_of_line)
                if reset_entry_handling.reset_entry_number == 0:
                    main_window.reset_entry_button.config(state=tk.NORMAL)
                else:
                    main_window.reset_entry_button.config(state=tk.DISABLED)
            elif line.startswith("connector_number|"):
                rest_of_line = _remove_keyword_from_line(line, "connector_number|")
                connector_handling.connector_number = int(rest_of_line)
            elif line.startswith("conditionaction_id|"):
                rest_of_line = _remove_keyword_from_line(line, "conditionaction_id|")
                condition_action_handling.ConditionAction.conditionaction_id = int(rest_of_line)
            elif line.startswith("mytext_id|"):
                rest_of_line = _remove_keyword_from_line(line, "mytext_id|")
                state_action_handling.MyText.mytext_id = int(rest_of_line)
            elif line.startswith("global_actions_number|"):
                rest_of_line = _remove_keyword_from_line(line, "global_actions_number|")
                global_actions_handling.global_actions_clocked_number = int(rest_of_line)
                if global_actions_handling.global_actions_clocked_number == 0:
                    main_window.global_action_clocked_button.config(state=tk.NORMAL)
                else:
                    main_window.global_action_clocked_button.config(state=tk.DISABLED)
            elif line.startswith("state_actions_default_number|"):
                rest_of_line = _remove_keyword_from_line(line, "state_actions_default_number|")
                global_actions_handling.state_actions_default_number = int(rest_of_line)
                if global_actions_handling.state_actions_default_number == 0:
                    main_window.state_action_default_button.config(state=tk.NORMAL)
                else:
                    main_window.state_action_default_button.config(state=tk.DISABLED)
            elif line.startswith("global_actions_combinatorial_number|"):
                rest_of_line = _remove_keyword_from_line(line, "global_actions_combinatorial_number|")
                global_actions_handling.global_actions_combinatorial_number = int(rest_of_line)
                if global_actions_handling.global_actions_combinatorial_number == 0:
                    main_window.global_action_combinatorial_button.config(state=tk.NORMAL)
                else:
                    main_window.global_action_combinatorial_button.config(state=tk.DISABLED)
            elif line.startswith("state_radius|"):
                rest_of_line = _remove_keyword_from_line(line, "state_radius|")
                canvas_editing.state_radius = float(rest_of_line)
            elif line.startswith("reset_entry_size|"):
                rest_of_line = _remove_keyword_from_line(line, "reset_entry_size|")
                canvas_editing.reset_entry_size = int(float(rest_of_line))
            elif line.startswith("priority_distance|"):
                rest_of_line = _remove_keyword_from_line(line, "priority_distance|")
                canvas_editing.priority_distance = int(float(rest_of_line))
            elif line.startswith("fontsize|"):
                rest_of_line = _remove_keyword_from_line(line, "fontsize|")
                fontsize = float(rest_of_line)
                canvas_editing.fontsize = fontsize
                if canvas_editing.state_name_font is not None:
                    canvas_editing.state_name_font.configure(size=int(fontsize))
            elif line.startswith("label_fontsize|"):
                rest_of_line = _remove_keyword_from_line(line, "label_fontsize|")
                canvas_editing.label_fontsize = float(rest_of_line)
            elif line.startswith("include_timestamp_in_output|"):
                rest_of_line = _remove_keyword_from_line(line, "include_timestamp_in_output|")
                main_window.include_timestamp_in_output.set(rest_of_line.lower() == "true")
            elif line.startswith("visible_center|"):
                rest_of_line = _remove_keyword_from_line(line, "visible_center|")
                canvas_editing.shift_visible_center_to_window_center(rest_of_line)
            elif line.startswith("state|"):
                rest_of_line = _remove_keyword_from_line(line, "state|")
                coords = []
                tags = ()
                entries = rest_of_line.split()
                for e in entries:
                    try:
                        v = float(e)
                        coords.append(v)
                    except ValueError:
                        tags = tags + (e,)
                state_id = main_window.canvas.create_oval(
                    coords, fill=constants.STATE_COLOR, width=CANVAS_STATE_WIDTH_NORMAL, outline="blue", tags=tags
                )
                main_window.canvas.tag_bind(
                    state_id,
                    "<Enter>",
                    lambda event, id=state_id: main_window.canvas.itemconfig(id, width=CANVAS_STATE_WIDTH_HOVER),
                )
                main_window.canvas.tag_bind(
                    state_id,
                    "<Leave>",
                    lambda event, id=state_id: main_window.canvas.itemconfig(id, width=CANVAS_STATE_WIDTH_NORMAL),
                )
                main_window.canvas.tag_bind(
                    state_id, "<Button-3>", lambda event, id=state_id: state_handling.show_menu(event, id)
                )
            elif line.startswith("polygon|"):
                rest_of_line = _remove_keyword_from_line(line, "polygon|")
                coords = []
                tags = ()
                entries = rest_of_line.split()
                for e in entries:
                    try:
                        v = float(e)
                        coords.append(v)
                    except ValueError:
                        tags = tags + (e,)
                polygon_id = main_window.canvas.create_polygon(coords, fill="red", outline="orange", tags=tags)
                main_window.canvas.tag_bind(
                    polygon_id,
                    "<Enter>",
                    lambda event, id=polygon_id: main_window.canvas.itemconfig(id, width=CANVAS_POLYGON_WIDTH_HOVER),
                )
                main_window.canvas.tag_bind(
                    polygon_id,
                    "<Leave>",
                    lambda event, id=polygon_id: main_window.canvas.itemconfig(id, width=CANVAS_POLYGON_WIDTH_NORMAL),
                )
            elif line.startswith("text|"):
                rest_of_line = _remove_keyword_from_line(line, "text|")
                tags = ()
                entries = rest_of_line.split()
                coords = []
                coords.append(float(entries[0]))
                coords.append(float(entries[1]))
                text = entries[2]
                for e in entries[3:]:
                    tags = tags + (e,)
                text_id = main_window.canvas.create_text(
                    coords, text=text, tags=tags, font=canvas_editing.state_name_font
                )
                for t in tags:
                    if t.startswith("transition"):
                        main_window.canvas.tag_bind(
                            text_id,
                            "<Double-Button-1>",
                            lambda event, transition_tag=t[:-8]: transition_handling.edit_priority(
                                event, transition_tag
                            ),
                        )
                    else:
                        main_window.canvas.tag_bind(
                            text_id,
                            "<Double-Button-1>",
                            lambda event, text_id=text_id: state_handling.edit_state_name(event, text_id),
                        )
            elif line.startswith("line|"):
                rest_of_line = _remove_keyword_from_line(line, "line|")
                coords = []
                tags = ()
                entries = rest_of_line.split()
                for e in entries:
                    try:
                        v = float(e)
                        coords.append(v)
                    except ValueError:
                        tags = tags + (e,)
                trans_id = main_window.canvas.create_line(coords, smooth=True, fill="blue", tags=tags)
                main_window.canvas.tag_lower(trans_id)  # Lines are always "under" the priority rectangles.
                main_window.canvas.tag_bind(
                    trans_id,
                    "<Enter>",
                    lambda event, trans_id=trans_id: main_window.canvas.itemconfig(
                        trans_id, width=CANVAS_LINE_WIDTH_HOVER
                    ),
                )
                main_window.canvas.tag_bind(
                    trans_id,
                    "<Leave>",
                    lambda event, trans_id=trans_id: main_window.canvas.itemconfig(
                        trans_id, width=CANVAS_LINE_WIDTH_NORMAL
                    ),
                )
                for t in tags:
                    if t.startswith("connected_to_transition"):
                        main_window.canvas.itemconfig(trans_id, dash=DASH_PATTERN, state=tk.HIDDEN)
                    elif t.startswith("connected_to_state"):
                        main_window.canvas.itemconfig(trans_id, dash=DASH_PATTERN)
                    elif t.startswith("transition"):
                        main_window.canvas.itemconfig(trans_id, arrow="last")
                        main_window.canvas.tag_bind(
                            trans_id, "<Button-3>", lambda event, id=trans_id: transition_handling.show_menu(event, id)
                        )
            elif line.startswith("rectangle|"):  # Used as connector or as priority entry.
                rest_of_line = _remove_keyword_from_line(line, "rectangle|")
                coords = []
                tags = ()
                entries = rest_of_line.split()
                for e in entries:
                    try:
                        v = float(e)
                        coords.append(v)
                    except ValueError:
                        tags = tags + (e,)
                rectangle_color = constants.STATE_COLOR
                for t in tags:
                    if t.startswith("connector"):
                        rectangle_color = constants.CONNECTOR_COLOR
                canvas_id = main_window.canvas.create_rectangle(coords, tag=tags, fill=rectangle_color)
                main_window.canvas.tag_raise(canvas_id)  # priority rectangles are always in "foreground"
            elif line.startswith("window_state_action_block|"):
                rest_of_line = _remove_keyword_from_line(line, "window_state_action_block|")
                text = _get_data(rest_of_line, fileobject)
                coords = []
                tags = ()
                last_line = fileobject.readline()
                entries = last_line.split()
                for e in entries:
                    try:
                        v = float(e)
                        coords.append(v)
                    except ValueError:
                        tags = tags + (e,)
                WINDOW_X_OFFSET = 100
                action_ref = state_action_handling.MyText(
                    coords[0] - WINDOW_X_OFFSET,
                    coords[1],
                    height=TEXT_WIDGET_HEIGHT,
                    width=TEXT_WIDGET_WIDTH,
                    padding=TEXT_WIDGET_PADDING,
                    increment=False,
                )
                action_ref.text_id.insert("1.0", text)
                action_ref.text_id.format()
                main_window.canvas.itemconfigure(action_ref.window_id, tag=tags)
            elif line.startswith("window_condition_action_block|"):
                rest_of_line = _remove_keyword_from_line(line, "window_condition_action_block|")
                condition = _get_data(rest_of_line, fileobject)
                next_line = fileobject.readline()
                action = _get_data(next_line, fileobject)
                coords = []
                tags = ()
                last_line = fileobject.readline()
                entries = last_line.split()
                for e in entries:
                    try:
                        v = float(e)
                        coords.append(v)
                    except ValueError:
                        tags = tags + (e,)
                connected_to_reset_entry = False
                for t in tags:
                    if t == "connected_to_reset_transition":
                        connected_to_reset_entry = True
                condition_action_ref = condition_action_handling.ConditionAction(
                    coords[0],
                    coords[1],
                    connected_to_reset_entry,
                    height=TEXT_WIDGET_HEIGHT,
                    width=TEXT_WIDGET_WIDTH,
                    padding=TEXT_WIDGET_PADDING,
                    increment=False,
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
                main_window.canvas.itemconfigure(condition_action_ref.window_id, tag=tags)
            elif line.startswith("window_global_actions|"):
                rest_of_line = _remove_keyword_from_line(line, "window_global_actions|")
                text_before = _get_data(rest_of_line, fileobject)
                next_line = fileobject.readline()
                text_after = _get_data(next_line, fileobject)
                coords = []
                tags = ()
                last_line = fileobject.readline()
                entries = last_line.split()
                for e in entries:
                    try:
                        v = float(e)
                        coords.append(v)
                    except ValueError:
                        tags = tags + (e,)
                global_actions_ref = global_actions.GlobalActions(
                    coords[0],
                    coords[1],
                    height=TEXT_WIDGET_HEIGHT,
                    width=TEXT_WIDGET_WIDTH,
                    padding=TEXT_WIDGET_PADDING,
                )
                global_actions_ref.text_before_id.insert("1.0", text_before)
                global_actions_ref.text_before_id.format()
                global_actions_ref.text_after_id.insert("1.0", text_after)
                global_actions_ref.text_after_id.format()
                main_window.canvas.itemconfigure(global_actions_ref.window_id, tag=tags)
            elif line.startswith("window_global_actions_combinatorial|"):
                rest_of_line = _remove_keyword_from_line(line, "window_global_actions_combinatorial|")
                text = _get_data(rest_of_line, fileobject)
                coords = []
                tags = ()
                last_line = fileobject.readline()
                entries = last_line.split()
                for e in entries:
                    try:
                        v = float(e)
                        coords.append(v)
                    except ValueError:
                        tags = tags + (e,)
                action_ref = global_actions_combinatorial.GlobalActionsCombinatorial(
                    coords[0], coords[1], height=1, width=8, padding=1
                )
                action_ref.text_id.insert("1.0", text)
                action_ref.text_id.format()
                main_window.canvas.itemconfigure(action_ref.window_id, tag=tags)
            elif line.startswith("window_state_actions_default|"):
                rest_of_line = _remove_keyword_from_line(line, "window_state_actions_default|")
                text = _get_data(rest_of_line, fileobject)
                coords = []
                tags = ()
                last_line = fileobject.readline()
                entries = last_line.split()
                for e in entries:
                    try:
                        v = float(e)
                        coords.append(v)
                    except ValueError:
                        tags = tags + (e,)
                action_ref = state_actions_default.StateActionsDefault(
                    coords[0], coords[1], height=1, width=8, padding=1
                )
                action_ref.text_id.insert("1.0", text)
                action_ref.text_id.format()
                main_window.canvas.itemconfigure(action_ref.window_id, tag=tags)
    undo_handling.stack = []
    undo_handling.stack_write_pointer = 0
    undo_handling.design_has_changed()  # Initialize the stack with the read design.
    # main_window.root.update()
    dir_name, file_name = os.path.split(read_filename)
    main_window.root.title(f"{file_name} ({dir_name})")
    canvas_editing.view_all()


def _remove_keyword_from_line(line, keyword):
    """Remove keyword prefix from line."""
    return line[len(keyword) :]


def _get_data(rest_of_line, fileobject):
    """Extract data from version 1 file format."""
    length_of_data = _get_length_info_from_line(rest_of_line)
    first_data = _remove_length_info(rest_of_line)
    data = _get_remaining_data(fileobject, length_of_data, first_data)
    return data


def _get_length_info_from_line(rest_of_line) -> int:
    """Extract length information from line."""
    return int(re.sub(r"\|.*", "", rest_of_line))


def _remove_length_info(rest_of_line):
    """Remove length information from line."""
    return re.sub(r".*\|", "", rest_of_line)


def _get_remaining_data(fileobject, length_of_data, first_data):
    """Get remaining data based on length information."""
    data = first_data
    while len(data) < length_of_data:
        data = data + fileobject.readline()
    return data[:-1]
