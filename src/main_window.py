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

import canvas_editing
import canvas_modify_bindings
import codegen.hdl_generation as hdl_generation
import compile_handling
import constants
import custom_text
import file_handling
import grid_drawing
import move_handling_initialization
import undo_handling
import update_hdl_tab
from codegen.hdl_generation_config import GenerationConfig
from constants import GuiTab
from dialogs.color_changer import ColorChanger
from dialogs.regex_dialog import RegexDialog
from link_dictionary import init_link_dict, link_dict
from project_manager import project_manager

_VERSION = "5.7"
header_string = (
    "HDL-FSM-Editor\nVersion " + _VERSION + "\nCreated by Matthias Schweikart\nContact: matthias.schweikart@gmx.de"
)


root: tk.Tk
notebook: ttk.Notebook
module_name: tk.StringVar
language: tk.StringVar
generate_path_value: tk.StringVar
additional_sources_value: tk.StringVar
working_directory_value: tk.StringVar
select_file_number_text: tk.IntVar
reset_signal_name: tk.StringVar
clock_signal_name: tk.StringVar
compile_cmd: tk.StringVar
edit_cmd: tk.StringVar
interface_package_text: custom_text.CustomText
interface_generics_text: custom_text.CustomText
interface_ports_text: custom_text.CustomText
internals_package_text: custom_text.CustomText
internals_architecture_text: custom_text.CustomText
internals_process_clocked_text: custom_text.CustomText
internals_process_combinatorial_text: custom_text.CustomText
canvas: tk.Canvas
hdl_frame_text: custom_text.CustomText
log_frame_text: custom_text.CustomText

state_action_default_button: ttk.Button
global_action_clocked_button: ttk.Button
global_action_combinatorial_button: ttk.Button
reset_entry_button: ttk.Button

_select_file_number_label: ttk.Label
_select_file_number_frame: ttk.Frame
_interface_package_label: ttk.Label
_interface_package_scroll: ttk.Scrollbar
_interface_generics_label: ttk.Label
_interface_ports_label: ttk.Label
_internals_package_label: ttk.Label
_internals_package_scroll: ttk.Scrollbar
_internals_architecture_label: ttk.Label
_internals_process_clocked_label: ttk.Label
_internals_process_combinatorial_label: ttk.Label
_compile_cmd_docu: ttk.Label
_debug_active: tk.IntVar
regex_message_find_for_vhdl: str = "(.*?):([0-9]+):[0-9]+:.*"
regex_message_find_for_verilog: str = (
    "(.*?):([0-9]+): .*"  # Added ' ' after the second ':', to get no hit at time stamps (i.e. 16:58:36).
)
regex_file_name_quote: str = "\\1"
regex_file_line_number_quote: str = "\\2"
_regex_error_happened: bool = False
_line_number_under_pointer_log_tab: int = 0
_line_number_under_pointer_hdl_tab: int = 0
_func_id_jump1: str | None = None
_func_id_jump2: str | None = None
size_of_file1_line_number: int = 0
size_of_file2_line_number: int = 0
_func_id_jump: str | None = None
_module_name_entry: ttk.Entry
_clock_signal_name_entry: ttk.Entry
diagram_background_color: tk.StringVar
_diagram_background_color_error: ttk.Label
show_grid: bool = True
grid_drawer: grid_drawing.GridDraw
paned_window_interface: ttk.PanedWindow
_interface_package_frame: ttk.Frame
paned_window_internals: ttk.PanedWindow
_internals_package_frame: ttk.Frame
sash_positions: dict[str, dict[int, int]] = {"interface_tab": {}, "internals_tab": {}}
undo_button: ttk.Button
redo_button: ttk.Button
date_of_hdl_file_shown_in_hdl_tab: float = 0.0
date_of_hdl_file2_shown_in_hdl_tab: float = 0.0
include_timestamp_in_output: tk.BooleanVar
_check_version_result: str = ""

keywords: dict[str, list[str]] = constants.VHDL_KEYWORDS


def read_message() -> None:
    try:
        source = urllib.request.urlopen("http://www.hdl-fsm-editor.de/message.txt")
        message = source.read()
        _read_message_result = message.decode()
        # print(message.decode())
    except urllib.error.URLError:
        _read_message_result = "No message was found."
        # print("No message was found.")
    except ConnectionRefusedError:
        # pass
        _read_message_result = ""
    print(_read_message_result)
    _copy_message_into_log_tab(_read_message_result)


def _copy_message_into_log_tab(_read_message_result) -> None:
    log_frame_text.config(state=tk.NORMAL)
    log_frame_text.insert("1.0", header_string + "\n" + _check_version_result + "\n" + _read_message_result + "\n")
    log_frame_text.config(state=tk.NORMAL)


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
        if new_version != "Version" + _VERSION:
            _check_version_result = (
                "Please update to the new version of HDL-FSM-Editor available at http://www.hdl-fsm-editor.de"
            )
        else:
            _check_version_result = "Your version of HDL-FSM-Editor is up to date."
    except urllib.error.URLError:
        _check_version_result = "HDL-FSM-Editor version could not be checked, as you are offline."
    print(_check_version_result)


def show_window() -> None:
    root.wm_deiconify()


def view_all_after_window_is_built() -> None:
    canvas_editing.view_all()
    canvas.unbind("<Visibility>")


def _close_tool() -> None:
    title = root.title()
    if title.endswith("*"):
        action = file_handling.ask_save_unsaved_changes(title)
        if action == "cancel":
            return
        elif action == "save":
            file_handling.save()
            # Check if save was successful (current_file is not empty)
            if project_manager.current_file == "":
                return

    # Clean up temp file and exit
    if os.path.isfile(project_manager.current_file + ".tmp"):
        os.remove(project_manager.current_file + ".tmp")
    sys.exit()


def _get_resource_path(resource_name: str) -> Path:
    """Get the path to a resource file, handling both development and PyInstaller environments."""
    base_path = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).parent.parent

    return base_path / "rsc" / resource_name


def create_root() -> None:
    global root
    # The top window:
    root = tk.Tk()
    root.withdraw()  # Because it could be batch-mode because of "-generate_hdl" switch.

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
    init_link_dict(root)


