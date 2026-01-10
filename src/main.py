"""
HDL-FSM-Editor: A tool for modeling FSMs
"""

import argparse
import sys
from os.path import exists
from tkinter import messagebox

import constants
import file_handling
import main_window
import undo_handling
from codegen import hdl_generation
from project_manager import project_manager


def _setup_application_ui() -> None:
    """Set up the main application UI components."""
    main_window.create_gui()
    main_window.set_word_boundaries()
    # Initialize undo/redo system
    undo_handling.design_has_changed()


def _parse_and_process_arguments() -> None:
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
            if args.generate_hdl:
                print("Error: File " + args.filename + " was not found.")
            else:
                messagebox.showerror("Error", f"File {args.filename} was not found.")
        elif not args.filename.endswith(".hfe"):
            if args.generate_hdl:
                print("Error: File " + args.filename + " must have extension '.hfe'.")
            else:
                messagebox.showerror("Error", f"File {args.filename} must have extension '.hfe'.")
        else:
            # Load the file
            project_manager.current_file = args.filename
            project_manager.root.title("new")
            file_handling.new_design()
            if args.generate_hdl:
                file_handling.open_file_with_name(args.filename, is_script_mode=True)
            else:
                file_handling.open_file_with_name(args.filename, is_script_mode=False)
            project_manager.canvas.bind("<Visibility>", lambda _event: main_window.view_all_after_window_is_built())

    # Handle batch generation
    if args.generate_hdl:
        success = hdl_generation.run_hdl_generation(write_to_file=True, is_script_mode=True)
        sys.exit(0 if success else 1)


def _main() -> None:
    """Main entry point for HDL-FSM-Editor."""
    print(constants.header_string)
    _setup_application_ui()
    _parse_and_process_arguments()
    project_manager.root.wm_deiconify()
    project_manager.root.mainloop()


if __name__ == "__main__":
    _main()

# During editing in the diagram notebook tab, several tags are used to identify the canvas items.
# This is a list of all these tags:
#
# Tags of a state (blue circle in the diagram):
# "state<n>"                      : Unique identifier for the circle, which represents the state.
# "transition<n>_start"           : The transition "transition<n>" starts at this state.
# "transition<n>_end"             : The transition "transition<n>" ends at this state.
# "connection<n>_end"             : The connection "connection<n>" (a dashed line) assigns a state action block.
# "state<n>_comment_line_end"     : The line "state<n>_comment_line" (a dashed line) connects a state comment block.
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
# "ca_connection<n>_end"          : The connection "ca_connection<n>" (a dashed line) assigns a condition&action-block.
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
# "connection<n>_start"           : The connection "connection<n>" (dashed) assigns the state action block to a state.
#
# Tags of a condition&action block (text window with grey background):
# "condition_action<n>"           : Unique identifier for the window
# "ca_connection<n>_anchor"       : The connection "ca_connection<n>" (a dashed line) assigns the block to a transition.
# "connected_to_reset_transition" : This block is a assigned to the transition which is connected to the reset-entry.
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
# state<n>_comment_line_start     : The line with the identifier state<n>_comment_line connects the block to the state.

# Tags of a state comment line (dashed line in the diagram, which connects a state and its state comment block block):
# state<n>_comment_line           : Unique identifier for the line
