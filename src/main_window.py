"""
This module contains all methods to create the main-window of the HDL-FSM-Editor.
"""

import os
import re
import sys
import tkinter as tk
import urllib.error
import urllib.request
from pathlib import Path
from tkinter import messagebox, ttk
from tkinter.filedialog import askdirectory, askopenfilename

import canvas_delete
import canvas_editing
import canvas_modify_bindings
import compile_handling
import constants
import custom_text
import file_handling
import find_replace
import grid_drawing
import link_dictionary
import linting
import move_handling_initialization
import undo_handling
import update_hdl_tab
from codegen import hdl_generation
from codegen.hdl_generation_config import GenerationConfig
from constants import GuiTab
from dialogs.color_changer import ColorChanger
from dialogs.regex_dialog import RegexDialog
from project_manager import project_manager

_check_version_result: str = ""  # wird nur in main_window.py verwendet, kann in Attribut umgewandelt werden
_select_file_number_radio_button1 = 0  # wird nur in main_window.py verwendet, kann in Attribut umgewandelt werden
_select_file_number_radio_button2 = 0  # wird nur in main_window.py verwendet, kann in Attribut umgewandelt werden
_interface_package_frame: ttk.Frame  # wird nur in main_window.py verwendet, kann in Attribut umgewandelt werden
_internals_package_frame: ttk.Frame  # wird nur in main_window.py verwendet, kann in Attribut umgewandelt werden
paned_window_interface: ttk.PanedWindow  # wird nur in main_window.py verwendet, kann in Attribut umgewandelt werden
paned_window_internals: ttk.PanedWindow  # wird nur in main_window.py verwendet, kann in Attribut umgewandelt werden
_debug_active: tk.IntVar  # wird nur in main_window.py verwendet, kann in Attribut umgewandelt werden
_regex_error_happened: bool = False  # wird nur in main_window.py verwendet, kann in Attribut umgewandelt werden
_line_number_under_pointer_log_tab: int = 0  # wird nur in main_window.py verwendet, kann in Attribut umgewandelt werden
_line_number_under_pointer_hdl_tab: int = 0  # wird nur in main_window.py verwendet, kann in Attribut umgewandelt werden
_func_id_jump1: str | None = None  # wird nur in main_window.py verwendet, kann in Attribut umgewandelt werden
_func_id_jump2: str | None = None  # wird nur in main_window.py verwendet, kann in Attribut umgewandelt werden
_func_id_jump: str | None = None  # wird nur in main_window.py verwendet, kann in Attribut umgewandelt werden


def read_message() -> None:
    try:
        source = urllib.request.urlopen("http://www.hdl-fsm-editor.de/message.txt")
        message = source.read()
        _read_message_result = message.decode()
    except urllib.error.URLError:
        _read_message_result = "No message was found."
    except ConnectionRefusedError:
        _read_message_result = ""
    print(_read_message_result)
    _copy_message_into_log_tab(_read_message_result)


def _copy_message_into_log_tab(_read_message_result) -> None:
    project_manager.log_frame_text.config(state=tk.NORMAL)
    project_manager.log_frame_text.insert(
        "1.0", constants.header_string + "\n" + _check_version_result + "\n" + _read_message_result + "\n"
    )
    project_manager.log_frame_text.config(state=tk.NORMAL)


def check_version() -> None:
    global _check_version_result
    try:
        print("Checking for a newer version ...")
        source = urllib.request.urlopen("http://www.hdl-fsm-editor.de/index.php")
        website_source = str(source.read())
        version_start = website_source.find("Version")
        new_version = website_source[version_start : version_start + 24]
        end_index = new_version.find("(")
        new_version = new_version[:end_index]
        new_version = re.sub(" ", "", new_version)
        if new_version != "Version" + constants.VERSION:
            _check_version_result = (
                "Please update to the new version of HDL-FSM-Editor available at http://www.hdl-fsm-editor.de"
            )
        else:
            _check_version_result = "Your version of HDL-FSM-Editor is up to date."
    except urllib.error.URLError:
        _check_version_result = "HDL-FSM-Editor version could not be checked, as you are offline."
    print(_check_version_result)


def show_window() -> None:
    project_manager.root.wm_deiconify()


def _close_tool() -> None:
    title = project_manager.root.title()
    if title.endswith("*"):
        action = file_handling.ask_save_unsaved_changes(title)
        if action == "cancel":
            return
        elif action == "save":
            file_handling.save()
            # Check if save was successful (current_file is not empty)
            if project_manager.current_file == "":
                return
    if os.path.isfile(project_manager.current_file + ".tmp"):
        os.remove(project_manager.current_file + ".tmp")
    sys.exit()


def _get_resource_path(resource_name: str) -> Path:
    """Get the path to a resource file, handling both development and PyInstaller environments."""
    base_path = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).parent.parent

    return base_path / "rsc" / resource_name


def create_root() -> None:
    root = tk.Tk()
    root.withdraw()  # Because it could be batch-mode because of "-generate_hdl" switch.
    project_manager.root = root

    # Set the application icon
    try:
        icon_path = _get_resource_path("hfe_icon.ico")
        if icon_path.exists():
            root.iconbitmap(icon_path)
        else:
            print(f"Warning: Icon file not found at {icon_path}")
    except Exception as e:
        print(f"Warning: Could not set application icon: {e}")

    # Configure the grid field where the notebook will be placed in, so that the notebook is resized at window resize:
    root.columnconfigure(0, weight=1)
    root.rowconfigure(1, weight=1)
    root.grid()
    root.protocol("WM_DELETE_WINDOW", _close_tool)
    # init_link_dict(root)
    project_manager.link_dict_ref = link_dictionary.LinkDictionary(root)


def _capslock_warning(character):
    messagebox.showwarning(
        "Warning in HDL-FSM-Editor",
        "The character " + character + " is not bound to any action.\nPerhaps Capslock is active?",
    )


def create_notebook() -> None:
    notebook = ttk.Notebook(project_manager.root, padding=5)
    project_manager.notebook = notebook
    notebook.grid(column=0, row=1, sticky="nsew")