def create_menu_bar() -> None:
    menue_frame = ttk.Frame(root, borderwidth=2, relief=tk.RAISED)
    menue_frame.grid(column=0, row=0, sticky="nsew")

    file_menu_button = ttk.Menubutton(menue_frame, text="File", style="Window.TMenubutton")
    file_menu = tk.Menu(file_menu_button)
    file_menu_button.configure(menu=file_menu)
    file_menu.add_command(label="New", accelerator="Ctrl+n", command=file_handling.new_design, font=("Arial", 10))
    file_menu.add_command(label="Open ...", accelerator="Ctrl+o", command=file_handling.open_file, font=("Arial", 10))
    file_menu.add_command(label="Save", accelerator="Ctrl+s", command=file_handling.save, font=("Arial", 10))
    file_menu.add_command(label="Save as ...", command=file_handling.save_as, font=("Arial", 10))
    file_menu.add_command(label="Exit", command=sys.exit, font=("Arial", 10))

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
    search_frame = ttk.Frame(menue_frame, borderwidth=2)  # , relief=RAISED)
    search_button = ttk.Button(
        search_frame,
        text="Find",
        command=lambda: canvas_editing.find(search_string, replace_string, replace=False),
        style="Find.TButton",
    )
    search_string_entry = ttk.Entry(search_frame, width=23, textvariable=search_string)
    replace_string_entry = ttk.Entry(search_frame, width=23, textvariable=replace_string)
    replace_button = ttk.Button(
        search_frame,
        text="Find & Replace",
        command=lambda: canvas_editing.find(search_string, replace_string, replace=True),
        style="Find.TButton",
    )
    search_string_entry.bind(
        "<Return>", lambda event: canvas_editing.find(search_string, replace_string, replace=False)
    )
    search_button.bind("<Return>", lambda event: canvas_editing.find(search_string, replace_string, replace=False))
    replace_string_entry.bind(
        "<Return>", lambda event: canvas_editing.find(search_string, replace_string, replace=True)
    )
    replace_button.bind("<Return>", lambda event: canvas_editing.find(search_string, replace_string, replace=True))
    search_string_entry.grid(row=0, column=0)
    search_button.grid(row=0, column=1)
    replace_string_entry.grid(row=0, column=2)
    replace_button.grid(row=0, column=3)

    info_menu_button = ttk.Menubutton(menue_frame, text="Info", style="Window.TMenubutton")
    info_menu = tk.Menu(info_menu_button)
    info_menu_button.configure(menu=info_menu)
    info_menu.add_command(
        label="About", command=lambda: messagebox.showinfo("About:", header_string), font=("Arial", 10)
    )

    notebook.bind("<<NotebookTabChanged>>", lambda event: _handle_notebook_tab_changed_event())

    file_menu_button.grid(row=0, column=0)
    hdl_menu_button.grid(row=0, column=1)
    tool_title.grid(row=0, column=2)
    search_frame.grid(row=0, column=3)  # , sticky=tk.E)
    info_menu_button.grid(row=0, column=4)  # , sticky=tk.E)
    menue_frame.columnconfigure(2, weight=1)
    # menue_frame.columnconfigure(3, weight=1)
    # menue_frame.columnconfigure(4, weight=1)

    # Bindings of the menus:
    root.bind_all("<Control-o>", lambda event: file_handling.open_file())
    root.bind_all("<Control-s>", lambda event: file_handling.save())
    root.bind_all("<Control-g>", lambda event: hdl_generation.run_hdl_generation(write_to_file=True))
    root.bind_all("<Control-n>", lambda event: file_handling.new_design())
    root.bind_all("<Control-p>", lambda event: compile_handling.compile_hdl())
    root.bind_all("<Control-f>", lambda event: search_string_entry.focus_set())
    root.bind_all("<Control-O>", lambda event: _capslock_warning("O"))
    root.bind_all("<Control-S>", lambda event: _capslock_warning("S"))
    root.bind_all("<Control-G>", lambda event: _capslock_warning("G"))
    root.bind_all("<Control-N>", lambda event: _capslock_warning("N"))
    root.bind_all("<Control-P>", lambda event: _capslock_warning("P"))
    root.bind_all("<Control-F>", lambda event: _capslock_warning("F"))


def _capslock_warning(character):
    messagebox.showwarning(
        "Warning in HDL-FSM-Editor",
        "The character " + character + " is not bound to any action.\nPerhaps Capslock is active?",
    )


def create_notebook() -> None:
    global notebook
    notebook = ttk.Notebook(root, padding=5)
    notebook.grid(column=0, row=1, sticky="nsew")


