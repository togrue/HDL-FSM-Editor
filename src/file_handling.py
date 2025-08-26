"""
This module contains all methods needed for reading and writing from or to a file.
"""

import json
import os
import tkinter as tk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename, asksaveasfilename
from typing import Any

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
import state_comment
import state_handling
import tag_plausibility
import transition_handling
import undo_handling
import update_hdl_tab
from constants import GuiTab
from project_manager import project_manager


def ask_save_unsaved_changes(title: str) -> str:
    """
    Ask user what to do with unsaved changes.
    Returns: 'save', 'discard', or 'cancel'
    """
    result = messagebox.askyesnocancel(
        "HDL-FSM-Editor",
        f"There are unsaved changes in design:\n{title[:-1]}\nDo you want to save them?",
        default="cancel",
        icon="warning",
    )
    if result is True:
        return "save"
    if result is False:
        return "discard"
    return "cancel"


def save_as() -> None:
    project_manager.previous_file = project_manager.current_file
    project_manager.current_file = asksaveasfilename(
        defaultextension=".hfe",
        initialfile=main_window.module_name.get(),
        filetypes=(("HDL-FSM-Editor files", "*.hfe"), ("all files", "*.*")),
    )
    if project_manager.current_file != "":
        dir_name, file_name = os.path.split(project_manager.current_file)
        main_window.root.title(f"{file_name} ({dir_name})")
        save_in_file_new(project_manager.current_file)


def save() -> None:
    # Use state manager instead of global variables
    project_manager.previous_file = project_manager.current_file
    if project_manager.current_file == "":
        project_manager.current_file = asksaveasfilename(
            defaultextension=".hfe",
            initialfile=main_window.module_name.get(),
            filetypes=(("HDL-FSM-Editor files", "*.hfe"), ("all files", "*.*")),
        )
    if project_manager.current_file != "":
        dir_name, file_name = os.path.split(project_manager.current_file)
        main_window.root.title(f"{file_name} ({dir_name})")
        main_window.root.after_idle(
            save_in_file_new, project_manager.current_file
        )  # Wait for the handling of all possible events.


def open_file() -> None:
    filename_new = askopenfilename(filetypes=(("HDL-FSM-Editor files", "*.hfe"), ("all files", "*.*")))
    if filename_new != "":
        success = new_design()
        if success:
            open_file_with_name_new(filename_new, is_script_mode=False)


def new_design() -> bool:
    title = main_window.root.title()
    if title.endswith("*"):
        action = ask_save_unsaved_changes(title)
        if action == "cancel":
            return False
        if action == "save":
            save()
            # Check if save was successful (current_file is not empty)
            if project_manager.current_file == "":
                return False

    _clear_design()
    return True


def _clear_design() -> bool:
    project_manager.current_file = ""
    main_window.module_name.set("")
    main_window.reset_signal_name.set("")
    main_window.clock_signal_name.set("")
    main_window.interface_package_text.delete("1.0", tk.END)
    main_window.interface_generics_text.delete("1.0", tk.END)
    main_window.interface_ports_text.delete("1.0", tk.END)
    main_window.internals_package_text.delete("1.0", tk.END)
    main_window.internals_architecture_text.delete("1.0", tk.END)
    main_window.internals_process_clocked_text.delete("1.0", tk.END)
    main_window.internals_process_combinatorial_text.delete("1.0", tk.END)
    main_window.hdl_frame_text.config(state=tk.NORMAL)
    main_window.hdl_frame_text.delete("1.0", tk.END)
    main_window.hdl_frame_text.config(state=tk.DISABLED)
    main_window.canvas.delete("all")
    state_handling.state_number = 0
    transition_handling.transition_number = 0
    reset_entry_handling.reset_entry_number = 0
    main_window.reset_entry_button.config(state=tk.NORMAL)
    connector_handling.connector_number = 0
    condition_action_handling.ConditionAction.conditionaction_id = 0
    condition_action_handling.ConditionAction.dictionary = {}
    state_action_handling.MyText.mytext_id = 0
    state_action_handling.MyText.mytext_dict = {}
    state_actions_default.StateActionsDefault.dictionary = {}
    global_actions_handling.state_actions_default_number = 0
    main_window.state_action_default_button.config(state=tk.NORMAL)
    global_actions_handling.global_actions_clocked_number = 0
    main_window.global_action_clocked_button.config(state=tk.NORMAL)
    global_actions_handling.global_actions_combinatorial_number = 0
    main_window.global_action_combinatorial_button.config(state=tk.NORMAL)
    global_actions_combinatorial.GlobalActionsCombinatorial.dictionary = {}
    global_actions.GlobalActions.dictionary = {}
    canvas_editing.state_radius = 20.0
    canvas_editing.priority_distance = 14
    canvas_editing.reset_entry_size = 40
    canvas_editing.canvas_x_coordinate = 0
    canvas_editing.canvas_y_coordinate = 0
    canvas_editing.fontsize = 10
    canvas_editing.label_fontsize = 8
    assert canvas_editing.state_name_font is not None
    canvas_editing.state_name_font.configure(size=int(canvas_editing.fontsize))
    main_window.include_timestamp_in_output.set(True)
    main_window.root.title("unnamed")
    main_window.grid_drawer.draw_grid()
    return True