def create_control_notebook_tab() -> None:
    global _select_file_number_radio_button1, _select_file_number_radio_button2
    control_frame = ttk.Frame(project_manager.notebook, takefocus=False)
    control_frame.grid(sticky=(tk.W, tk.E))
    control_frame.columnconfigure(0, weight=0)  # column contains the labels.
    control_frame.columnconfigure(1, weight=1)  # column contains the entry boxes.
    control_frame.columnconfigure(2, weight=0)  # column contains the buttons.

    module_name = tk.StringVar()
    project_manager.module_name = module_name
    module_name.set("")
    module_name_label = ttk.Label(control_frame, text="Module-Name:", padding=5)
    _module_name_entry = ttk.Entry(control_frame, textvariable=module_name)
    module_name_label.grid(row=0, column=0, sticky=tk.W)
    _module_name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
    _module_name_entry.select_clear()

    language = tk.StringVar()
    project_manager.language = language
    language.set("VHDL")
    language_label = ttk.Label(control_frame, text="Language:", padding=5)
    language_combobox = ttk.Combobox(
        control_frame, textvariable=language, values=("VHDL", "Verilog", "SystemVerilog"), state="readonly"
    )
    language_combobox.bind("<<ComboboxSelected>>", lambda event: switch_language_mode())
    language_label.grid(row=1, column=0, sticky=tk.W)
    language_combobox.grid(row=1, column=1, sticky=tk.W)

    generate_path_value = tk.StringVar(value="")
    project_manager.generate_path_value = generate_path_value
    generate_path_value.trace_add("write", _show_path_has_changed)
    generate_path_label = ttk.Label(control_frame, text="Directory for generated HDL:", padding=5)
    _generate_path_entry = ttk.Entry(control_frame, textvariable=generate_path_value, width=80)
    generate_path_button = ttk.Button(control_frame, text="Select...", command=_set_path, style="Path.TButton")
    generate_path_label.grid(row=2, column=0, sticky=tk.W)
    _generate_path_entry.grid(row=2, column=1, sticky="ew")
    generate_path_button.grid(row=2, column=2, sticky="ew")

    _select_file_number_label = ttk.Label(control_frame, text="Generation attributes:", padding=5)
    _select_file_number_frame = ttk.Frame(control_frame)
    _select_file_number_label.grid(row=3, column=0, sticky=tk.W)
    _select_file_number_frame.grid(row=3, column=1, sticky=(tk.W, tk.E))

    select_file_number_text = tk.IntVar()
    project_manager.select_file_number_text = select_file_number_text
    select_file_number_text.set(2)
    _select_file_number_radio_button1 = ttk.Radiobutton(
        _select_file_number_frame, takefocus=False, variable=select_file_number_text, text="1 file", value=1
    )
    _select_file_number_radio_button2 = ttk.Radiobutton(
        _select_file_number_frame, takefocus=False, variable=select_file_number_text, text="2 files", value=2
    )
    include_timestamp_in_output = tk.BooleanVar(value=True)
    project_manager.include_timestamp_in_output = include_timestamp_in_output
    include_timestamp_in_output.trace_add("write", lambda *args: undo_handling.update_window_title())
    include_timestamp_checkbox = ttk.Checkbutton(_select_file_number_frame, variable=include_timestamp_in_output)
    include_timestamp_label = ttk.Label(
        _select_file_number_frame, text="Include timestamp in generated HDL files", width=40
    )
    include_timestamp_checkbox.grid(row=0, column=0, sticky=tk.W)
    include_timestamp_label.grid(row=0, column=1, sticky=tk.W)
    _select_file_number_radio_button1.grid(row=0, column=2, sticky=tk.W)
    _select_file_number_radio_button2.grid(row=0, column=3, sticky=tk.W)

    reset_signal_name = tk.StringVar()
    project_manager.reset_signal_name = reset_signal_name
    reset_signal_name.set("")
    reset_signal_name_label = ttk.Label(control_frame, text="Name of asynchronous reset input port:", padding=5)
    _reset_signal_name_entry = ttk.Entry(control_frame, width=23, textvariable=reset_signal_name)
    _reset_signal_name_entry.bind("<Key>", lambda event: undo_handling.update_window_title())
    reset_signal_name_label.grid(row=4, column=0, sticky=tk.W)
    _reset_signal_name_entry.grid(row=4, column=1, sticky=tk.W)

    clock_signal_name = tk.StringVar()
    project_manager.clock_signal_name = clock_signal_name
    clock_signal_name.set("")
    clock_signal_name_label = ttk.Label(control_frame, text="Name of clock input port:", padding=5)
    _clock_signal_name_entry = ttk.Entry(control_frame, width=23, textvariable=clock_signal_name)
    _clock_signal_name_entry.bind("<Key>", lambda event: undo_handling.update_window_title())
    clock_signal_name_label.grid(row=5, column=0, sticky=tk.W)
    _clock_signal_name_entry.grid(row=5, column=1, sticky=tk.W)

    compile_cmd = tk.StringVar()
    project_manager.compile_cmd = compile_cmd
    compile_cmd.set("ghdl -a $file1 $file2; ghdl -e $name; ghdl -r $name")
    compile_cmd_label = ttk.Label(control_frame, text="Compile command:", padding=5)
    _compile_cmd_entry = ttk.Entry(control_frame, width=23, textvariable=compile_cmd)
    compile_cmd_label.grid(row=6, column=0, sticky=tk.W)
    _compile_cmd_entry.grid(row=6, column=1, sticky="ew")

    _compile_cmd_docu = ttk.Label(
        control_frame,
        text="Variables for compile command:\n$file1\t= Entity-File\n$file2\t= Architecture-File\n$file\t\
= File with Entity and Architecture\n$name\t= Module Name",
        padding=5,
    )
    project_manager.compile_cmd_docu = _compile_cmd_docu
    project_manager.compile_cmd_docu.grid(row=7, column=1, sticky=tk.W)

    edit_cmd = tk.StringVar()
    project_manager.edit_cmd = edit_cmd
    edit_cmd.set("C:/Program Files/Notepad++/notepad++.exe -nosession -multiInst")
    edit_cmd_label = ttk.Label(control_frame, text="Edit command (executed by Ctrl+e):", padding=5)
    _edit_cmd_entry = ttk.Entry(control_frame, width=23, textvariable=edit_cmd)
    edit_cmd_label.grid(row=8, column=0, sticky=tk.W)
    _edit_cmd_entry.grid(row=8, column=1, sticky="ew")

    additional_sources_value = tk.StringVar(value="")
    project_manager.additional_sources_value = additional_sources_value
    additional_sources_value.trace_add("write", _show_path_has_changed)
    additional_sources_label = ttk.Label(
        control_frame,
        text="Additional sources:\n(used only by HDL-SCHEM-Editor, must\nbe added manually to compile command)",
        padding=5,
    )
    _additional_sources_entry = ttk.Entry(control_frame, textvariable=additional_sources_value, width=80)
    additional_sources_button = ttk.Button(control_frame, text="Select...", command=__add_path, style="Path.TButton")
    additional_sources_label.grid(row=9, column=0, sticky=tk.W)
    _additional_sources_entry.grid(row=9, column=1, sticky=(tk.W, tk.E))
    additional_sources_button.grid(row=9, column=2, sticky=(tk.W, tk.E))

    working_directory_value = tk.StringVar(value="")
    project_manager.working_directory_value = working_directory_value
    working_directory_value.trace_add("write", _show_path_has_changed)
    working_directory_label = ttk.Label(control_frame, text="Working directory:", padding=5)
    _working_directory_entry = ttk.Entry(control_frame, textvariable=working_directory_value, width=80)
    working_directory_button = ttk.Button(
        control_frame, text="Select...", command=_set_working_directory, style="Path.TButton"
    )
    working_directory_label.grid(row=10, column=0, sticky=tk.W)
    _working_directory_entry.grid(row=10, column=1, sticky="ew")
    working_directory_button.grid(row=10, column=2, sticky="ew")

    diagram_background_color = tk.StringVar(value="white")
    project_manager.diagram_background_color = diagram_background_color
    diagram_background_color.trace_add("write", lambda *args: _change_color_of_diagram_background())
    diagram_background_color_label = ttk.Label(control_frame, text="Diagram background color:", padding=5)
    diagram_background_color_entry = ttk.Entry(control_frame, textvariable=diagram_background_color, width=80)
    diagram_background_color_button = ttk.Button(
        control_frame, text="Choose color...", command=choose_bg_color, style="Path.TButton"
    )
    diagram_background_color_label.grid(row=11, column=0, sticky=tk.W)
    diagram_background_color_entry.grid(row=11, column=1, sticky="ew")
    diagram_background_color_button.grid(row=11, column=2, sticky="ew")
    _diagram_background_color_error = ttk.Label(control_frame, text="", padding=5)
    project_manager._diagram_background_color_error = _diagram_background_color_error
    _diagram_background_color_error.grid(row=12, column=1, sticky=tk.W)

    project_manager.notebook.add(control_frame, sticky="nsew", text=GuiTab.CONTROL.value)

    project_manager.entry_widgets = [
        {"stringvar": module_name, "entry": _module_name_entry},
        {"stringvar": generate_path_value, "entry": _generate_path_entry},
        {"stringvar": reset_signal_name, "entry": _reset_signal_name_entry},
        {"stringvar": clock_signal_name, "entry": _clock_signal_name_entry},
        {"stringvar": compile_cmd, "entry": _compile_cmd_entry},
        {"stringvar": edit_cmd, "entry": _edit_cmd_entry},
        {"stringvar": additional_sources_value, "entry": _additional_sources_entry},
        {"stringvar": working_directory_value, "entry": _working_directory_entry},
    ]