def create_control_notebook_tab() -> None:
    global \
        module_name, \
        language, \
        generate_path_value, \
        additional_sources_value, \
        working_directory_value, \
        select_file_number_text, \
        reset_signal_name, \
        clock_signal_name, \
        compile_cmd
    global \
        _select_file_number_label, \
        _select_file_number_frame, \
        _compile_cmd_docu, \
        edit_cmd, \
        _module_name_entry, \
        _clock_signal_name_entry
    global diagram_background_color, _diagram_background_color_error, include_timestamp_in_output
    control_frame = ttk.Frame(notebook, takefocus=False)
    control_frame.grid()

    module_name = tk.StringVar()
    module_name.set("")
    module_name_label = ttk.Label(control_frame, text="Module-Name:", padding=5)
    _module_name_entry = ttk.Entry(control_frame, width=23, textvariable=module_name)
    module_name_label.grid(row=0, column=0, sticky=tk.W)
    _module_name_entry.grid(row=0, column=1, sticky=tk.W)
    _module_name_entry.select_clear()

    language = tk.StringVar()
    language.set("VHDL")
    language_label = ttk.Label(control_frame, text="Language:", padding=5)
    language_combobox = ttk.Combobox(
        control_frame, textvariable=language, values=("VHDL", "Verilog", "SystemVerilog"), state="readonly"
    )
    language_combobox.bind("<<ComboboxSelected>>", lambda event: switch_language_mode())
    language_label.grid(row=1, column=0, sticky=tk.W)
    language_combobox.grid(row=1, column=1, sticky=tk.W)

    generate_path_value = tk.StringVar(value="")
    generate_path_value.trace_add("write", _show_path_has_changed)
    generate_path_label = ttk.Label(control_frame, text="Directory for generated HDL:", padding=5)
    generate_path_entry = ttk.Entry(control_frame, textvariable=generate_path_value, width=80)
    generate_path_button = ttk.Button(control_frame, text="Select...", command=_set_path, style="Path.TButton")
    generate_path_label.grid(row=2, column=0, sticky=tk.W)
    generate_path_entry.grid(row=2, column=1, sticky="ew")
    generate_path_button.grid(row=2, column=2, sticky="ew")
    control_frame.columnconfigure((2, 0), weight=0)
    control_frame.columnconfigure((2, 1), weight=1)
    control_frame.columnconfigure((2, 2), weight=0)

    _select_file_number_label = ttk.Label(control_frame, text="Select for generation:", padding=5)
    _select_file_number_frame = ttk.Frame(control_frame)
    _select_file_number_label.grid(row=3, column=0, sticky=tk.W)
    _select_file_number_frame.grid(row=3, column=1, sticky=(tk.W, tk.E))
    control_frame.columnconfigure((3, 0), weight=0)
    control_frame.columnconfigure((3, 1), weight=1)

    select_file_number_text = tk.IntVar()
    select_file_number_text.set(2)
    select_file_number_radio_button1 = ttk.Radiobutton(
        _select_file_number_frame, takefocus=False, variable=select_file_number_text, text="1 file", value=1
    )
    select_file_number_radio_button2 = ttk.Radiobutton(
        _select_file_number_frame, takefocus=False, variable=select_file_number_text, text="2 files", value=2
    )
    include_timestamp_in_output = tk.BooleanVar(value=True)
    include_timestamp_in_output.trace_add("write", lambda *args: undo_handling.update_window_title())
    include_timestamp_checkbox = ttk.Checkbutton(_select_file_number_frame, variable=include_timestamp_in_output)
    include_timestamp_label = ttk.Label(_select_file_number_frame, text="Include timestamp in generated HDL files")
    select_file_number_radio_button1.grid(row=0, column=1, sticky=tk.W)
    select_file_number_radio_button2.grid(row=0, column=2, sticky=tk.W)
    include_timestamp_checkbox.grid(row=0, column=2, sticky=tk.E)
    include_timestamp_label.grid(row=0, column=3, sticky=tk.E)
    _select_file_number_frame.columnconfigure((0, 0), weight=0)
    _select_file_number_frame.columnconfigure((0, 1), weight=0)
    _select_file_number_frame.columnconfigure((0, 2), weight=1)
    _select_file_number_frame.columnconfigure((0, 3), weight=0)

    reset_signal_name = tk.StringVar()
    reset_signal_name.set("")
    reset_signal_name_label = ttk.Label(control_frame, text="Name of asynchronous reset input port:", padding=5)
    reset_signal_name_entry = ttk.Entry(control_frame, width=23, textvariable=reset_signal_name)
    reset_signal_name_entry.bind("<Key>", lambda event: undo_handling.update_window_title())
    reset_signal_name_label.grid(row=4, column=0, sticky=tk.W)
    reset_signal_name_entry.grid(row=4, column=1, sticky=tk.W)

    clock_signal_name = tk.StringVar()
    clock_signal_name.set("")
    clock_signal_name_label = ttk.Label(control_frame, text="Name of clock input port:", padding=5)
    _clock_signal_name_entry = ttk.Entry(control_frame, width=23, textvariable=clock_signal_name)
    _clock_signal_name_entry.bind("<Key>", lambda event: undo_handling.update_window_title())
    clock_signal_name_label.grid(row=5, column=0, sticky=tk.W)
    _clock_signal_name_entry.grid(row=5, column=1, sticky=tk.W)

    compile_cmd = tk.StringVar()
    compile_cmd.set("ghdl -a $file1 $file2; ghdl -e $name; ghdl -r $name")
    compile_cmd_label = ttk.Label(control_frame, text="Compile command:", padding=5)
    compile_cmd_entry = ttk.Entry(control_frame, width=23, textvariable=compile_cmd)
    compile_cmd_label.grid(row=6, column=0, sticky=tk.W)
    compile_cmd_entry.grid(row=6, column=1, sticky="ew")
    control_frame.columnconfigure((6, 0), weight=0)
    control_frame.columnconfigure((6, 1), weight=1)

    _compile_cmd_docu = ttk.Label(
        control_frame,
        text="Variables for compile command:\n$file1\t= Entity-File\n$file2\t= Architecture-File\n$file\t\
= File with Entity and Architecture\n$name\t= Module Name",
        padding=5,
    )
    _compile_cmd_docu.grid(row=7, column=1, sticky=tk.W)
    control_frame.columnconfigure((7, 0), weight=0)
    control_frame.columnconfigure((7, 1), weight=1)

    edit_cmd = tk.StringVar()
    edit_cmd.set("C:/Program Files/Notepad++/notepad++.exe -nosession -multiInst")
    edit_cmd_label = ttk.Label(control_frame, text="Edit command (executed by Ctrl+e):", padding=5)
    edit_cmd_entry = ttk.Entry(control_frame, width=23, textvariable=edit_cmd)
    edit_cmd_label.grid(row=8, column=0, sticky=tk.W)
    edit_cmd_entry.grid(row=8, column=1, sticky="ew")
    control_frame.columnconfigure((8, 0), weight=0)
    control_frame.columnconfigure((8, 1), weight=1)

    additional_sources_value = tk.StringVar(value="")
    additional_sources_value.trace_add("write", _show_path_has_changed)
    additional_sources_label = ttk.Label(
        control_frame,
        text="Additional sources:\n(used only by HDL-SCHEM-Editor, must\nbe added manually to compile command)",
        padding=5,
    )
    additional_sources_entry = ttk.Entry(control_frame, textvariable=additional_sources_value, width=80)
    additional_sources_button = ttk.Button(control_frame, text="Select...", command=__add_path, style="Path.TButton")
    additional_sources_label.grid(row=9, column=0, sticky=tk.W)
    additional_sources_entry.grid(row=9, column=1, sticky=(tk.W, tk.E))
    additional_sources_button.grid(row=9, column=2, sticky=(tk.W, tk.E))
    control_frame.columnconfigure((9, 0), weight=0)
    control_frame.columnconfigure((9, 1), weight=1)
    control_frame.columnconfigure((9, 2), weight=0)

    working_directory_value = tk.StringVar(value="")
    working_directory_value.trace_add("write", _show_path_has_changed)
    working_directory_label = ttk.Label(control_frame, text="Working directory:", padding=5)
    working_directory_entry = ttk.Entry(control_frame, textvariable=working_directory_value, width=80)
    working_directory_button = ttk.Button(
        control_frame, text="Select...", command=_set_working_directory, style="Path.TButton"
    )
    working_directory_label.grid(row=10, column=0, sticky=tk.W)
    working_directory_entry.grid(row=10, column=1, sticky="ew")
    working_directory_button.grid(row=10, column=2, sticky="ew")
    control_frame.columnconfigure((10, 0), weight=0)
    control_frame.columnconfigure((10, 1), weight=1)
    control_frame.columnconfigure((10, 2), weight=0)

    diagram_background_color = tk.StringVar(value="white")
    diagram_background_color.trace_add("write", lambda *args: _change_color_of_diagram_background())
    diagram_background_color_label = ttk.Label(control_frame, text="Diagram background color:", padding=5)
    diagram_background_color_entry = ttk.Entry(control_frame, textvariable=diagram_background_color, width=80)
    diagram_background_color_button = ttk.Button(
        control_frame, text="Choose color...", command=choose_bg_color, style="Path.TButton"
    )
    diagram_background_color_label.grid(row=11, column=0, sticky=tk.W)
    diagram_background_color_entry.grid(row=11, column=1, sticky="ew")
    diagram_background_color_button.grid(row=11, column=2, sticky="ew")
    control_frame.columnconfigure((11, 0), weight=0)
    control_frame.columnconfigure((11, 1), weight=1)
    control_frame.columnconfigure((11, 2), weight=0)
    _diagram_background_color_error = ttk.Label(control_frame, text="", padding=5)
    _diagram_background_color_error.grid(row=12, column=1, sticky=tk.W)
    control_frame.columnconfigure((12, 0), weight=0)
    control_frame.columnconfigure((12, 1), weight=1)
    control_frame.columnconfigure((12, 2), weight=0)

    notebook.add(control_frame, sticky="nsew", text=GuiTab.CONTROL.value)