########################################################################################################################


def save_in_file_new(save_filename: str) -> None:  # Called at saving and at every design change (writing to .tmp-file)
    design_dictionary = _save_design_to_dict()
    old_cursor = main_window.root.cget(
        "cursor"
    )  # may be different from "arrow" at design changes (writing to .tmp-file)
    main_window.root.config(cursor="watch")
    try:
        with open(save_filename, "w", encoding="utf-8") as fileobject:
            json.dump(design_dictionary, fileobject, indent=4, default=str, ensure_ascii=False)
        if not save_filename.endswith(".tmp") and os.path.isfile(f"{project_manager.previous_file}.tmp"):
            os.remove(f"{project_manager.previous_file}.tmp")
        main_window.root.config(cursor=old_cursor)
    except Exception as e:
        main_window.root.config(cursor=old_cursor)
        messagebox.showerror("Error in HDL-FSM-Editor", f"Writing to file {save_filename} caused an exception: {e}")
    if not tag_plausibility.TagPlausibility().get_tag_status_is_okay():
        main_window.root.config(cursor=old_cursor)
        messagebox.showerror("Error", "The database is corrupt.\nDo not use the written file.\nSee details at STDOUT.")


def _save_design_to_dict() -> dict[str, Any]:
    design_dictionary: dict[str, Any] = {}
    _save_control_data(design_dictionary)
    _save_interface_data(design_dictionary)
    _save_internals_data(design_dictionary)
    _save_log_config(design_dictionary)
    _save_canvas_data(design_dictionary)

    return design_dictionary


def _save_control_data(design_dictionary: dict[str, Any]) -> None:
    design_dictionary["modulename"] = main_window.module_name.get()
    design_dictionary["language"] = main_window.language.get()
    design_dictionary["generate_path"] = main_window.generate_path_value.get()
    design_dictionary["additional_sources"] = main_window.additional_sources_value.get()
    design_dictionary["working_directory"] = main_window.working_directory_value.get()
    design_dictionary["number_of_files"] = main_window.select_file_number_text.get()
    design_dictionary["reset_signal_name"] = main_window.reset_signal_name.get()
    design_dictionary["clock_signal_name"] = main_window.clock_signal_name.get()
    design_dictionary["compile_cmd"] = main_window.compile_cmd.get()
    design_dictionary["edit_cmd"] = main_window.edit_cmd.get()
    design_dictionary["include_timestamp_in_output"] = main_window.include_timestamp_in_output.get()


def _save_interface_data(design_dictionary: dict[str, Any]) -> None:
    design_dictionary["interface_package"] = main_window.interface_package_text.get("1.0", f"{tk.END}-1 chars")
    design_dictionary["interface_generics"] = main_window.interface_generics_text.get("1.0", f"{tk.END}-1 chars")
    design_dictionary["interface_ports"] = main_window.interface_ports_text.get("1.0", f"{tk.END}-1 chars")


def _save_internals_data(design_dictionary: dict[str, Any]) -> None:
    design_dictionary["internals_package"] = main_window.internals_package_text.get("1.0", f"{tk.END}-1 chars")
    design_dictionary["internals_architecture"] = main_window.internals_architecture_text.get(
        "1.0", f"{tk.END}-1 chars"
    )
    design_dictionary["internals_process"] = main_window.internals_process_clocked_text.get("1.0", f"{tk.END}-1 chars")
    design_dictionary["internals_process_combinatorial"] = main_window.internals_process_combinatorial_text.get(
        "1.0", f"{tk.END}-1 chars"
    )