def _set_path() -> None:
    path = askdirectory(title="Select directory for generated HDL")
    if path != "" and not path.isspace():
        project_manager.generate_path_value.set(path)


def __add_path():
    old_entry = project_manager.additional_sources_value.get()
    if old_entry != "":
        old_entries = old_entry.split(",")
        path = askopenfilename(initialdir=os.path.dirname(old_entries[0]))
    else:
        path = askopenfilename()
    if path != "":
        if old_entry == "":
            project_manager.additional_sources_value.set(path)
        else:
            project_manager.additional_sources_value.set(old_entry + ", " + path)


def _set_working_directory() -> None:
    path = askdirectory()
    if path != "" and not path.isspace():
        project_manager.working_directory_value.set(path)


def create_interface_notebook_tab() -> None:
    global paned_window_interface, _interface_package_frame

    paned_window_interface = ttk.PanedWindow(project_manager.notebook, orient=tk.VERTICAL, takefocus=True)

    _interface_package_frame = ttk.Frame(paned_window_interface)
    _interface_package_frame.columnconfigure(0, weight=1)
    _interface_package_frame.columnconfigure(1, weight=0)
    _interface_package_frame.rowconfigure(0, weight=0)
    _interface_package_frame.rowconfigure(1, weight=1)
    _interface_package_label = ttk.Label(_interface_package_frame, text="Packages:", padding=5)
    interface_package_info = ttk.Label(_interface_package_frame, text="Undo/Redo: Ctrl-z/Ctrl-Z,Ctrl-y", padding=5)
    interface_package_text = custom_text.CustomText(
        _interface_package_frame, text_type="package", height=3, width=10, undo=True, font=("Courier", 10)
    )
    project_manager.interface_package_text = interface_package_text
    interface_package_text.insert("1.0", "library ieee;\nuse ieee.std_logic_1164.all;")
    interface_package_text.update_highlight_tags(
        10, ["not_read", "not_written", "control", "datatype", "function", "comment"]
    )
    interface_package_text.bind("<Control-Z>", lambda event: interface_package_text.edit_redo())
    interface_package_text.bind("<Control-e>", lambda event: interface_package_text.edit_in_external_editor())
    interface_package_text.bind("<<TextModified>>", lambda event: undo_handling.update_window_title())
    _interface_package_scroll = ttk.Scrollbar(
        _interface_package_frame, orient=tk.VERTICAL, cursor="arrow", command=interface_package_text.yview
    )
    interface_package_text.config(yscrollcommand=_interface_package_scroll.set)
    _interface_package_label.grid(row=0, column=0, sticky="wns")
    interface_package_info.grid(row=0, column=0, sticky=tk.E)
    interface_package_text.grid(row=1, column=0, sticky="nsew")
    _interface_package_scroll.grid(row=1, column=1, sticky="nsew")
    paned_window_interface.add(_interface_package_frame, weight=1)

    interface_generics_frame = ttk.Frame(paned_window_interface)
    interface_generics_frame.columnconfigure(0, weight=1)
    interface_generics_frame.columnconfigure(1, weight=0)
    interface_generics_frame.rowconfigure(0, weight=0)
    interface_generics_frame.rowconfigure(1, weight=1)
    _interface_generics_label = ttk.Label(interface_generics_frame, text="Generics:", padding=5)
    project_manager.interface_generics_label = _interface_generics_label
    interface_generics_info = ttk.Label(interface_generics_frame, text="Undo/Redo: Ctrl-z/Ctrl-Z,Ctrl-y", padding=5)
    interface_generics_text = custom_text.CustomText(
        interface_generics_frame, text_type="generics", height=3, width=10, undo=True, font=("Courier", 10)
    )
    project_manager.interface_generics_text = interface_generics_text
    interface_generics_text.bind("<Control-Z>", lambda event: interface_generics_text.edit_redo())
    interface_generics_text.bind("<Control-e>", lambda event: interface_generics_text.edit_in_external_editor())
    interface_generics_text.bind("<<TextModified>>", lambda event: undo_handling.update_window_title())
    interface_generics_scroll = ttk.Scrollbar(
        interface_generics_frame, orient=tk.VERTICAL, cursor="arrow", command=interface_generics_text.yview
    )
    interface_generics_text.config(yscrollcommand=interface_generics_scroll.set)
    _interface_generics_label.grid(row=0, column=0, sticky="wns")
    interface_generics_info.grid(row=0, column=0, sticky=tk.E)
    interface_generics_text.grid(row=1, column=0, sticky="nsew")
    interface_generics_scroll.grid(row=1, column=1, sticky="nsew")
    paned_window_interface.add(interface_generics_frame, weight=1)

    interface_ports_frame = ttk.Frame(paned_window_interface)
    interface_ports_frame.columnconfigure(0, weight=1)
    interface_ports_frame.columnconfigure(1, weight=0)
    interface_ports_frame.rowconfigure(0, weight=0)
    interface_ports_frame.rowconfigure(1, weight=1)
    _interface_ports_label = ttk.Label(interface_ports_frame, text="Ports:", padding=5)
    project_manager.interface_ports_label = _interface_ports_label
    interface_ports_info = ttk.Label(interface_ports_frame, text="Undo/Redo: Ctrl-z/Ctrl-Z,Ctrl-y", padding=5)
    interface_ports_text = custom_text.CustomText(
        interface_ports_frame, text_type="ports", height=3, width=10, undo=True, font=("Courier", 10)
    )
    project_manager.interface_ports_text = interface_ports_text
    interface_ports_text.bind("<Control-z>", lambda event: interface_ports_text.undo())
    interface_ports_text.bind("<Control-Z>", lambda event: interface_ports_text.redo())
    interface_ports_text.bind("<Control-e>", lambda event: interface_ports_text.edit_in_external_editor())
    interface_ports_text.bind("<<TextModified>>", lambda event: undo_handling.update_window_title())
    interface_ports_scroll = ttk.Scrollbar(
        interface_ports_frame, orient=tk.VERTICAL, cursor="arrow", command=interface_ports_text.yview
    )
    interface_ports_text.config(yscrollcommand=interface_ports_scroll.set)
    _interface_ports_label.grid(row=0, column=0, sticky=tk.W)
    interface_ports_info.grid(row=0, column=0, sticky=tk.E)
    interface_ports_text.grid(row=1, column=0, sticky="nsew")
    interface_ports_scroll.grid(row=1, column=1, sticky="nsew")
    paned_window_interface.add(interface_ports_frame, weight=1)

    project_manager.notebook.add(paned_window_interface, sticky="nsew", text=GuiTab.INTERFACE.value)