def _set_path() -> None:
    path = askdirectory(title="Select directory for generated HDL")
    if path != "" and not path.isspace():
        generate_path_value.set(path)


def __add_path():
    old_entry = additional_sources_value.get()
    if old_entry != "":
        old_entries = old_entry.split(",")
        path = askopenfilename(initialdir=os.path.dirname(old_entries[0]))
    else:
        path = askopenfilename()
    if path != "":
        if old_entry == "":
            additional_sources_value.set(path)
        else:
            additional_sources_value.set(old_entry + ", " + path)


def _set_working_directory() -> None:
    path = askdirectory()
    if path != "" and not path.isspace():
        working_directory_value.set(path)


def create_interface_notebook_tab() -> None:
    global interface_package_text, interface_generics_text, interface_ports_text
    global _interface_package_label, _interface_package_scroll
    global _interface_generics_label, _interface_ports_label
    global paned_window_interface, _interface_package_frame

    paned_window_interface = ttk.PanedWindow(notebook, orient=tk.VERTICAL, takefocus=True)

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
    interface_package_text.insert("1.0", "library ieee;\nuse ieee.std_logic_1164.all;")
    interface_package_text.update_highlight_tags(
        10, ["not_read", "not_written", "control", "datatype", "function", "comment"]
    )
    interface_package_text.bind("<Control-Z>", lambda event: interface_package_text.edit_redo())
    interface_package_text.bind("<Control-e>", lambda event: interface_package_text.edit_in_external_editor())
    interface_package_text.bind("<<TextModified>>", lambda event: undo_handling.update_window_title())
    interface_package_text.bind("<Key>", lambda event, id=interface_package_text: _handle_key(event, id))
    _interface_package_scroll = ttk.Scrollbar(
        _interface_package_frame, orient=tk.VERTICAL, cursor="arrow", command=interface_package_text.yview
    )
    interface_package_text.config(yscrollcommand=_interface_package_scroll.set)
    _interface_package_label.grid(row=0, column=0, sticky="wns")  # "W" nötig, damit Text links bleibt
    interface_package_info.grid(row=0, column=0, sticky=tk.E)
    interface_package_text.grid(row=1, column=0, sticky="nsew")  # "W,E" nötig, damit Text tatsächlich breiter wird
    _interface_package_scroll.grid(row=1, column=1, sticky="nsew")  # "W,E" nötig, damit Text tatsächlich breiter wird
    paned_window_interface.add(_interface_package_frame, weight=1)

    interface_generics_frame = ttk.Frame(paned_window_interface)
    interface_generics_frame.columnconfigure(0, weight=1)
    interface_generics_frame.columnconfigure(1, weight=0)
    interface_generics_frame.rowconfigure(0, weight=0)
    interface_generics_frame.rowconfigure(1, weight=1)
    _interface_generics_label = ttk.Label(interface_generics_frame, text="Generics:", padding=5)
    interface_generics_info = ttk.Label(interface_generics_frame, text="Undo/Redo: Ctrl-z/Ctrl-Z,Ctrl-y", padding=5)
    interface_generics_text = custom_text.CustomText(
        interface_generics_frame, text_type="generics", height=3, width=10, undo=True, font=("Courier", 10)
    )
    interface_generics_text.bind("<Control-Z>", lambda event: interface_generics_text.edit_redo())
    interface_generics_text.bind("<Control-e>", lambda event: interface_generics_text.edit_in_external_editor())
    interface_generics_text.bind("<<TextModified>>", lambda event: undo_handling.update_window_title())
    interface_generics_text.bind("<Key>", lambda event, id=interface_generics_text: _handle_key_at_generics(id))
    interface_generics_scroll = ttk.Scrollbar(
        interface_generics_frame, orient=tk.VERTICAL, cursor="arrow", command=interface_generics_text.yview
    )
    interface_generics_text.config(yscrollcommand=interface_generics_scroll.set)
    _interface_generics_label.grid(row=0, column=0, sticky="wns")
    interface_generics_info.grid(row=0, column=0, sticky=tk.E)
    interface_generics_text.grid(row=1, column=0, sticky="nsew")
    interface_generics_scroll.grid(row=1, column=1, sticky="nsew")  # "W,E" nötig, damit Text tatsächlich breiter wird
    paned_window_interface.add(interface_generics_frame, weight=1)
    interface_generics_frame.bind("<Configure>", __resize_event_interface_tab_frames)

    interface_ports_frame = ttk.Frame(paned_window_interface)
    interface_ports_frame.columnconfigure(0, weight=1)
    interface_ports_frame.columnconfigure(1, weight=0)
    interface_ports_frame.rowconfigure(0, weight=0)
    interface_ports_frame.rowconfigure(1, weight=1)
    _interface_ports_label = ttk.Label(interface_ports_frame, text="Ports:", padding=5)
    interface_ports_info = ttk.Label(interface_ports_frame, text="Undo/Redo: Ctrl-z/Ctrl-Z,Ctrl-y", padding=5)
    interface_ports_text = custom_text.CustomText(
        interface_ports_frame, text_type="ports", height=3, width=10, undo=True, font=("Courier", 10)
    )
    interface_ports_text.bind("<Control-z>", lambda event: interface_ports_text.undo())
    interface_ports_text.bind("<Control-Z>", lambda event: interface_ports_text.redo())
    interface_ports_text.bind("<Control-e>", lambda event: interface_ports_text.edit_in_external_editor())
    interface_ports_text.bind("<<TextModified>>", lambda event: undo_handling.update_window_title())
    interface_ports_text.bind("<Key>", lambda event, id=interface_ports_text: _handle_key_at_ports(id))
    interface_ports_scroll = ttk.Scrollbar(
        interface_ports_frame, orient=tk.VERTICAL, cursor="arrow", command=interface_ports_text.yview
    )
    interface_ports_text.config(yscrollcommand=interface_ports_scroll.set)
    _interface_ports_label.grid(row=0, column=0, sticky=tk.W)
    interface_ports_info.grid(row=0, column=0, sticky=tk.E)
    interface_ports_text.grid(row=1, column=0, sticky="nsew")
    interface_ports_scroll.grid(row=1, column=1, sticky="nsew")  # "W,E" nötig, damit Text tatsächlich breiter wird
    paned_window_interface.add(interface_ports_frame, weight=1)

    notebook.add(paned_window_interface, sticky="nsew", text=GuiTab.INTERFACE.value)