def _save_log_config(design_dictionary: dict[str, Any]) -> None:
    if main_window.language.get() == "VHDL":
        design_dictionary["regex_message_find"] = main_window.regex_message_find_for_vhdl
    else:
        design_dictionary["regex_message_find"] = main_window.regex_message_find_for_verilog
    design_dictionary["regex_file_name_quote"] = main_window.regex_file_name_quote
    design_dictionary["regex_file_line_number_quote"] = main_window.regex_file_line_number_quote


def _save_canvas_data(design_dictionary: dict[str, Any]) -> None:
    design_dictionary["diagram_background_color"] = main_window.diagram_background_color.get()
    design_dictionary["state_number"] = state_handling.state_number
    design_dictionary["transition_number"] = transition_handling.transition_number
    design_dictionary["reset_entry_number"] = reset_entry_handling.reset_entry_number
    design_dictionary["connector_number"] = connector_handling.connector_number
    design_dictionary["conditionaction_id"] = condition_action_handling.ConditionAction.conditionaction_id
    design_dictionary["mytext_id"] = state_action_handling.MyText.mytext_id
    design_dictionary["global_actions_number"] = global_actions_handling.global_actions_clocked_number
    design_dictionary["state_actions_default_number"] = global_actions_handling.state_actions_default_number
    design_dictionary["global_actions_combinatorial_number"] = (
        global_actions_handling.global_actions_combinatorial_number
    )
    design_dictionary["state_radius"] = canvas_editing.state_radius
    design_dictionary["reset_entry_size"] = canvas_editing.reset_entry_size
    design_dictionary["priority_distance"] = canvas_editing.priority_distance
    design_dictionary["fontsize"] = canvas_editing.fontsize
    design_dictionary["label_fontsize"] = canvas_editing.label_fontsize
    design_dictionary["visible_center"] = canvas_editing.get_visible_center_as_string()
    design_dictionary["sash_positions"] = main_window.sash_positions
    design_dictionary["state"] = []
    design_dictionary["text"] = []
    design_dictionary["line"] = []
    design_dictionary["polygon"] = []
    design_dictionary["rectangle"] = []
    design_dictionary["window_state_action_block"] = []
    design_dictionary["window_state_comment"] = []
    design_dictionary["window_condition_action_block"] = []
    design_dictionary["window_global_actions"] = []
    design_dictionary["window_global_actions_combinatorial"] = []
    design_dictionary["window_state_actions_default"] = []

    items = main_window.canvas.find_all()
    for i in items:
        if main_window.canvas.type(i) == "oval":
            design_dictionary["state"].append(
                [main_window.canvas.coords(i), main_window.canvas.gettags(i), main_window.canvas.itemcget(i, "fill")]
            )
        elif main_window.canvas.type(i) == "text":
            design_dictionary["text"].append(
                [main_window.canvas.coords(i), main_window.canvas.gettags(i), main_window.canvas.itemcget(i, "text")]
            )
        elif main_window.canvas.type(i) == "line" and "grid_line" not in main_window.canvas.gettags(i):
            design_dictionary["line"].append([main_window.canvas.coords(i), main_window.canvas.gettags(i)])
        elif main_window.canvas.type(i) == "polygon":
            design_dictionary["polygon"].append([main_window.canvas.coords(i), main_window.canvas.gettags(i)])
        elif main_window.canvas.type(i) == "rectangle":
            design_dictionary["rectangle"].append([main_window.canvas.coords(i), main_window.canvas.gettags(i)])
        elif main_window.canvas.type(i) == "window":
            if i in state_action_handling.MyText.mytext_dict:
                design_dictionary["window_state_action_block"].append(
                    [
                        main_window.canvas.coords(i),
                        state_action_handling.MyText.mytext_dict[i].text_id.get("1.0", f"{tk.END}-1 chars"),
                        main_window.canvas.gettags(i),
                    ]
                )
            elif i in state_comment.StateComment.dictionary:
                design_dictionary["window_state_comment"].append(
                    [
                        main_window.canvas.coords(i),
                        state_comment.StateComment.dictionary[i].text_id.get("1.0", f"{tk.END}-1 chars"),
                        main_window.canvas.gettags(i),
                    ]
                )
            elif i in condition_action_handling.ConditionAction.dictionary:
                design_dictionary["window_condition_action_block"].append(
                    [
                        main_window.canvas.coords(i),
                        condition_action_handling.ConditionAction.dictionary[i].condition_id.get(
                            "1.0", f"{tk.END}-1 chars"
                        ),
                        condition_action_handling.ConditionAction.dictionary[i].action_id.get(
                            "1.0", f"{tk.END}-1 chars"
                        ),
                        main_window.canvas.gettags(i),
                    ]
                )
            elif i in global_actions.GlobalActions.dictionary:
                design_dictionary["window_global_actions"].append(
                    [
                        main_window.canvas.coords(i),
                        global_actions.GlobalActions.dictionary[i].text_before_id.get("1.0", f"{tk.END}-1 chars"),
                        global_actions.GlobalActions.dictionary[i].text_after_id.get("1.0", f"{tk.END}-1 chars"),
                        main_window.canvas.gettags(i),
                    ]
                )
            elif i in global_actions_combinatorial.GlobalActionsCombinatorial.dictionary:
                design_dictionary["window_global_actions_combinatorial"].append(
                    [
                        main_window.canvas.coords(i),
                        global_actions_combinatorial.GlobalActionsCombinatorial.dictionary[i].text_id.get(
                            "1.0", f"{tk.END}-1 chars"
                        ),
                        main_window.canvas.gettags(i),
                    ]
                )
            elif i in state_actions_default.StateActionsDefault.dictionary:
                design_dictionary["window_state_actions_default"].append(
                    [
                        main_window.canvas.coords(i),
                        state_actions_default.StateActionsDefault.dictionary[i].text_id.get("1.0", f"{tk.END}-1 chars"),
                        main_window.canvas.gettags(i),
                    ]
                )
            else:
                print("file_handling: Fatal, unknown dictionary key ", i)