def create_internals_notebook_tab() -> None:
    global paned_window_internals, _internals_package_frame

    paned_window_internals = ttk.PanedWindow(project_manager.notebook, orient=tk.VERTICAL, takefocus=True)

    _internals_package_frame = ttk.Frame(paned_window_internals)
    _internals_package_frame.columnconfigure(0, weight=1)
    _internals_package_frame.columnconfigure(1, weight=0)
    _internals_package_frame.rowconfigure(0, weight=0)
    _internals_package_frame.rowconfigure(1, weight=1)
    _internals_package_label = ttk.Label(_internals_package_frame, text="Packages:", padding=5)
    interface_package_info = ttk.Label(_internals_package_frame, text="Undo/Redo: Ctrl-z/Ctrl-Z,Ctrl-y", padding=5)
    internals_package_text = custom_text.CustomText(
        _internals_package_frame, text_type="package", height=3, width=10, undo=True, font=("Courier", 10)
    )
    project_manager.internals_package_text = internals_package_text
    internals_package_text.bind("<Control-Z>", lambda event: internals_package_text.edit_redo())
    internals_package_text.bind("<Control-e>", lambda event: internals_package_text.edit_in_external_editor())
    internals_package_text.bind("<<TextModified>>", lambda event: undo_handling.update_window_title())
    _internals_package_scroll = ttk.Scrollbar(
        _internals_package_frame, orient=tk.VERTICAL, cursor="arrow", command=internals_package_text.yview
    )
    internals_package_text.config(yscrollcommand=_internals_package_scroll.set)
    _internals_package_label.grid(row=0, column=0, sticky=tk.W)
    interface_package_info.grid(row=0, column=0, sticky=tk.E)
    internals_package_text.grid(row=1, column=0, sticky="nsew")
    _internals_package_scroll.grid(row=1, column=1, sticky="nsew")
    paned_window_internals.add(_internals_package_frame, weight=1)

    internals_architecture_frame = ttk.Frame(paned_window_internals)
    internals_architecture_frame.columnconfigure(0, weight=1)
    internals_architecture_frame.columnconfigure(1, weight=0)
    internals_architecture_frame.rowconfigure(0, weight=0)
    internals_architecture_frame.rowconfigure(1, weight=1)
    _internals_architecture_label = ttk.Label(
        internals_architecture_frame, text="Architecture Declarations:", padding=5
    )
    project_manager.internals_architecture_label = _internals_architecture_label
    interface_architecture_info = ttk.Label(
        internals_architecture_frame, text="Undo/Redo: Ctrl-z/Ctrl-Z,Ctrl-y", padding=5
    )
    internals_architecture_text = custom_text.CustomText(
        internals_architecture_frame, text_type="declarations", height=3, width=10, undo=True, font=("Courier", 10)
    )
    project_manager.internals_architecture_text = internals_architecture_text
    internals_architecture_text.bind("<Control-z>", lambda event: internals_architecture_text.undo())
    internals_architecture_text.bind("<Control-Z>", lambda event: internals_architecture_text.redo())
    internals_architecture_text.bind("<Control-e>", lambda event: internals_architecture_text.edit_in_external_editor())
    internals_architecture_text.bind("<<TextModified>>", lambda event: undo_handling.update_window_title())
    internals_architecture_scroll = ttk.Scrollbar(
        internals_architecture_frame, orient=tk.VERTICAL, cursor="arrow", command=internals_architecture_text.yview
    )
    internals_architecture_text.config(yscrollcommand=internals_architecture_scroll.set)
    _internals_architecture_label.grid(row=0, column=0, sticky=tk.W)
    interface_architecture_info.grid(row=0, column=0, sticky=tk.E)
    internals_architecture_text.grid(row=1, column=0, sticky="nsew")
    internals_architecture_scroll.grid(row=1, column=1, sticky="nsew")
    paned_window_internals.add(internals_architecture_frame, weight=1)

    internals_process_clocked_frame = ttk.Frame(paned_window_internals)
    internals_process_clocked_frame.columnconfigure(0, weight=1)
    internals_process_clocked_frame.columnconfigure(1, weight=0)
    internals_process_clocked_frame.rowconfigure(0, weight=0)
    internals_process_clocked_frame.rowconfigure(1, weight=1)
    _internals_process_clocked_label = ttk.Label(
        internals_process_clocked_frame, text="Variable Declarations for clocked process:", padding=5
    )
    project_manager.internals_process_clocked_label = _internals_process_clocked_label
    interface_process_clocked_info = ttk.Label(
        internals_process_clocked_frame, text="Undo/Redo: Ctrl-z/Ctrl-Z,Ctrl-y", padding=5
    )
    internals_process_clocked_text = custom_text.CustomText(
        internals_process_clocked_frame, text_type="variable", height=3, width=10, undo=True, font=("Courier", 10)
    )
    project_manager.internals_process_clocked_text = internals_process_clocked_text
    internals_process_clocked_text.bind("<Control-z>", lambda event: internals_process_clocked_text.undo())
    internals_process_clocked_text.bind("<Control-Z>", lambda event: internals_process_clocked_text.redo())
    internals_process_clocked_text.bind(
        "<Control-e>", lambda event: internals_process_clocked_text.edit_in_external_editor()
    )
    internals_process_clocked_text.bind("<<TextModified>>", lambda event: undo_handling.update_window_title())
    internals_process_clocked_scroll = ttk.Scrollbar(
        internals_process_clocked_frame,
        orient=tk.VERTICAL,
        cursor="arrow",
        command=internals_process_clocked_text.yview,
    )
    internals_process_clocked_text.config(yscrollcommand=internals_process_clocked_scroll.set)
    _internals_process_clocked_label.grid(row=0, column=0, sticky=tk.W)
    interface_process_clocked_info.grid(row=0, column=0, sticky=tk.E)
    internals_process_clocked_text.grid(row=1, column=0, sticky="nsew")
    internals_process_clocked_scroll.grid(row=1, column=1, sticky="nsew")
    paned_window_internals.add(internals_process_clocked_frame, weight=1)

    internals_process_combinatorial_frame = ttk.Frame(paned_window_internals)
    internals_process_combinatorial_frame.columnconfigure(0, weight=1)
    internals_process_combinatorial_frame.columnconfigure(1, weight=0)
    internals_process_combinatorial_frame.rowconfigure(0, weight=0)
    internals_process_combinatorial_frame.rowconfigure(1, weight=1)
    _internals_process_combinatorial_label = ttk.Label(
        internals_process_combinatorial_frame, text="Variable Declarations for combinatorial process:", padding=5
    )
    project_manager.internals_process_combinatorial_label = _internals_process_combinatorial_label
    interface_process_combinatorial_info = ttk.Label(
        internals_process_combinatorial_frame, text="Undo/Redo: Ctrl-z/Ctrl-Z,Ctrl-y", padding=5
    )
    internals_process_combinatorial_text = custom_text.CustomText(
        internals_process_combinatorial_frame, text_type="variable", height=3, width=10, undo=True, font=("Courier", 10)
    )
    project_manager.internals_process_combinatorial_text = internals_process_combinatorial_text
    internals_process_combinatorial_text.bind("<Control-z>", lambda event: internals_process_combinatorial_text.undo())
    internals_process_combinatorial_text.bind("<Control-Z>", lambda event: internals_process_combinatorial_text.redo())
    internals_process_combinatorial_text.bind(
        "<Control-e>", lambda event: internals_process_combinatorial_text.edit_in_external_editor()
    )
    internals_process_combinatorial_text.bind("<<TextModified>>", lambda event: undo_handling.update_window_title())
    internals_process_combinatorial_scroll = ttk.Scrollbar(
        internals_process_combinatorial_frame,
        orient=tk.VERTICAL,
        cursor="arrow",
        command=internals_process_combinatorial_text.yview,
    )
    internals_process_combinatorial_text.config(yscrollcommand=internals_process_combinatorial_scroll.set)
    _internals_process_combinatorial_label.grid(row=0, column=0, sticky=tk.W)
    interface_process_combinatorial_info.grid(row=0, column=0, sticky=tk.E)
    internals_process_combinatorial_text.grid(row=1, column=0, sticky="nsew")
    internals_process_combinatorial_scroll.grid(row=1, column=1, sticky="nsew")
    paned_window_internals.add(internals_process_combinatorial_frame, weight=1)

    project_manager.notebook.add(paned_window_internals, sticky="nsew", text=GuiTab.INTERNALS.value)