def create_internals_notebook_tab() -> None:
    global \
        internals_package_text, \
        internals_architecture_text, \
        internals_process_clocked_text, \
        internals_process_combinatorial_text
    global _internals_package_label, _internals_package_scroll
    global _internals_architecture_label, _internals_process_clocked_label, _internals_process_combinatorial_label
    global paned_window_internals, _internals_package_frame

    paned_window_internals = ttk.PanedWindow(notebook, orient=tk.VERTICAL, takefocus=True)

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
    internals_package_text.bind("<Control-Z>", lambda event: internals_package_text.edit_redo())
    internals_package_text.bind("<Control-e>", lambda event: internals_package_text.edit_in_external_editor())
    internals_package_text.bind("<<TextModified>>", lambda event: undo_handling.update_window_title())
    internals_package_text.bind("<Key>", lambda event, id=internals_package_text: _handle_key(event, id))
    _internals_package_scroll = ttk.Scrollbar(
        _internals_package_frame, orient=tk.VERTICAL, cursor="arrow", command=internals_package_text.yview
    )
    internals_package_text.config(yscrollcommand=_internals_package_scroll.set)
    _internals_package_label.grid(row=0, column=0, sticky=tk.W)  # "W" nötig, damit Text links bleibt
    interface_package_info.grid(row=0, column=0, sticky=tk.E)
    internals_package_text.grid(row=1, column=0, sticky="nsew")  # "W,E" nötig, damit Text tatsächlich breiter wird
    _internals_package_scroll.grid(row=1, column=1, sticky="nsew")  # "W,E" nötig, damit Text tatsächlich breiter wird
    paned_window_internals.add(_internals_package_frame, weight=1)

    internals_architecture_frame = ttk.Frame(paned_window_internals)
    internals_architecture_frame.columnconfigure(0, weight=1)
    internals_architecture_frame.columnconfigure(1, weight=0)
    internals_architecture_frame.rowconfigure(0, weight=0)
    internals_architecture_frame.rowconfigure(1, weight=1)
    _internals_architecture_label = ttk.Label(
        internals_architecture_frame, text="Architecture Declarations:", padding=5
    )
    interface_architecture_info = ttk.Label(
        internals_architecture_frame, text="Undo/Redo: Ctrl-z/Ctrl-Z,Ctrl-y", padding=5
    )
    internals_architecture_text = custom_text.CustomText(
        internals_architecture_frame, text_type="declarations", height=3, width=10, undo=True, font=("Courier", 10)
    )
    internals_architecture_text.bind("<Control-z>", lambda event: internals_architecture_text.undo())
    internals_architecture_text.bind("<Control-Z>", lambda event: internals_architecture_text.redo())
    internals_architecture_text.bind("<Control-e>", lambda event: internals_architecture_text.edit_in_external_editor())
    internals_architecture_text.bind("<<TextModified>>", lambda event: undo_handling.update_window_title())
    internals_architecture_text.bind(
        "<Key>", lambda event, id=internals_architecture_text: _handle_key_at_declarations(id)
    )
    internals_architecture_scroll = ttk.Scrollbar(
        internals_architecture_frame, orient=tk.VERTICAL, cursor="arrow", command=internals_architecture_text.yview
    )
    internals_architecture_text.config(yscrollcommand=internals_architecture_scroll.set)
    _internals_architecture_label.grid(row=0, column=0, sticky=tk.W)
    interface_architecture_info.grid(row=0, column=0, sticky=tk.E)
    internals_architecture_text.grid(row=1, column=0, sticky="nsew")
    internals_architecture_scroll.grid(
        row=1, column=1, sticky="nsew"
    )  # "W,E" nötig, damit Text tatsächlich breiter wird
    paned_window_internals.add(internals_architecture_frame, weight=1)
    internals_architecture_frame.bind("<Configure>", __resize_event_internals_tab_frames)

    internals_process_clocked_frame = ttk.Frame(paned_window_internals)
    internals_process_clocked_frame.columnconfigure(0, weight=1)
    internals_process_clocked_frame.columnconfigure(1, weight=0)
    internals_process_clocked_frame.rowconfigure(0, weight=0)
    internals_process_clocked_frame.rowconfigure(1, weight=1)
    _internals_process_clocked_label = ttk.Label(
        internals_process_clocked_frame, text="Variable Declarations for clocked process:", padding=5
    )
    interface_process_clocked_info = ttk.Label(
        internals_process_clocked_frame, text="Undo/Redo: Ctrl-z/Ctrl-Z,Ctrl-y", padding=5
    )
    internals_process_clocked_text = custom_text.CustomText(
        internals_process_clocked_frame, text_type="variable", height=3, width=10, undo=True, font=("Courier", 10)
    )
    internals_process_clocked_text.bind("<Control-z>", lambda event: internals_process_clocked_text.undo())
    internals_process_clocked_text.bind("<Control-Z>", lambda event: internals_process_clocked_text.redo())
    internals_process_clocked_text.bind(
        "<Control-e>", lambda event: internals_process_clocked_text.edit_in_external_editor()
    )
    internals_process_clocked_text.bind("<<TextModified>>", lambda event: undo_handling.update_window_title())
    internals_process_clocked_text.bind(
        "<Key>", lambda event, id=internals_process_clocked_text: _handle_key_at_declarations(id)
    )
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
    internals_process_clocked_scroll.grid(
        row=1, column=1, sticky="nsew"
    )  # "W,E" nötig, damit Text tatsächlich breiter wird
    paned_window_internals.add(internals_process_clocked_frame, weight=1)

    internals_process_combinatorial_frame = ttk.Frame(paned_window_internals)
    internals_process_combinatorial_frame.columnconfigure(0, weight=1)
    internals_process_combinatorial_frame.columnconfigure(1, weight=0)
    internals_process_combinatorial_frame.rowconfigure(0, weight=0)
    internals_process_combinatorial_frame.rowconfigure(1, weight=1)
    _internals_process_combinatorial_label = ttk.Label(
        internals_process_combinatorial_frame, text="Variable Declarations for combinatorial process:", padding=5
    )
    interface_process_combinatorial_info = ttk.Label(
        internals_process_combinatorial_frame, text="Undo/Redo: Ctrl-z/Ctrl-Z,Ctrl-y", padding=5
    )
    internals_process_combinatorial_text = custom_text.CustomText(
        internals_process_combinatorial_frame, text_type="variable", height=3, width=10, undo=True, font=("Courier", 10)
    )
    internals_process_combinatorial_text.bind("<Control-z>", lambda event: internals_process_combinatorial_text.undo())
    internals_process_combinatorial_text.bind("<Control-Z>", lambda event: internals_process_combinatorial_text.redo())
    internals_process_combinatorial_text.bind(
        "<Control-e>", lambda event: internals_process_combinatorial_text.edit_in_external_editor()
    )
    internals_process_combinatorial_text.bind("<<TextModified>>", lambda event: undo_handling.update_window_title())
    internals_process_combinatorial_text.bind(
        "<Key>", lambda event, id=internals_process_combinatorial_text: _handle_key_at_declarations(id)
    )
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
    internals_process_combinatorial_scroll.grid(
        row=1, column=1, sticky="nsew"
    )  # "W,E" nötig, damit Text tatsächlich breiter wird
    paned_window_internals.add(internals_process_combinatorial_frame, weight=1)

    notebook.add(paned_window_internals, sticky="nsew", text=GuiTab.INTERNALS.value)


