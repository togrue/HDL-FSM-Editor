"""
This module contains all methods to change the binding of the left mouse-button for
inserting the different graphical objects.
"""

import canvas_editing
import connector_handling
import global_actions_handling
import move_handling_canvas_item
import move_handling_initialization
import reset_entry_handling
import state_handling
import transition_handling
from project_manager import project_manager


def switch_to_state_insertion() -> None:
    move_handling_canvas_item.MoveHandlingCanvasItem.transition_insertion_runs = False
    # From now on states can be inserted by left mouse button (this ends with the escape key):
    project_manager.root.config(cursor="circle")
    project_manager.canvas.bind("<Button-1>", state_handling.insert_state)


def switch_to_transition_insertion() -> None:
    move_handling_canvas_item.MoveHandlingCanvasItem.transition_insertion_runs = True
    # From now on transitions can be inserted by left mouse button (this ends with the escape key):
    project_manager.root.config(cursor="cross")
    project_manager.canvas.bind("<Button-1>", transition_handling.transition_start)


def switch_to_connector_insertion() -> None:
    move_handling_canvas_item.MoveHandlingCanvasItem.transition_insertion_runs = False
    #    print("switch_to_connector_insertion")
    project_manager.root.config(cursor="dot")
    project_manager.canvas.bind("<Button-1>", connector_handling.ConnectorInsertion)


def switch_to_reset_entry_insertion() -> None:
    move_handling_canvas_item.MoveHandlingCanvasItem.transition_insertion_runs = False
    #    print("switch_to_reset_entry_insertion")
    project_manager.root.config(cursor="center_ptr")
    project_manager.canvas.bind("<Button-1>", reset_entry_handling.insert_reset_entry)


def switch_to_state_action_default_insertion() -> None:
    move_handling_canvas_item.MoveHandlingCanvasItem.transition_insertion_runs = False
    #    print("switch_to_state_action_default_insertion")
    project_manager.root.config(cursor="bogosity")
    project_manager.canvas.bind("<Button-1>", global_actions_handling.insert_state_actions_default)


def switch_to_global_action_clocked_insertion() -> None:
    move_handling_canvas_item.MoveHandlingCanvasItem.transition_insertion_runs = False
    #    print("switch_to_global_action_clocked_insertion")
    project_manager.root.config(cursor="bogosity")
    project_manager.canvas.bind("<Button-1>", global_actions_handling.insert_global_actions_clocked)


def switch_to_global_action_combinatorial_insertion() -> None:
    move_handling_canvas_item.MoveHandlingCanvasItem.transition_insertion_runs = False
    #    print("switch_to_global_action_combinatorial_insertion")
    project_manager.root.config(cursor="bogosity")
    project_manager.canvas.bind("<Button-1>", global_actions_handling.insert_global_actions_combinatorial)


def switch_to_move_mode() -> None:
    move_handling_canvas_item.MoveHandlingCanvasItem.transition_insertion_runs = False
    #    print("switch_to_move_mode")
    project_manager.root.config(cursor="arrow")
    project_manager.canvas.focus_set()  # Removes the focus from the last used button.
    project_manager.canvas.bind("<Button-1>", move_handling_initialization.move_initialization)


def switch_to_view_area() -> None:
    move_handling_canvas_item.MoveHandlingCanvasItem.transition_insertion_runs = False
    #    print("switch_to_view_area")
    project_manager.root.config(cursor="plus")
    project_manager.canvas.bind("<Button-1>", canvas_editing.start_view_rectangle)