def create_diagram_notebook_tab() -> None:
    diagram_frame = ttk.Frame(project_manager.notebook, borderwidth=0, relief="flat")
    diagram_frame.grid()
    diagram_frame.columnconfigure(0, weight=1)  # tkinter method (grid_columnconfigure is tcl method)
    diagram_frame.rowconfigure(0, weight=1)
    project_manager.notebook.add(diagram_frame, sticky="nsew", text=GuiTab.DIAGRAM.value)
    # Create the elements of the drawing area:
    h = ttk.Scrollbar(diagram_frame, orient=tk.HORIZONTAL, cursor="arrow", style="Horizontal.TScrollbar")
    v = ttk.Scrollbar(diagram_frame, orient=tk.VERTICAL, cursor="arrow")
    canvas = tk.Canvas(
        diagram_frame,
        borderwidth=2,
        bg="white",
        scrollregion=(-100000, -100000, 100000, 100000),
        xscrollcommand=h.set,
        yscrollcommand=v.set,
        highlightthickness=0,
        relief=tk.SUNKEN,
    )
    project_manager.canvas = canvas
    h["command"] = __scroll_xview
    v["command"] = __scroll_yview
    button_frame = ttk.Frame(diagram_frame, padding="3 3 3 3", borderwidth=1)

    # Layout of the drawing area:
    canvas.grid(column=0, row=0, sticky="nsew")
    h.grid(column=0, row=1, sticky="ew")  # The sticky argument extends the scrollbar, so that a "shift" is possible.
    v.grid(column=1, row=0, sticky="ns")  # The sticky argument extends the scrollbar, so that a "shift" is possible.
    button_frame.grid(column=0, row=2, sticky="swe")

    # Implement the buttons of the drawing area:
    undo_redo_frame = ttk.Frame(button_frame, borderwidth=2)
    undo_button = ttk.Button(
        undo_redo_frame, text="Undo (Ctrl-z)", command=undo_handling.undo, style="Undo.TButton", state="disabled"
    )
    project_manager.undo_button = undo_button
    redo_button = ttk.Button(
        undo_redo_frame, text="Redo(Ctrl-Z)", command=undo_handling.redo, style="Redo.TButton", state="disabled"
    )
    project_manager.redo_button = redo_button
    undo_button.grid(row=0, column=0)
    redo_button.grid(row=0, column=1)

    action_frame = ttk.Frame(button_frame, borderwidth=2)
    state_action_default_button = ttk.Button(
        action_frame, text="Default State Actions (combinatorial)", style="DefaultStateActions.TButton"
    )
    project_manager.state_action_default_button = state_action_default_button
    global_action_clocked_button = ttk.Button(
        action_frame, text="Global Actions (clocked)", style="GlobalActionsClocked.TButton"
    )
    project_manager.global_action_clocked_button = global_action_clocked_button
    global_action_combinatorial_button = ttk.Button(
        action_frame, text="Global Actions (combinatorial)", style="GlobalActionsCombinatorial.TButton"
    )
    project_manager.global_action_combinatorial_button = global_action_combinatorial_button
    state_action_default_button.grid(row=0, column=0)
    global_action_clocked_button.grid(row=0, column=1)
    global_action_combinatorial_button.grid(row=0, column=2)

    new_transition_button = ttk.Button(button_frame, text="new Transition", style="NewTransition.TButton")
    new_state_button = ttk.Button(button_frame, text="new State", style="NewState.TButton")
    new_connector_button = ttk.Button(button_frame, text="new Connector", style="NewConnector.TButton")
    reset_entry_button = ttk.Button(button_frame, text="Reset Entry", style="ResetEntry.TButton")
    project_manager.reset_entry_button = reset_entry_button
    view_all_button = ttk.Button(button_frame, text="view all", style="View.TButton")
    view_area_button = ttk.Button(button_frame, text="view area", style="View.TButton")
    plus_button = ttk.Button(button_frame, text="+", style="View.TButton")
    minus_button = ttk.Button(button_frame, text="-", style="View.TButton")

    # Layout of the button area:
    new_state_button.grid(row=0, column=0)
    new_transition_button.grid(row=0, column=1)
    new_connector_button.grid(row=0, column=2)
    reset_entry_button.grid(row=0, column=3)
    action_frame.grid(row=0, column=4)
    undo_redo_frame.grid(row=0, column=5)
    view_all_button.grid(row=0, column=6, sticky=tk.E)
    view_area_button.grid(row=0, column=7)
    plus_button.grid(row=0, column=8)
    minus_button.grid(row=0, column=9)
    button_frame.columnconfigure(4, weight=1)
    button_frame.columnconfigure(5, weight=1)

    # Bindings of the drawing area:
    project_manager.root.bind_all("<Escape>", lambda event: canvas_modify_bindings.switch_to_move_mode())
    new_state_button.bind("<Button-1>", lambda event: canvas_modify_bindings.switch_to_state_insertion())
    new_transition_button.bind("<Button-1>", lambda event: canvas_modify_bindings.switch_to_transition_insertion())
    new_connector_button.bind("<Button-1>", lambda event: canvas_modify_bindings.switch_to_connector_insertion())
    reset_entry_button.bind("<Button-1>", lambda event: canvas_modify_bindings.switch_to_reset_entry_insertion())
    state_action_default_button.bind(
        "<Button-1>", lambda event: canvas_modify_bindings.switch_to_state_action_default_insertion()
    )
    global_action_clocked_button.bind(
        "<Button-1>", lambda event: canvas_modify_bindings.switch_to_global_action_clocked_insertion()
    )
    global_action_combinatorial_button.bind(
        "<Button-1>", lambda event: canvas_modify_bindings.switch_to_global_action_combinatorial_insertion()
    )
    view_area_button.bind("<Button-1>", lambda event: canvas_modify_bindings.switch_to_view_area())
    view_all_button.bind("<Button-1>", lambda event: canvas_editing.view_all())
    plus_button.bind("<Button-1>", lambda event: canvas_editing.zoom_plus())
    minus_button.bind("<Button-1>", lambda event: canvas_editing.zoom_minus())

    canvas.bind_all("<Delete>", lambda event: canvas_delete.CanvasDelete(canvas))
    canvas.bind("<Button-1>", move_handling_initialization.move_initialization)
    canvas.bind("<Motion>", canvas_delete.CanvasDelete.store_mouse_position)
    canvas.bind("<Control-MouseWheel>", canvas_editing.zoom_wheel)  # MouseWheel used at Windows.
    canvas.bind("<Control-Button-4>", canvas_editing.zoom_wheel)  # MouseWheel-Scroll-Up used at Linux.
    canvas.bind("<Control-Button-5>", canvas_editing.zoom_wheel)  # MouseWheel-Scroll-Down used at Linux.
    canvas.bind("<Control-Button-1>", canvas_editing.scroll_start)
    canvas.bind("<Control-B1-Motion>", canvas_editing.scroll_move)
    canvas.bind("<Control-ButtonRelease-1>", canvas_editing.scroll_end)
    canvas.bind("<MouseWheel>", canvas_editing.scroll_wheel)
    canvas.bind("<Button-3>", canvas_editing.start_view_rectangle)
    canvas.bind("<Configure>", __check_for_window_resize)

    canvas_editing.create_font_for_state_names()
    grid_drawer = grid_drawing.GridDraw(canvas)
    project_manager.grid_drawer = grid_drawer


def __scroll_xview(*args) -> None:
    project_manager.grid_drawer.remove_grid()
    project_manager.canvas.xview(*args)
    project_manager.grid_drawer.draw_grid()


def __scroll_yview(*args) -> None:
    project_manager.grid_drawer.remove_grid()
    project_manager.canvas.yview(*args)
    project_manager.grid_drawer.draw_grid()


def __check_for_window_resize(_) -> None:
    project_manager.grid_drawer.remove_grid()
    project_manager.grid_drawer.draw_grid()