def create_diagram_notebook_tab() -> None:
    global canvas
    global state_action_default_button
    global global_action_clocked_button
    global global_action_combinatorial_button
    global reset_entry_button
    global grid_drawer
    global undo_button, redo_button

    diagram_frame = ttk.Frame(notebook, borderwidth=0, relief="flat")
    diagram_frame.grid()
    diagram_frame.columnconfigure(0, weight=1)  # tkinter method (grid_columnconfigure is tcl method)
    diagram_frame.rowconfigure(0, weight=1)
    notebook.add(diagram_frame, sticky="nsew", text=GuiTab.DIAGRAM.value)

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
    redo_button = ttk.Button(
        undo_redo_frame, text="Redo(Ctrl-Z)", command=undo_handling.redo, style="Redo.TButton", state="disabled"
    )
    undo_button.grid(row=0, column=0)
    redo_button.grid(row=0, column=1)

    action_frame = ttk.Frame(button_frame, borderwidth=2)
    state_action_default_button = ttk.Button(
        action_frame, text="Default State Actions (combinatorial)", style="DefaultStateActions.TButton"
    )
    global_action_clocked_button = ttk.Button(
        action_frame, text="Global Actions (clocked)", style="GlobalActionsClocked.TButton"
    )
    global_action_combinatorial_button = ttk.Button(
        action_frame, text="Global Actions (combinatorial)", style="GlobalActionsCombinatorial.TButton"
    )
    state_action_default_button.grid(row=0, column=0)
    global_action_clocked_button.grid(row=0, column=1)
    global_action_combinatorial_button.grid(row=0, column=2)

    new_transition_button = ttk.Button(button_frame, text="new Transition", style="NewTransition.TButton")
    new_state_button = ttk.Button(button_frame, text="new State", style="NewState.TButton")
    new_connector_button = ttk.Button(button_frame, text="new Connector", style="NewConnector.TButton")
    reset_entry_button = ttk.Button(button_frame, text="Reset Entry", style="ResetEntry.TButton")
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
    root.bind_all("<Escape>", lambda event: canvas_modify_bindings.switch_to_move_mode())
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

    canvas.bind_all("<Delete>", lambda event: canvas_editing.delete())
    canvas.bind("<Button-1>", move_handling_initialization.move_initialization)
    canvas.bind("<Motion>", canvas_editing.store_mouse_position)
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


def __scroll_xview(*args) -> None:
    grid_drawer.remove_grid()
    canvas.xview(*args)
    grid_drawer.draw_grid()


def __scroll_yview(*args) -> None:
    grid_drawer.remove_grid()
    canvas.yview(*args)
    grid_drawer.draw_grid()


def __check_for_window_resize(_) -> None:
    grid_drawer.remove_grid()
    grid_drawer.draw_grid()


def _handle_notebook_tab_changed_event() -> None:
    _enable_undo_redo_if_diagram_tab_is_active_else_disable()
    _update_hdl_tab_if_necessary()


def _enable_undo_redo_if_diagram_tab_is_active_else_disable() -> None:
    if notebook.index(notebook.select()) == 3:
        canvas.bind_all("<Control-z>", lambda event: undo_handling.undo())
        canvas.bind_all("<Control-Z>", lambda event: undo_handling.redo())
    else:
        canvas.unbind_all("<Control-z>")  # necessary, because if you type Control-z when another tab is active,
        canvas.unbind_all("<Control-Z>")  # then in the diagram tab an undo would take place.


def create_hdl_notebook_tab() -> None:
    global hdl_frame_text
    hdl_frame = ttk.Frame(notebook)
    hdl_frame.grid()
    hdl_frame.columnconfigure(0, weight=1)
    hdl_frame.rowconfigure(0, weight=1)

    hdl_frame_text = custom_text.CustomText(hdl_frame, text_type="generated", undo=False, font=("Courier", 10))
    hdl_frame_text.grid(row=0, column=0, sticky="nsew")
    hdl_frame_text.columnconfigure((0, 0), weight=1)
    hdl_frame_text.config(state=tk.DISABLED)

    hdl_frame_text_scroll = ttk.Scrollbar(hdl_frame, orient=tk.VERTICAL, cursor="arrow", command=hdl_frame_text.yview)
    hdl_frame_text.config(yscrollcommand=hdl_frame_text_scroll.set)
    hdl_frame_text_scroll.grid(row=0, column=1, sticky="nsew")

    hdl_frame_text.bind("<Motion>", _cursor_move_hdl_tab)

    notebook.add(hdl_frame, sticky="nsew", text=GuiTab.GENERATED_HDL.value)


def create_log_notebook_tab() -> None:
    global log_frame_text, _debug_active
    log_frame = ttk.Frame(notebook)
    log_frame.grid()
    log_frame.columnconfigure(0, weight=1)
    log_frame.rowconfigure(1, weight=1)

    log_frame_button_frame = ttk.Frame(log_frame)
    log_frame_text = custom_text.CustomText(log_frame, text_type="log", undo=False)
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

    notebook.add(log_frame, sticky="nsew", text=GuiTab.COMPILE_MSG.value)
    _debug_active = tk.IntVar()
    _debug_active.set(1)  # 1: inactive, 2: active


def _clear_log_tab(_) -> None:
    log_frame_text.config(state=tk.NORMAL)
    log_frame_text.delete("1.0", tk.END)
    log_frame_text.config(state=tk.DISABLED)