def open_file_with_name_new(read_filename: str, is_script_mode: bool) -> None:
    replaced_read_filename = read_filename
    if os.path.isfile(f"{read_filename}.tmp") and not is_script_mode:
        answer = messagebox.askyesno(
            "HDL-FSM-Editor",
            f"Found BackUp-File\n{read_filename}.tmp\n"
            "This file remains after a HDL-FSM-Editor crash and contains all latest changes.\n"
            "Shall this file be read?",
        )
        if answer is True:
            replaced_read_filename = f"{read_filename}.tmp"
    main_window.root.config(cursor="watch")
    try:
        with open(replaced_read_filename, encoding="utf-8") as fileobject:
            data = fileobject.read()
        project_manager.current_file = read_filename
        design_dictionary = json.loads(data)
        _load_design_from_dict(design_dictionary)
        if os.path.isfile(f"{read_filename}.tmp") and not is_script_mode:
            os.remove(f"{read_filename}.tmp")

        # Final cleanup
        undo_handling.stack = []
        # Loading the design created by "traces" some stack-entries, which are removed here:
        undo_handling.stack_write_pointer = 0
        main_window.undo_button.config(state="disabled")

        # Put the read design into stack[0]:
        undo_handling.design_has_changed()  # Initialize the stack with the read design.
        main_window.root.update()
        dir_name, file_name = os.path.split(read_filename)
        main_window.root.title(f"{file_name} ({dir_name})")
        if not is_script_mode:
            update_ref = update_hdl_tab.UpdateHdlTab(
                design_dictionary["language"],
                design_dictionary["number_of_files"],
                read_filename,
                design_dictionary["generate_path"],
                design_dictionary["modulename"],
            )
            main_window.date_of_hdl_file_shown_in_hdl_tab = update_ref.get_date_of_hdl_file()
            main_window.date_of_hdl_file2_shown_in_hdl_tab = update_ref.get_date_of_hdl_file2()
            main_window.show_tab(GuiTab.DIAGRAM)
            main_window.root.after_idle(canvas_editing.view_all)
        main_window.root.config(cursor="arrow")
        if not tag_plausibility.TagPlausibility().get_tag_status_is_okay():
            if is_script_mode:
                print("Error, the database is corrupt. Do not use this file.")
            else:
                messagebox.showerror("Error", "The database is corrupt.\nDo not use this file.\nSee details at STDOUT.")
    except FileNotFoundError:
        main_window.root.config(cursor="arrow")
        if is_script_mode:
            print("Error: File " + read_filename + " could not be found.")
        else:
            messagebox.showerror("Error", f"File {read_filename} could not be found.")
    except ValueError:  # includes JSONDecodeError
        main_window.root.config(cursor="arrow")
        if is_script_mode:
            print("Error: File " + read_filename + " has wrong format.")
        else:
            messagebox.showerror("Error", f"File \n{read_filename}\nhas wrong format.")