def _handle_notebook_tab_changed_event() -> None:
    _enable_undo_redo_if_diagram_tab_is_active_else_disable()
    _update_hdl_tab_if_necessary()


def _enable_undo_redo_if_diagram_tab_is_active_else_disable() -> None:
    if project_manager.notebook.index(project_manager.notebook.select()) == 3:
        project_manager.canvas.bind_all("<Control-z>", lambda event: undo_handling.undo())
        project_manager.canvas.bind_all("<Control-Z>", lambda event: undo_handling.redo())
    else:
        project_manager.canvas.unbind_all(
            "<Control-z>"
        )  # necessary, because if you type Control-z when another tab is active,
        project_manager.canvas.unbind_all("<Control-Z>")  # then in the diagram tab an undo would take place.


def create_hdl_notebook_tab() -> None:
    hdl_frame = ttk.Frame(project_manager.notebook)
    hdl_frame.grid()
    hdl_frame.columnconfigure(0, weight=1)
    hdl_frame.rowconfigure(0, weight=1)

    hdl_frame_text = custom_text.CustomText(hdl_frame, text_type="generated", undo=False, font=("Courier", 10))
    project_manager.hdl_frame_text = hdl_frame_text
    hdl_frame_text.grid(row=0, column=0, sticky="nsew")
    hdl_frame_text.columnconfigure((0, 0), weight=1)
    hdl_frame_text.config(state=tk.DISABLED)

    hdl_frame_text_scroll = ttk.Scrollbar(hdl_frame, orient=tk.VERTICAL, cursor="arrow", command=hdl_frame_text.yview)
    hdl_frame_text.config(yscrollcommand=hdl_frame_text_scroll.set)
    hdl_frame_text_scroll.grid(row=0, column=1, sticky="nsew")

    hdl_frame_text.bind("<Motion>", _cursor_move_hdl_tab)

    project_manager.notebook.add(hdl_frame, sticky="nsew", text=GuiTab.GENERATED_HDL.value)


def create_log_notebook_tab() -> None:
    global _debug_active
    log_frame = ttk.Frame(project_manager.notebook)
    log_frame.grid()
    log_frame.columnconfigure(0, weight=1)
    log_frame.rowconfigure(1, weight=1)

    log_frame_button_frame = ttk.Frame(log_frame)
    log_frame_text = custom_text.CustomText(log_frame, text_type="log", undo=False)
    project_manager.log_frame_text = log_frame_text
    log_frame_button_frame.grid(row=0, column=0, sticky="ew")
    log_frame_text.grid(row=1, column=0, sticky="nsew")
    log_frame_text.columnconfigure((0, 0), weight=1)
    log_frame_text.config(state=tk.DISABLED)

    log_frame_clear_button = ttk.Button(log_frame_button_frame, takefocus=False, text="Clear", style="Find.TButton")
    log_frame_clear_button.grid(row=0, column=0, sticky=tk.W)
    log_frame_clear_button.bind("<Button-1>", _clear_log_tab)

    log_frame_regex_button = ttk.Button(
        log_frame_button_frame, takefocus=False, text="Define Regex for Hyperlinks", style="Find.TButton"
    )
    log_frame_regex_button.grid(row=0, column=1, sticky=tk.W)
    log_frame_regex_button.config(command=_edit_regex)

    log_frame_text_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, cursor="arrow", command=log_frame_text.yview)
    log_frame_text.config(yscrollcommand=log_frame_text_scroll.set)
    log_frame_text_scroll.grid(row=1, column=1, sticky="nsew")

    log_frame_text.bind("<Motion>", _cursor_move_log_tab)

    project_manager.notebook.add(log_frame, sticky="nsew", text=GuiTab.COMPILE_MSG.value)
    _debug_active = tk.IntVar()
    _debug_active.set(1)  # 1: inactive, 2: active


def _clear_log_tab(_) -> None:
    project_manager.log_frame_text.config(state=tk.NORMAL)
    project_manager.log_frame_text.delete("1.0", tk.END)
    project_manager.log_frame_text.config(state=tk.DISABLED)


def create_menu_bar() -> None:
    menue_frame = ttk.Frame(project_manager.root, borderwidth=2, relief=tk.RAISED)
    menue_frame.grid(column=0, row=0, sticky="nsew")

    file_menu_button = ttk.Menubutton(menue_frame, text="File", style="Window.TMenubutton")
    file_menu = tk.Menu(file_menu_button)
    file_menu_button.configure(menu=file_menu)
    file_menu.add_command(label="New", accelerator="Ctrl+n", command=file_handling.new_design, font=("Arial", 10))
    file_menu.add_command(label="Open ...", accelerator="Ctrl+o", command=file_handling.open_file, font=("Arial", 10))
    file_menu.add_command(label="Save", accelerator="Ctrl+s", command=file_handling.save, font=("Arial", 10))
    file_menu.add_command(label="Save as ...", command=file_handling.save_as, font=("Arial", 10))
    file_menu.add_command(label="Exit", command=_close_tool, font=("Arial", 10))

    hdl_menu_button = ttk.Menubutton(menue_frame, text="HDL", style="Window.TMenubutton")
    hdl_menu = tk.Menu(hdl_menu_button)
    hdl_menu_button.configure(menu=hdl_menu)
    hdl_menu.add_command(
        label="Generate",
        accelerator="Ctrl+g",
        command=lambda: hdl_generation.run_hdl_generation(write_to_file=True),
        font=("Arial", 10),
    )
    hdl_menu.add_command(
        label="Compile", accelerator="Ctrl+p", command=compile_handling.compile_hdl, font=("Arial", 10)
    )

    tool_title = ttk.Label(menue_frame, text="HDL-FSM-Editor", font=("Arial", 15))

    search_string = tk.StringVar()
    search_string.set("")
    replace_string = tk.StringVar()
    replace_string.set("")
    search_frame = ttk.Frame(menue_frame, borderwidth=2)
    search_button = ttk.Button(
        search_frame,
        text="Find",
        command=lambda: find_replace.FindReplace(search_string, replace_string, replace=False),
        style="Find.TButton",
    )
    search_string_entry = ttk.Entry(search_frame, width=23, textvariable=search_string)
    replace_string_entry = ttk.Entry(search_frame, width=23, textvariable=replace_string)
    replace_button = ttk.Button(
        search_frame,
        text="Find & Replace",
        command=lambda: find_replace.FindReplace(search_string, replace_string, replace=True),
        style="Find.TButton",
    )
    search_string_entry.bind(
        "<Return>", lambda event: find_replace.FindReplace(search_string, replace_string, replace=False)
    )
    search_button.bind("<Return>", lambda event: find_replace.FindReplace(search_string, replace_string, replace=False))
    replace_string_entry.bind(
        "<Return>", lambda event: find_replace.FindReplace(search_string, replace_string, replace=True)
    )
    replace_button.bind("<Return>", lambda event: find_replace.FindReplace(search_string, replace_string, replace=True))
    search_string_entry.grid(row=0, column=0)
    search_button.grid(row=0, column=1)
    replace_string_entry.grid(row=0, column=2)
    replace_button.grid(row=0, column=3)

    info_menu_button = ttk.Menubutton(menue_frame, text="Info", style="Window.TMenubutton")
    info_menu = tk.Menu(info_menu_button)
    info_menu_button.configure(menu=info_menu)
    info_menu.add_command(
        label="About", command=lambda: messagebox.showinfo("About:", constants.header_string), font=("Arial", 10)
    )

    project_manager.notebook.bind("<<NotebookTabChanged>>", lambda event: _handle_notebook_tab_changed_event())

    file_menu_button.grid(row=0, column=0)
    hdl_menu_button.grid(row=0, column=1)
    tool_title.grid(row=0, column=2)
    search_frame.grid(row=0, column=3)
    info_menu_button.grid(row=0, column=4)
    menue_frame.columnconfigure(2, weight=1)

    # Bindings of the menus:
    project_manager.root.bind_all("<Control-o>", lambda event: file_handling.open_file())
    project_manager.root.bind_all("<Control-s>", lambda event: file_handling.save())
    project_manager.root.bind_all("<Control-g>", lambda event: hdl_generation.run_hdl_generation(write_to_file=True))
    project_manager.root.bind_all("<Control-n>", lambda event: file_handling.new_design())
    project_manager.root.bind_all("<Control-p>", lambda event: compile_handling.compile_hdl())
    project_manager.root.bind_all("<Control-f>", lambda event: search_string_entry.focus_set())
    project_manager.root.bind_all("<Control-O>", lambda event: _capslock_warning("O"))
    project_manager.root.bind_all("<Control-S>", lambda event: _capslock_warning("S"))
    project_manager.root.bind_all("<Control-G>", lambda event: _capslock_warning("G"))
    project_manager.root.bind_all("<Control-N>", lambda event: _capslock_warning("N"))
    project_manager.root.bind_all("<Control-P>", lambda event: _capslock_warning("P"))
    project_manager.root.bind_all("<Control-F>", lambda event: _capslock_warning("F"))