def _edit_regex(*_) -> None:
    """Open the regex configuration dialog and update settings if confirmed."""
    global \
        regex_message_find_for_vhdl, \
        regex_message_find_for_verilog, \
        regex_file_name_quote, \
        regex_file_line_number_quote, \
        _regex_error_happened

    # Determine current pattern based on language
    current_pattern = regex_message_find_for_vhdl if language.get() == "VHDL" else regex_message_find_for_verilog

    # Create and show dialog
    result = RegexDialog.ask_regex(
        parent=root,
        language=language.get(),
        current_pattern=current_pattern,
        current_filename_group=regex_file_name_quote,
        current_line_number_group=regex_file_line_number_quote,
        current_debug_active=_debug_active.get() == 2,
    )

    if result is not None:
        # Update global variables based on language
        if language.get() == "VHDL":
            regex_message_find_for_vhdl = result.pattern
        else:
            regex_message_find_for_verilog = result.pattern

        regex_file_name_quote = result.filename_group
        regex_file_line_number_quote = result.line_number_group
        _debug_active.set(2 if result.debug_active else 1)

        undo_handling.design_has_changed()
        _regex_error_happened = False


def _cursor_move_hdl_tab(*_) -> None:
    global _line_number_under_pointer_hdl_tab, _func_id_jump
    if hdl_frame_text.get("1.0", tk.END + "- 1 char") == "":
        return
    # Determine current cursor position:
    delta_x = hdl_frame_text.winfo_pointerx() - hdl_frame_text.winfo_rootx()
    delta_y = hdl_frame_text.winfo_pointery() - hdl_frame_text.winfo_rooty()
    index_string = hdl_frame_text.index(f"@{delta_x},{delta_y}")  # index_string has the format "1.34"
    # Determine current line number:
    line_number = int(re.sub(r"\..*", "", index_string))  # Remove everything after '.'
    if line_number != _line_number_under_pointer_hdl_tab:
        hdl_frame_text.tag_delete("underline")
        config = GenerationConfig.from_main_window()
        if line_number > hdl_generation.last_line_number_of_file1:
            line_number_in_file = line_number - hdl_generation.last_line_number_of_file1
            selected_file = config.get_architecture_file()
            start_index = size_of_file2_line_number
        else:
            line_number_in_file = line_number
            selected_file = config.get_primary_file()
            start_index = size_of_file1_line_number
        while hdl_frame_text.get(f"{line_number}.{start_index - 1}") == " ":
            start_index += 1
        if link_dict().has_link(selected_file, line_number_in_file):
            hdl_frame_text.tag_add("underline", f"{line_number}.{start_index - 1}", f"{line_number + 1}.0")
            hdl_frame_text.tag_config("underline", underline=1)
            _func_id_jump = hdl_frame_text.bind(
                "<Control-Button-1>",
                lambda event: link_dict().jump_to_source(selected_file, line_number_in_file),
            )
        else:
            hdl_frame_text.unbind("<Button-1>", _func_id_jump)
            _func_id_jump = None
        _line_number_under_pointer_hdl_tab = line_number


def _cursor_move_log_tab(*_) -> None:
    global _func_id_jump1, _func_id_jump2, _regex_error_happened, _line_number_under_pointer_log_tab
    if log_frame_text.get("1.0", tk.END + "- 1 char") == "":
        return
    debug = _debug_active.get() == 2
    # Determine current cursor position:
    delta_x = log_frame_text.winfo_pointerx() - log_frame_text.winfo_rootx()
    delta_y = log_frame_text.winfo_pointery() - log_frame_text.winfo_rooty()
    index_string = log_frame_text.index(f"@{delta_x},{delta_y}")
    # Determine current line number:
    line_number = int(re.sub(r"\..*", "", index_string))
    if line_number != _line_number_under_pointer_log_tab and _regex_error_happened is False:
        log_frame_text.tag_delete("underline")
        regex_message_find = regex_message_find_for_vhdl if language.get() == "VHDL" else regex_message_find_for_verilog
        content_of_line = log_frame_text.get(str(line_number) + ".0", str(line_number + 1) + ".0")
        content_of_line = content_of_line[:-1]  # Remove return

        if debug:
            print("\nUsed Regex                         : ", regex_message_find)
        try:
            message_rgx = re.compile(regex_message_find)
        except re.error as e:
            _regex_error_happened = True
            messagebox.showerror("Error in HDL-FSM-Editor by regular expression", repr(e))
            return

        if message_rgx.match(content_of_line):
            file_name = message_rgx.sub(regex_file_name_quote, content_of_line)
            if debug:
                print("Regex found line                   : ", content_of_line)
                print("Regex found filename (group 1)     :", '"' + file_name + '"')

            file_line_number_string = message_rgx.sub(regex_file_line_number_quote, content_of_line)
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

            if link_dict().has_link(
                file_name, file_line_number
            ):  # For example ieee source files are not a key in link_dict.
                if debug:
                    print("Filename and line-number are found in Link-Dictionary.")
                log_frame_text.tag_add("underline", str(line_number) + ".0", str(line_number + 1) + ".0")
                log_frame_text.tag_config("underline", underline=1, foreground="red")
                _func_id_jump1 = log_frame_text.bind(
                    "<Control-Button-1>",
                    lambda event: link_dict().jump_to_source(file_name, file_line_number),
                )
                _func_id_jump2 = log_frame_text.bind(
                    "<Alt-Button-1>",
                    lambda event: link_dict().jump_to_hdl(file_name, file_line_number),
                )
            else:
                if debug:
                    print("Filename or line-number not found in Link-Dictionary.")
                # Add only tag (for coloring in red), but don't underline as no link exists.
                log_frame_text.tag_add("underline", str(line_number) + ".0", str(line_number + 1) + ".0")

        else:
            if debug:
                print("Regex did not match line           : ", content_of_line)
            if _func_id_jump1 is not None:
                log_frame_text.unbind("<Button-1>", _func_id_jump1)
            if _func_id_jump2 is not None:
                log_frame_text.unbind("<Button-1>", _func_id_jump2)
            _func_id_jump1 = None
            _func_id_jump2 = None
        _line_number_under_pointer_log_tab = line_number


