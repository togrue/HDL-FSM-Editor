"""
HDL-FSM-Editor: A tool for modeling FSMs
"""

import argparse
import sys
from os.path import exists
from tkinter import messagebox, ttk

import file_handling
import hdl_generation
import main_window
import undo_handling
from state_manager import state_manager


def setup_application_ui():
    """Set up the main application UI components."""

    main_window.create_root()

    # Configure application styling
    style = ttk.Style(main_window.root)
    style.theme_use("default")
    # style.theme_use('clam')
    # style.theme_use('winnative')
    # style.theme_use('alt')
    # style.theme_use('classic')
    # style.theme_use('vista')
    # style.theme_use('xpnative')
    style.configure("Window.TFrame", background="blue")
    style.configure("Window.TMenubutton")
    style.configure("StateActionsWindow.TFrame", background="cyan2")
    style.configure("StateActionsWindow.TLabel", background="cyan2")
    style.configure("GlobalActionsWindow.TFrame", background="PaleGreen2")
    style.configure("GlobalActionsWindow.TLabel", background="PaleGreen2")
    style.configure("DefaultStateActions.TButton", background="cyan2")
    style.configure("GlobalActionsClocked.TButton", background="PaleGreen2")
    style.configure("GlobalActionsCombinatorial.TButton", background="PaleGreen2")
    style.configure("NewState.TButton", background="SkyBlue1")
    style.configure("NewTransition.TButton", background="white")
    style.configure("NewConnector.TButton", background="orchid1")
    style.configure("ResetEntry.TButton", background="IndianRed1")
    style.configure("View.TButton", background="lemon chiffon")
    style.configure("Undo.TButton")
    style.configure("Redo.TButton")
    style.configure("Find.TButton")
    style.configure("Path.TButton")

    # Create UI components
    main_window.set_word_boundaries()
    main_window.create_notebook()
    main_window.create_control_notebook_tab()
    main_window.create_interface_notebook_tab()
    main_window.create_internals_notebook_tab()
    main_window.create_diagram_notebook_tab()
    main_window.create_hdl_notebook_tab()
    main_window.create_log_notebook_tab()
    main_window.create_menu_bar()

    # Initialize undo/redo system
    undo_handling.design_has_changed()


def parse_and_process_arguments():
    """Parse command-line arguments and process them."""
    parser = argparse.ArgumentParser(description="HDL-FSM-Editor: A tool for modeling FSMs")
    parser.add_argument("filename", nargs="?", help="HDL-FSM-Editor file (.hfe) to open")
    parser.add_argument("--no-version-check", action="store_true", help="Skip version check at startup")
    parser.add_argument("--no-message", action="store_true", help="Skip message check at startup")
    parser.add_argument("--generate-hdl", action="store_true", help="Generate HDL and exit")

    args = parser.parse_args()

    # Handle version and message checks
    if not args.no_version_check:
        main_window.check_version()
    if not args.no_message:
        main_window.read_message()

    # Handle filename
    if args.filename:
        if not exists(args.filename):
            messagebox.showerror("Error", f"File {args.filename} was not found.")
        elif not args.filename.endswith(".hfe"):
            messagebox.showerror("Error", f"File {args.filename} must have extension '.hfe'.")
        else:
            # Load the file
            state_manager.current_file = args.filename
            main_window.root.title("new")
            file_handling.remove_old_design()
            file_handling.open_file_with_name_new(args.filename)
            main_window.canvas.bind("<Visibility>", lambda event: main_window.view_all_after_window_is_built())

    # Handle batch generation
    if args.generate_hdl:
        hdl_generation.run_hdl_generation(write_to_file=True)
        sys.exit()


def main():
    """Main entry point for HDL-FSM-Editor."""
    print(main_window.header_string)

    setup_application_ui()

    parse_and_process_arguments()

    main_window.show_window()
    main_window.root.mainloop()


if __name__ == "__main__":
    main()