def _load_design_from_dict(design_dictionary: dict[str, Any]) -> None:
    custom_text.CustomText.read_variables_of_all_windows.clear()
    custom_text.CustomText.written_variables_of_all_windows.clear()
    # Bring the notebook tab with the diagram into the foreground
    main_window.show_tab(GuiTab.DIAGRAM)

    _load_control_data(design_dictionary)
    _load_interface_data(design_dictionary)
    _load_internals_data(design_dictionary)
    _load_log_config(design_dictionary)
    _load_canvas_data(design_dictionary)
    _load_canvas_elements(design_dictionary)


def _load_control_data(design_dictionary: dict[str, Any]) -> None:
    """Load control data including module name, language, paths, and signal names."""
    main_window.module_name.set(design_dictionary["modulename"])
    old_language = main_window.language.get()
    main_window.language.set(design_dictionary["language"])
    if design_dictionary["language"] != old_language:
        main_window.switch_language_mode()
    main_window.generate_path_value.set(design_dictionary["generate_path"])
    main_window.additional_sources_value.set(design_dictionary.get("additional_sources", ""))
    main_window.working_directory_value.set(design_dictionary.get("working_directory", ""))
    # For Verilog and SystemVerilog, always use single file mode regardless of what's in the file
    if design_dictionary["language"] in ["Verilog", "SystemVerilog"]:
        main_window.select_file_number_text.set(1)
    else:
        main_window.select_file_number_text.set(design_dictionary["number_of_files"])
    main_window.reset_signal_name.set(design_dictionary["reset_signal_name"])
    main_window.clock_signal_name.set(design_dictionary["clock_signal_name"])
    main_window.compile_cmd.set(design_dictionary["compile_cmd"])
    main_window.edit_cmd.set(design_dictionary["edit_cmd"])
    main_window.include_timestamp_in_output.set(design_dictionary.get("include_timestamp_in_output", True))


def _load_interface_data(design_dictionary: dict[str, Any]) -> None:
    """Load interface data including package, generics, and ports text."""
    main_window.interface_package_text.insert("1.0", design_dictionary["interface_package"])
    main_window.interface_generics_text.insert("1.0", design_dictionary["interface_generics"])
    main_window.interface_ports_text.insert("1.0", design_dictionary["interface_ports"])

    # Update highlight tags and custom text class lists
    main_window.interface_package_text.update_highlight_tags(
        10, ["not_read", "not_written", "control", "datatype", "function", "comment"]
    )
    main_window.interface_generics_text.update_highlight_tags(
        10, ["not_read", "not_written", "control", "datatype", "function", "comment"]
    )
    main_window.interface_ports_text.update_highlight_tags(
        10, ["not_read", "not_written", "control", "datatype", "function", "comment"]
    )
    main_window.interface_generics_text.update_custom_text_class_generics_list()
    main_window.interface_ports_text.update_custom_text_class_ports_list()


def _load_internals_data(design_dictionary: dict[str, Any]) -> None:
    """Load internals data including package, architecture, and process text."""
    main_window.internals_package_text.insert("1.0", design_dictionary["internals_package"])
    main_window.internals_architecture_text.insert("1.0", design_dictionary["internals_architecture"])
    main_window.internals_process_clocked_text.insert("1.0", design_dictionary["internals_process"])
    main_window.internals_process_combinatorial_text.insert("1.0", design_dictionary["internals_process_combinatorial"])

    # Update highlight tags and custom text class lists
    main_window.internals_package_text.update_highlight_tags(
        10, ["not_read", "not_written", "control", "datatype", "function", "comment"]
    )
    main_window.internals_architecture_text.update_highlight_tags(
        10, ["not_read", "not_written", "control", "datatype", "function", "comment"]
    )
    main_window.internals_process_clocked_text.update_highlight_tags(
        10, ["not_read", "not_written", "control", "datatype", "function", "comment"]
    )
    main_window.internals_process_combinatorial_text.update_highlight_tags(
        10, ["not_read", "not_written", "control", "datatype", "function", "comment"]
    )
    main_window.internals_architecture_text.update_custom_text_class_signals_list()
    main_window.internals_process_clocked_text.update_custom_text_class_signals_list()
    main_window.internals_process_combinatorial_text.update_custom_text_class_signals_list()