def switch_language_mode() -> None:
    global keywords
    new_language = language.get()
    if new_language == "VHDL":
        keywords = constants.VHDL_KEYWORDS
        # enable 2 files mode
        select_file_number_text.set(2)
        _select_file_number_label.grid(row=3, column=0, sticky=tk.W)
        _select_file_number_frame.grid(row=3, column=1, sticky=(tk.W, tk.E))
        # Interface: Adapt documentation for generics and ports
        paned_window_interface.insert(0, _interface_package_frame, weight=1)
        _interface_generics_label.config(text="Generics:")
        _interface_ports_label.config(text="Ports:")
        # Internals: Enable VHDL-package text field
        paned_window_internals.insert(0, _internals_package_frame, weight=1)
        # Internals: Architecture-Declarations, 2*Variable Declarations umbenennen
        _internals_architecture_label.config(text="Architecture Declarations:")
        _internals_process_clocked_label.config(text="Variable Declarations for clocked process:")
        _internals_process_combinatorial_label.config(text="Variable Declarations for combinatorial process:")
        # Modify compile command:
        compile_cmd.set("ghdl -a $file1 $file2; ghdl -e $name; ghdl -r $name")
        _compile_cmd_docu.config(
            text="Variables for compile command:\n$file1\t= Entity-File\n$file2\t= Architecture-File\n$file\t\
= File with Entity and Architecture\n$name\t= Entity Name"
        )
    else:  # "Verilog" or "SystemVerilog"
        keywords = constants.VERILOG_KEYWORDS
        # Control: disable 2 files mode
        select_file_number_text.set(1)
        _select_file_number_label.grid_forget()
        _select_file_number_frame.grid_forget()
        # Interface: Remove VHDL-package text field
        paned_window_interface.forget(_interface_package_frame)
        # Interface: Adapt documentation for generics and ports
        _interface_generics_label.config(text="Parameters:")
        _interface_ports_label.config(text="Ports:")
        # Internals: Remove VHDL-package text field
        paned_window_internals.forget(_internals_package_frame)
        # Internals: Architecture-Declarations umbenennen, 2*Variable Declarations umbenennen
        _internals_architecture_label.config(text="Internal Declarations:")
        _internals_process_clocked_label.config(
            text="Local Variable Declarations for clocked always process (not supported by all Verilog compilers):"
        )
        _internals_process_combinatorial_label.config(
            text="Local Variable Declarations for combinatorial always process(not supported by all Verilog compilers):"
        )
        # Modify compile command:
        if new_language == "Verilog":
            compile_cmd.set("iverilog -o $name $file; vvp $name")
        else:
            compile_cmd.set("iverilog -g2012 -o $name $file; vvp $name")
        _compile_cmd_docu.config(text="Variables for compile command:\n$file\t= Module-File\n$name\t= Module Name")


def _handle_key(event, custom_text_ref) -> None:
    custom_text_ref.after_idle(
        custom_text_ref.update_highlight_tags, canvas_editing.fontsize, ["control", "datatype", "function", "comment"]
    )


def _handle_key_at_ports(custom_text_ref) -> None:
    custom_text_ref.after_idle(custom_text_ref.update_custom_text_class_ports_list)
    custom_text_ref.after_idle(custom_text_ref.update_highlighting)


def _handle_key_at_generics(custom_text_ref) -> None:
    custom_text_ref.after_idle(custom_text_ref.update_custom_text_class_generics_list)
    custom_text_ref.after_idle(custom_text_ref.update_highlighting)


def _handle_key_at_declarations(custom_text_ref) -> None:
    custom_text_ref.after_idle(custom_text_ref.update_custom_text_class_signals_list)
    custom_text_ref.after_idle(custom_text_ref.update_highlighting)


def _show_path_has_changed(*_) -> None:
    undo_handling.design_has_changed()


def show_tab(tab: GuiTab) -> None:
    assert isinstance(tab, GuiTab), f"tab must be a GuiTab, but is {type(tab)}"

    notebook_ids = notebook.tabs()
    for tab_id in notebook_ids:
        if notebook.tab(tab_id, option="text") == tab.value:
            notebook.select(tab_id)


def _update_hdl_tab_if_necessary() -> None:
    global date_of_hdl_file_shown_in_hdl_tab
    global date_of_hdl_file2_shown_in_hdl_tab
    if notebook.index(notebook.select()) == 4:
        if language.get() == "VHDL":
            if select_file_number_text.get() == 1:
                hdlfilename = generate_path_value.get() + "/" + module_name.get() + ".vhd"
                hdlfilename2 = ""
            else:
                hdlfilename = generate_path_value.get() + "/" + module_name.get() + "_e.vhd"
                hdlfilename2 = generate_path_value.get() + "/" + module_name.get() + "_fsm.vhd"
        else:  # verilog
            hdlfilename = generate_path_value.get() + "/" + module_name.get() + ".v"
            hdlfilename2 = ""

        if (os.path.isfile(hdlfilename) and date_of_hdl_file_shown_in_hdl_tab < os.path.getmtime(hdlfilename)) or (
            select_file_number_text.get() == 2
            and os.path.isfile(hdlfilename2)
            and date_of_hdl_file2_shown_in_hdl_tab < os.path.getmtime(hdlfilename2)
        ):
            answer = messagebox.askquestion(
                "Warning in HDL-FSM-Editor3",
                "The HDL was modified by another tool. Shall it be reloaded?",
                default="yes",
            )
            if answer == "yes":
                update_ref = update_hdl_tab.UpdateHdlTab(
                    language.get(),
                    select_file_number_text.get(),
                    project_manager.current_file,
                    generate_path_value.get(),
                    module_name.get(),
                )
                date_of_hdl_file_shown_in_hdl_tab = update_ref.get_date_of_hdl_file()
                date_of_hdl_file2_shown_in_hdl_tab = update_ref.get_date_of_hdl_file2()


def _change_color_of_diagram_background() -> None:
    try:
        canvas.configure(bg=diagram_background_color.get())
        _diagram_background_color_error.configure(text="")
    except tk.TclError:
        canvas.configure(bg="white")
        _diagram_background_color_error.configure(
            text="The string '"
            + diagram_background_color.get()
            + "' is not a valid color definition, using 'white' instead."
        )


def choose_bg_color() -> None:
    new_color = ColorChanger(canvas.cget("bg")).ask_color()
    if new_color is not None:
        canvas.configure(bg=new_color)
        diagram_background_color.set(new_color)


def __resize_event_interface_tab_frames(event) -> None:
    global sash_positions
    if "interface_tab" not in sash_positions:
        sash_positions["interface_tab"] = {}
    sash_positions["interface_tab"][0] = paned_window_interface.sashpos(0)
    if language.get() == "VHDL":
        sash_positions["interface_tab"][1] = paned_window_interface.sashpos(1)


def __resize_event_internals_tab_frames(event) -> None:
    global sash_positions
    if "internals_tab" not in sash_positions:
        sash_positions["internals_tab"] = {}
    sash_positions["internals_tab"][0] = paned_window_internals.sashpos(0)
    sash_positions["internals_tab"][1] = paned_window_internals.sashpos(1)
    if language.get() == "VHDL":
        sash_positions["internals_tab"][2] = paned_window_internals.sashpos(2)


def set_word_boundaries() -> None:
    # this first statement triggers tcl to autoload the library
    # that defines the variables we want to override.
    root.tk.call("tcl_wordBreakAfter", "", 0)
    # this defines what tcl considers to be a "word". For more
    # information see http://www.tcl.tk/man/tcl8.5/TclCmd/library.htm#M19
    root.tk.call("set", "tcl_wordchars", "[a-zA-Z0-9_]")
    root.tk.call("set", "tcl_nonwordchars", "[^a-zA-Z0-9_]")
