"""
This module contains all methods to change the binding of the left mouse-button for inserting the different graphical objects.
"""

import canvas_editing
import connector_handling
import global_actions_handling
import main_window
import move_handling_initialization
import reset_entry_handling
import state_handling
import transition_handling


def switch_to_state_insertion() -> None:
    # From now on states can be inserted by left mouse button (this ends with the escape key):
    main_window.root.config(cursor="circle")
    main_window.canvas.bind("<Button-1>", state_handling.insert_state)


def switch_to_transition_insertion() -> None:
    # From now on transitions can be inserted by left mouse button (this ends with the escape key):
    main_window.root.config(cursor="cross")
    main_window.canvas.bind("<Button-1>", transition_handling.transition_start)


def switch_to_connector_insertion() -> None:
    #    print("switch_to_connector_insertion")
    main_window.root.config(cursor="dot")
    main_window.canvas.bind("<Button-1>", connector_handling.insert_connector)


def switch_to_reset_entry_insertion() -> None:
    #    print("switch_to_reset_entry_insertion")
    main_window.root.config(cursor="center_ptr")
    main_window.canvas.bind("<Button-1>", reset_entry_handling.insert_reset_entry)


def switch_to_state_action_default_insertion() -> None:
    #    print("switch_to_state_action_default_insertion")
    main_window.root.config(cursor="bogosity")
    main_window.canvas.bind("<Button-1>", global_actions_handling.insert_state_actions_default)


def switch_to_global_action_clocked_insertion() -> None:
    #    print("switch_to_global_action_clocked_insertion")
    main_window.root.config(cursor="bogosity")
    main_window.canvas.bind("<Button-1>", global_actions_handling.insert_global_actions_clocked)


def switch_to_global_action_combinatorial_insertion() -> None:
    #    print("switch_to_global_action_combinatorial_insertion")
    main_window.root.config(cursor="bogosity")
    main_window.canvas.bind("<Button-1>", global_actions_handling.insert_global_actions_combinatorial)


def switch_to_move_mode() -> None:
    #    print("switch_to_move_mode")
    main_window.root.config(cursor="arrow")
    main_window.canvas.focus_set()  # Removes the focus from the last used button.
    main_window.canvas.bind("<Button-1>", move_handling_initialization.move_initialization)


def switch_to_view_area() -> None:
    #    print("switch_to_view_area")
    main_window.root.config(cursor="plus")
    main_window.canvas.bind("<Button-1>", canvas_editing.start_view_rectangle)