# During editing in the diagram notebook tab, several tags are used to identify the canvas items.
# This is a list of all these tags:
#
# Tags of a state (blue circle in the diagram):
# "state<n>"                      : Unique identifier for the circle, which represents the state.
# "transition<n>_start"           : The transition "transition<n>" starts at this state.
# "transition<n>_end"             : The transition "transition<n>" ends at this state.
# "connection<n>_end"             : The connection "connection<n>" (a dashed line) assigns a state action block to this state.
# "state<n>_comment_line_end"     : The line "state<n>_comment_line" (a dashed line) connects a state comment block to this state.
#
# Tags of the string inside each state circle:
# "state<n>_name"                 : identifier for the text object, which stores the state name.
#
# Tags of a connector (violet square in the diagram):
# "connector<n>"                  : Unique identifier for the square, which represents the connector.
# "transition<n>_start"           : The transition "transition<n>" starts at this state.
# "transition<n>_end"             : The transition "transition<n>" ends at this state.
#
# Tags of a transition (blue line in the diagram):
# "transition<n>"                 : Unique identifier for the line, which represents the transition.
# "coming_from_state<n>"          : Information, at which state the transition starts.
# "coming_from_connector<n>"      : Information, at which state the transition starts.
# "going_to_state<n>"             : Information, at which state the transition ends.
# "going_to_connector<n>"         : Information, at which state the transition ends.
# "coming_from_reset_entry"       : Information, that the transition starts at the reset_entry object.
# "ca_connection<n>_end"          : The connection "ca_connection<n>" (a dashed line) assigns a condition&action-block to this transition.
#
# Tags of the transition priority rectangle(blue square located at each transition line):
# "transition<n>rectangle"        : Unique identifier for the square.
#
# Tags of the transition priority value (text located in the priority rectangle):
# "transition<n>priority"         : Unique identifier for the text object, which stores the priority number.
#
# Tags of a connection line (dashed line in the diagram, which connects a state and a state action block):
# "connection<n>"                 : Unique identifier for the line
# "connected_to_state<n>"         : Information to which state the state action block is assigned.
#
# Tags of a ca_connection line (dashed line in the diagram, which connects a transition and a condition&action block):
# "ca_connection<n>"              : Unique identifier for the line
# "connected_to_transition<n>"    : Information to which state the state action block is assigned.
#
# Tags of a state action block (text window with blue background):
# "state_action<n>"               : Unique identifier for the window
# "connection<n>_start"           : The connection "connection<n>" (a dashed line) assigns the state action block to a state.
#
# Tags of a condition&action block (text window with grey background):
# "condition_action<n>"           : Unique identifier for the window
# "ca_connection<n>_anchor"       : The connection "ca_connection<n>" (a dashed line) assigns the condition&action block to a transition.
# "connected_to_reset_transition" : This condition&action block is a assigned to the transition which is connected to the reset-entry object.
#
# Tags of a reset-entry object (red arrow):
# "reset_entry"                   : Unique identifier for the reset entry (polygon) object.
# "transition<n>_start"           : The transition "transition<n>" starts at the reset entry object.
#
# Tags of the string inside the reset-entry object:
# "reset_text"                    : Unique identifier for the text object storing the string "Reset".
#
# Tags of the default state action block (not connected text window with blue background):
# "state_actions_default"         : Unique identifier for the window.
#
# Tags of the global actions combinatorial block (not connected text window with green background):
# "global_actions_combinatorial1" : Unique identifier for the window.
#
# Tags of the global actions clocked block (not connected text window with green background):
# "global_actions1"               : Unique identifier for the window.

# Tags of a state comment block (text window with blue background in the header):
# state<n>_comment                : Unique identifier for the window
# state<n>_comment_line_start     : The line with the identifier state<n>_comment_line connects the state comment block to the state

# Tags of a state comment line (dashed line in the diagram, which connects a state and its state comment block block):
# state<n>_comment_line           : Unique identifier for the line