def _edit_regex(*_) -> None:
    """Open the regex configuration dialog and update settings if confirmed."""
    global _regex_error_happened

    # Determine current pattern based on language
    current_pattern = (
        project_manager.regex_message_find_for_vhdl
        if project_manager.language.get() == "VHDL"
        else project_manager.regex_message_find_for_verilog
    )

    # Create and show dialog
    result = RegexDialog.ask_regex(
        parent=project_manager.root,
        language=project_manager.language.get(),
        current_pattern=current_pattern,
        current_filename_group=project_manager.regex_file_name_quote,
        current_line_number_group=project_manager.regex_file_line_number_quote,
        current_debug_active=_debug_active.get() == 2,
    )

    if result is not None:
        # Update global variables based on language
        if project_manager.language.get() == "VHDL":
            project_manager.regex_message_find_for_vhdl = result.pattern
        else:
            project_manager.regex_message_find_for_verilog = result.pattern

        project_manager.regex_file_name_quote = result.filename_group
        project_manager.regex_file_line_number_quote = result.line_number_group
        _debug_active.set(2 if result.debug_active else 1)

        undo_handling.design_has_changed()
        _regex_error_happened = False


def _cursor_move_hdl_tab(*_) -> None:
    global _line_number_under_pointer_hdl_tab, _func_id_jump
    if project_manager.hdl_frame_text.get("1.0", tk.END + "- 1 char") == "":
        return
    # Determine current cursor position:
    delta_x = project_manager.hdl_frame_text.winfo_pointerx() - project_manager.hdl_frame_text.winfo_rootx()
    delta_y = project_manager.hdl_frame_text.winfo_pointery() - project_manager.hdl_frame_text.winfo_rooty()
    index_string = project_manager.hdl_frame_text.index(f"@{delta_x},{delta_y}")  # index_string has the format "1.34"
    # Determine current line number:
    line_number = int(re.sub(r"\..*", "", index_string))  # Remove everything after '.'
    # Check if cursor is on a different line than before:
    if line_number != _line_number_under_pointer_hdl_tab:
        project_manager.hdl_frame_text.tag_delete("underline")  # remove previous underline
        config = GenerationConfig.from_main_window()
        if line_number > hdl_generation.last_line_number_of_file1:
            # Cursor is in file 2 (architecture file)
            line_number_in_file = line_number - hdl_generation.last_line_number_of_file1
            selected_file = config.get_architecture_file()
            start_index = project_manager.size_of_file2_line_number
        else:
            line_number_in_file = line_number
            selected_file = config.get_primary_file()
            start_index = project_manager.size_of_file1_line_number
        while project_manager.hdl_frame_text.get(f"{line_number}.{start_index - 1}") == " ":
            start_index += 1  # leading blanks shall not be underlined
        if project_manager.link_dict_ref.has_link(selected_file, line_number_in_file):
            project_manager.hdl_frame_text.tag_add(  # add tag for all characters until end of line
                "underline", f"{line_number}.{start_index - 1}", f"{line_number + 1}.0"
            )
            project_manager.hdl_frame_text.tag_config("underline", underline=1)  # activate underline
            _func_id_jump = project_manager.hdl_frame_text.bind(  # Bind to text widget
                "<Control-Button-1>",
                lambda event: project_manager.link_dict_ref.jump_to_source(selected_file, line_number_in_file),
            )
        else:
            # For this line no link exists:
            project_manager.hdl_frame_text.unbind("<Button-1>", _func_id_jump)
            _func_id_jump = None
        _line_number_under_pointer_hdl_tab = line_number


def _cursor_move_log_tab(*_) -> None:
    global _func_id_jump1, _func_id_jump2, _regex_error_happened, _line_number_under_pointer_log_tab
    if project_manager.log_frame_text.get("1.0", tk.END + "- 1 char") == "":
        return
    debug = _debug_active.get() == 2
    # Determine current cursor position:
    delta_x = project_manager.log_frame_text.winfo_pointerx() - project_manager.log_frame_text.winfo_rootx()
    delta_y = project_manager.log_frame_text.winfo_pointery() - project_manager.log_frame_text.winfo_rooty()
    index_string = project_manager.log_frame_text.index(f"@{delta_x},{delta_y}")
    # Determine current line number:
    line_number = int(re.sub(r"\..*", "", index_string))
    if line_number != _line_number_under_pointer_log_tab and _regex_error_happened is False:
        project_manager.log_frame_text.tag_delete("underline")

        regex_message_find = (
            project_manager.regex_message_find_for_vhdl
            if project_manager.language.get() == "VHDL"
            else project_manager.regex_message_find_for_verilog
        )
        if debug:
            print("\nUsed Regex                         : ", regex_message_find)
        try:
            message_rgx = re.compile(regex_message_find)
        except re.error as e:
            _regex_error_happened = True
            messagebox.showerror("Error in HDL-FSM-Editor by regular expression", repr(e))
            return

        content_of_line = project_manager.log_frame_text.get(str(line_number) + ".0", str(line_number + 1) + ".0")
        content_of_line = content_of_line[:-1]  # Remove return
        if message_rgx.match(content_of_line):
            file_name = message_rgx.sub(project_manager.regex_file_name_quote, content_of_line)
            if debug:
                print("Regex found line                   : ", content_of_line)
                print("Regex found filename (group 1)     :", '"' + file_name + '"')

            file_line_number_string = message_rgx.sub(project_manager.regex_file_line_number_quote, content_of_line)
            if file_line_number_string != content_of_line:
                try:
                    file_line_number = int(file_line_number_string)
                except ValueError:
                    messagebox.showerror("Error converting line number to integer:", file_line_number_string)
                    return
                if debug:
                    print("Regex found line-number (group 2)  :", '"' + file_line_number_string + '"')
            else:
                if debug:
                    print("Regex found no line-number         : Getting line-number by group 2 did not work.")
                return

            if project_manager.link_dict_ref.has_link(
                file_name, file_line_number
            ):  # For example ieee source files are not a key in link_dict.
                if debug:
                    print("Filename and line-number are found in Link-Dictionary.")
                project_manager.log_frame_text.tag_add(
                    "underline", str(line_number) + ".0", str(line_number + 1) + ".0"
                )
                project_manager.log_frame_text.tag_config("underline", underline=1, foreground="red")
                _func_id_jump1 = project_manager.log_frame_text.bind(
                    "<Control-Button-1>",
                    lambda event: project_manager.link_dict_ref.jump_to_source(file_name, file_line_number),
                )
                _func_id_jump2 = project_manager.log_frame_text.bind(
                    "<Alt-Button-1>",
                    lambda event: project_manager.link_dict_ref.jump_to_hdl(file_name, file_line_number),
                )
            else:
                if debug:
                    print("Filename or line-number not found in Link-Dictionary.")
                # Add only tag (for coloring in red), but don't underline as no link exists.
                project_manager.log_frame_text.tag_add(
                    "underline", str(line_number) + ".0", str(line_number + 1) + ".0"
                )

        else:
            if debug:
                print("Regex did not match line           : ", content_of_line)
            if _func_id_jump1 is not None:
                project_manager.log_frame_text.unbind("<Button-1>", _func_id_jump1)
            if _func_id_jump2 is not None:
                project_manager.log_frame_text.unbind("<Button-1>", _func_id_jump2)
            _func_id_jump1 = None
            _func_id_jump2 = None
        _line_number_under_pointer_log_tab = line_number