def _load_log_config(design_dictionary: dict[str, Any]) -> None:
    """Load regex configuration for log parsing."""

    if "regex_message_find" in design_dictionary:
        if design_dictionary["language"] == "VHDL":
            main_window.regex_message_find_for_vhdl = design_dictionary["regex_message_find"]
        else:
            main_window.regex_message_find_for_verilog = design_dictionary["regex_message_find"]
        main_window.regex_file_name_quote = design_dictionary["regex_file_name_quote"]
        main_window.regex_file_line_number_quote = design_dictionary["regex_file_line_number_quote"]


def _load_canvas_data(design_dictionary: dict[str, Any]) -> None:
    """Load canvas-related data including colors, dimensions, and UI state."""
    # Load diagram background color
    main_window.diagram_background_color.set(design_dictionary.get("diagram_background_color", "white"))
    main_window.canvas.configure(bg=main_window.diagram_background_color.get())

    # Load sash positions
    if "sash_positions" in design_dictionary:
        main_window.show_tab(
            GuiTab.INTERFACE
        )  # The tab must be shown at least once, so that the sash_positions do not have the default-value 0.
        if (
            "1" in design_dictionary["sash_positions"]["interface_tab"]
            and design_dictionary["sash_positions"]["interface_tab"]["1"]
            < 0.9 * main_window.paned_window_interface.winfo_height()
        ):
            for key, value in design_dictionary["sash_positions"]["interface_tab"].items():
                if (
                    main_window.paned_window_interface.sashpos(0) != 0
                    and main_window.paned_window_interface.sashpos(0) != 1
                ):
                    main_window.paned_window_interface.sashpos(int(key), value)
                    main_window.sash_positions["interface_tab"][int(key)] = value
        main_window.show_tab(
            GuiTab.INTERNALS
        )  # The tab must be shown at least once, so that the sash_positions do not have the default-value 0.
        if (
            "2" in design_dictionary["sash_positions"]["internals_tab"]
            and design_dictionary["sash_positions"]["internals_tab"]["2"]
            < 0.9 * main_window.paned_window_internals.winfo_height()
        ):
            for key, value in design_dictionary["sash_positions"]["internals_tab"].items():
                if (
                    main_window.paned_window_internals.sashpos(0) != 0
                    and main_window.paned_window_internals.sashpos(0) != 1
                ):
                    main_window.paned_window_internals.sashpos(int(key), value)
                    main_window.sash_positions["internals_tab"][int(key)] = value

    # Load canvas editing parameters
    state_handling.state_number = design_dictionary["state_number"]
    transition_handling.transition_number = design_dictionary["transition_number"]
    reset_entry_handling.reset_entry_number = design_dictionary["reset_entry_number"]
    if reset_entry_handling.reset_entry_number == 0:
        main_window.reset_entry_button.config(state=tk.NORMAL)
    else:
        main_window.reset_entry_button.config(state=tk.DISABLED)
    connector_handling.connector_number = design_dictionary["connector_number"]
    condition_action_handling.ConditionAction.conditionaction_id = design_dictionary["conditionaction_id"]
    state_action_handling.MyText.mytext_id = design_dictionary["mytext_id"]
    global_actions_handling.global_actions_clocked_number = design_dictionary["global_actions_number"]
    if global_actions_handling.global_actions_clocked_number == 0:
        main_window.global_action_clocked_button.config(state=tk.NORMAL)
    else:
        main_window.global_action_clocked_button.config(state=tk.DISABLED)
    global_actions_handling.state_actions_default_number = design_dictionary["state_actions_default_number"]
    if global_actions_handling.state_actions_default_number == 0:
        main_window.state_action_default_button.config(state=tk.NORMAL)
    else:
        main_window.state_action_default_button.config(state=tk.DISABLED)
    global_actions_handling.global_actions_combinatorial_number = design_dictionary[
        "global_actions_combinatorial_number"
    ]
    if global_actions_handling.global_actions_combinatorial_number == 0:
        main_window.global_action_combinatorial_button.config(state=tk.NORMAL)
    else:
        main_window.global_action_combinatorial_button.config(state=tk.DISABLED)

    # Load canvas visual parameters
    canvas_editing.state_radius = design_dictionary["state_radius"]
    canvas_editing.reset_entry_size = int(design_dictionary["reset_entry_size"])  # stored as float in dictionary
    canvas_editing.priority_distance = int(design_dictionary["priority_distance"])  # stored as float in dictionary
    canvas_editing.fontsize = design_dictionary["fontsize"]
    assert canvas_editing.state_name_font is not None
    canvas_editing.state_name_font.configure(size=int(canvas_editing.fontsize))
    canvas_editing.label_fontsize = design_dictionary["label_fontsize"]
    canvas_editing.shift_visible_center_to_window_center(design_dictionary["visible_center"])


def _load_canvas_elements(design_dictionary: dict[str, Any]) -> None:
    """Load all canvas elements including states, transitions, text, and windows."""
    transition_ids: list[int] = []
    ids_of_rectangles_to_raise: list[int] = []
    priority_ids: list[int] = []
    hide_priority_rectangle_list: list[str] = []
    transition_identifier: str = ""

    # Load states
    for definition in design_dictionary["state"]:
        coords = definition[0]
        tags = definition[1]
        fill_color = definition[2] if len(definition) == 3 else constants.STATE_COLOR
        number_of_outgoing_transitions = 0
        for tag in tags:
            if tag.startswith("transition") and tag.endswith("_start"):
                transition_identifier = tag.replace("_start", "")
                number_of_outgoing_transitions += 1
        if number_of_outgoing_transitions == 1:
            hide_priority_rectangle_list.append(transition_identifier)
        state_handling.draw_state_circle(coords, fill_color, tags)

    # Load polygons (reset symbols)
    for definition in design_dictionary["polygon"]:
        coords = definition[0]
        tags = definition[1]
        reset_entry_handling.draw_reset_entry(coords, tags)
        number_of_outgoing_transitions = 0
        for tag in tags:
            if tag.startswith("transition") and tag.endswith("_start"):
                transition_identifier = tag.replace("_start", "")
                number_of_outgoing_transitions += 1
        if number_of_outgoing_transitions == 1:
            hide_priority_rectangle_list.append(transition_identifier)

    # Load text elements
    for definition in design_dictionary["text"]:
        coords = definition[0]
        tags = definition[1]
        text = definition[2]
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
        else:  # priority number
            for t in tags:
                if t.startswith("transition"):
                    transition_tag = t[:-8]
                    text_id = transition_handling.draw_priority_number(coords, text, tags, transition_tag)
                    priority_ids.append(text_id)

    # Load lines (transitions)
    for definition in design_dictionary["line"]:
        coords = definition[0]
        tags = definition[1]
        trans_id = None
        for t in tags:
            if t.startswith("connected_to_transition"):  # line to condition&action block
                trans_id = main_window.canvas.create_line(coords, dash=(2, 2), fill="black", tags=tags, state=tk.HIDDEN)
                break
            if t.startswith("connected_to_state") or t.endswith("_comment_line"):  # line to state action/comment
                trans_id = main_window.canvas.create_line(coords, dash=(2, 2), fill="black", tags=tags)
                break
            if t.startswith("transition"):
                trans_id = transition_handling.draw_transition(coords, tags)
                break
        if trans_id is not None:
            main_window.canvas.tag_lower(trans_id)  # Lines are always "under" anything else.

    # Load rectangles (connector, priority-box)
    for definition in design_dictionary["rectangle"]:
        coords = definition[0]
        tags = definition[1]
        is_priority_rectangle = True
        for t in tags:
            if t.startswith("connector"):
                is_priority_rectangle = False
        if is_priority_rectangle:  # priority rectangle
            rectangle_id = transition_handling.draw_priority_rectangle(coords, tags)
            ids_of_rectangles_to_raise.append(rectangle_id)
        else:
            connector_handling.draw_connector(coords, tags)
            number_of_outgoing_transitions = 0
            for tag in tags:
                if tag.startswith("transition") and tag.endswith("_start"):
                    transition_identifier = tag.replace("_start", "")
                    number_of_outgoing_transitions += 1
            if number_of_outgoing_transitions == 1:
                hide_priority_rectangle_list.append(transition_identifier)

    # Load window elements
    _load_window_elements(design_dictionary)

    # Sort the display order for the transition priorities:
    for transition_id in transition_ids:
        main_window.canvas.tag_raise(transition_id)
    for rectangle_id in ids_of_rectangles_to_raise:
        main_window.canvas.tag_raise(rectangle_id)
    for priority_id in priority_ids:
        main_window.canvas.tag_raise(priority_id)
    for transition_identifer in hide_priority_rectangle_list:
        main_window.canvas.itemconfigure(f"{transition_identifer}priority", state=tk.HIDDEN)
        main_window.canvas.itemconfigure(f"{transition_identifer}rectangle", state=tk.HIDDEN)