def switch_language_mode() -> None:
    new_language = project_manager.language.get()
    if new_language == "VHDL":
        linting.highlight_pattern_dict = constants.VHDL_HIGHLIGHT_PATTERN_DICT
        # enable 2 files mode
        project_manager.select_file_number_text.set(2)
        _select_file_number_radio_button1.grid(row=0, column=2, sticky=tk.E)
        _select_file_number_radio_button2.grid(row=0, column=3, sticky=tk.E)
        # Interface: Adapt documentation for generics and ports
        paned_window_interface.insert(0, _interface_package_frame, weight=1)
        project_manager.interface_generics_label.config(text="Generics:")
        project_manager.interface_ports_label.config(text="Ports:")
        # Internals: Enable VHDL-package text field
        paned_window_internals.insert(0, _internals_package_frame, weight=1)
        # Internals: Architecture-Declarations, 2*Variable Declarations umbenennen
        project_manager.internals_architecture_label.config(text="Architecture Declarations:")
        project_manager.internals_process_clocked_label.config(text="Variable Declarations for clocked process:")
        project_manager.internals_process_combinatorial_label.config(
            text="Variable Declarations for combinatorial process:"
        )
        # Modify compile command:
        project_manager.compile_cmd.set("ghdl -a $file1 $file2; ghdl -e $name; ghdl -r $name")
        project_manager.compile_cmd_docu.config(
            text="Variables for compile command:\n$file1\t= Entity-File\n$file2\t= Architecture-File\n$file\t\
= File with Entity and Architecture\n$name\t= Entity Name"
        )
    else:  # "Verilog" or "SystemVerilog"
        linting.highlight_pattern_dict = constants.VERILOG_HIGHLIGHT_PATTERN_DICT
        # Control: disable 2 files mode
        project_manager.select_file_number_text.set(1)
        _select_file_number_radio_button1.grid_forget()
        _select_file_number_radio_button2.grid_forget()
        # Interface: Remove VHDL-package text field
        paned_window_interface.forget(_interface_package_frame)
        # Interface: Adapt documentation for generics and ports
        project_manager.interface_generics_label.config(text="Parameters:")
        project_manager.interface_ports_label.config(text="Ports:")
        # Internals: Remove VHDL-package text field
        paned_window_internals.forget(_internals_package_frame)
        # Internals: Architecture-Declarations umbenennen, 2*Variable Declarations umbenennen
        project_manager.internals_architecture_label.config(text="Internal Declarations:")
        project_manager.internals_process_clocked_label.config(
            text="Local Variable Declarations for clocked always process (not supported by all Verilog compilers):"
        )
        project_manager.internals_process_combinatorial_label.config(
            text="Local Variable Declarations for combinatorial always process(not supported by all Verilog compilers):"
        )
        # Modify compile command:
        if new_language == "Verilog":
            project_manager.compile_cmd.set("iverilog -o $name $file; vvp $name")
        else:
            project_manager.compile_cmd.set("iverilog -g2012 -o $name $file; vvp $name")
        project_manager.compile_cmd_docu.config(
            text="Variables for compile command:\n$file\t= Module-File\n$name\t= Module Name"
        )


def _show_path_has_changed(*_) -> None:
    undo_handling.design_has_changed()


def show_tab(tab: GuiTab) -> None:
    assert isinstance(tab, GuiTab), f"tab must be a GuiTab, but is {type(tab)}"

    notebook_ids = project_manager.notebook.tabs()
    for tab_id in notebook_ids:
        if project_manager.notebook.tab(tab_id, option="text") == tab.value:
            project_manager.notebook.select(tab_id)


def _update_hdl_tab_if_necessary() -> None:
    if project_manager.notebook.index(project_manager.notebook.select()) == 4:
        if project_manager.language.get() == "VHDL":
            if project_manager.select_file_number_text.get() == 1:
                hdlfilename = (
                    project_manager.generate_path_value.get() + "/" + project_manager.module_name.get() + ".vhd"
                )
                hdlfilename2 = ""
            else:
                hdlfilename = (
                    project_manager.generate_path_value.get() + "/" + project_manager.module_name.get() + "_e.vhd"
                )
                hdlfilename2 = (
                    project_manager.generate_path_value.get() + "/" + project_manager.module_name.get() + "_fsm.vhd"
                )
        else:  # verilog
            hdlfilename = project_manager.generate_path_value.get() + "/" + project_manager.module_name.get() + ".v"
            hdlfilename2 = ""

        if (
            os.path.isfile(hdlfilename)
            and project_manager.date_of_hdl_file_shown_in_hdl_tab < os.path.getmtime(hdlfilename)
        ) or (
            project_manager.select_file_number_text.get() == 2
            and os.path.isfile(hdlfilename2)
            and project_manager.date_of_hdl_file2_shown_in_hdl_tab < os.path.getmtime(hdlfilename2)
        ):
            answer = messagebox.askquestion(
                "Warning in HDL-FSM-Editor3",
                "The HDL was modified by another tool. Shall it be reloaded?",
                default="yes",
            )
            if answer == "yes":
                update_ref = update_hdl_tab.UpdateHdlTab(
                    project_manager.language.get(),
                    project_manager.select_file_number_text.get(),
                    project_manager.current_file,
                    project_manager.generate_path_value.get(),
                    project_manager.module_name.get(),
                )
                project_manager.date_of_hdl_file_shown_in_hdl_tab = update_ref.get_date_of_hdl_file()
                project_manager.date_of_hdl_file2_shown_in_hdl_tab = update_ref.get_date_of_hdl_file2()


def _change_color_of_diagram_background() -> None:
    try:
        project_manager.canvas.configure(bg=project_manager.diagram_background_color.get())
        project_manager.diagram_background_color_error.configure(text="")
    except tk.TclError:
        project_manager.canvas.configure(bg="white")
        project_manager.diagram_background_color_error.configure(
            text="The string '"
            + project_manager.diagram_background_color.get()
            + "' is not a valid color definition, using 'white' instead."
        )


def choose_bg_color() -> None:
    new_color = ColorChanger(project_manager.canvas.cget("bg")).ask_color()
    if new_color is not None:
        project_manager.canvas.configure(bg=new_color)
        project_manager.diagram_background_color.set(new_color)


def set_word_boundaries() -> None:
    # this first statement triggers tcl to autoload the library
    # that defines the variables we want to override.
    project_manager.root.tk.call("tcl_wordBreakAfter", "", 0)
    # this defines what tcl considers to be a "word". For more
    # information see http://www.tcl.tk/man/tcl8.5/TclCmd/library.htm#M19
    project_manager.root.tk.call("set", "tcl_wordchars", "[a-zA-Z0-9_]")
    project_manager.root.tk.call("set", "tcl_nonwordchars", "[^a-zA-Z0-9_]")


def view_all_after_window_is_built() -> None:
    canvas_editing.view_all()
    project_manager.canvas.unbind("<Visibility>")