def _load_window_elements(design_dictionary: dict[str, Any]) -> None:
    """Load all window elements including state actions, comments, and global actions."""
    # Load state action blocks
    for definition in design_dictionary["window_state_action_block"]:
        coords = definition[0]
        text = definition[1]
        tags = definition[2]
        state_action_ref = state_action_handling.MyText(
            main_window.canvas, coords[0] - 100, coords[1], height=1, width=8, padding=1, increment=False
        )
        main_window.canvas.itemconfigure(state_action_ref.window_id, tags=tags)
        state_action_ref.text_content = text + "\n"
        state_action_ref.text_id.insert("1.0", text)
        state_action_ref.text_id.format()

    # Load state comments
    for definition in design_dictionary.get("window_state_comment", []):
        coords = definition[0]
        text = definition[1]
        tags = definition[2]
        comment_ref = state_comment.StateComment(
            main_window.canvas, coords[0] - 100, coords[1], height=1, width=8, padding=1
        )
        main_window.canvas.itemconfigure(comment_ref.window_id, tags=tags)
        comment_ref.text_content = text + "\n"
        comment_ref.text_id.insert("1.0", text)
        comment_ref.text_id.format()

    # Load condition action blocks
    for definition in design_dictionary["window_condition_action_block"]:
        coords = definition[0]
        condition = definition[1]
        action = definition[2]
        tags = definition[3]
        connected_to_reset_entry = False
        for t in tags:
            if t == "connected_to_reset_transition":
                connected_to_reset_entry = True
        condition_action_ref = condition_action_handling.ConditionAction(
            main_window.canvas,
            coords[0],
            coords[1],
            connected_to_reset_entry,
            height=1,
            width=8,
            padding=1,
            increment=False,
        )
        main_window.canvas.itemconfigure(condition_action_ref.window_id, tags=tags)
        condition_action_ref.condition_id.condition_text = condition + "\n"
        condition_action_ref.condition_id.insert("1.0", condition)
        condition_action_ref.condition_id.format()
        condition_action_ref.action_id.action_text = action + "\n"
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

    # Load global actions
    for definition in design_dictionary["window_global_actions"]:
        coords = definition[0]
        text_before = definition[1]
        text_after = definition[2]
        tags = definition[3]
        global_actions_ref = global_actions.GlobalActions(
            main_window.canvas, coords[0], coords[1], height=1, width=8, padding=1
        )
        main_window.canvas.itemconfigure(global_actions_ref.window_id, tags=tags)
        global_actions_ref.text_before_id.text_before_content = text_before + "\n"
        global_actions_ref.text_before_id.insert("1.0", text_before)
        global_actions_ref.text_before_id.format()
        global_actions_ref.text_after_id.text_after_content = text_after + "\n"
        global_actions_ref.text_after_id.insert("1.0", text_after)
        global_actions_ref.text_after_id.format()

    # Load global actions combinatorial
    for definition in design_dictionary["window_global_actions_combinatorial"]:
        coords = definition[0]
        text = definition[1]
        tags = definition[2]
        global_action_ref = global_actions_combinatorial.GlobalActionsCombinatorial(
            main_window.canvas, coords[0], coords[1], height=1, width=8, padding=1
        )
        main_window.canvas.itemconfigure(global_action_ref.window_id, tags=tags)
        global_action_ref.text_content = text + "\n"
        global_action_ref.text_id.insert("1.0", text)
        global_action_ref.text_id.format()

    # Load state actions default
    for definition in design_dictionary["window_state_actions_default"]:
        coords = definition[0]
        text = definition[1]
        tags = definition[2]
        state_action_default_ref = state_actions_default.StateActionsDefault(
            main_window.canvas, coords[0], coords[1], height=1, width=8, padding=1
        )
        main_window.canvas.itemconfigure(state_action_default_ref.window_id, tags=tags)
        state_action_default_ref.text_content = text + "\n"
        state_action_default_ref.text_id.insert("1.0", text)
        state_action_default_ref.text_id.format()
