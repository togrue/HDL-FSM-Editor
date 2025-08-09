"""
This module contains all methods to change the binding of the left mouse-button for
inserting the different graphical objects.
"""

transition_insertion_runs = False


def switch_to_state_insertion() -> None:
    global transition_insertion_runs
    transition_insertion_runs = False
    # From now on states can be inserted by left mouse button (this ends with the escape key):
    import main_window
    import state_handling

    main_window.root.config(cursor="circle")
    main_window.canvas.bind("<Button-1>", state_handling.insert_state)


def switch_to_transition_insertion() -> None:
    global transition_insertion_runs
    transition_insertion_runs = True
    # From now on transitions can be inserted by left mouse button (this ends with the escape key):
    import main_window
    import transition_handling

    main_window.root.config(cursor="cross")
    main_window.canvas.bind("<Button-1>", transition_handling.transition_start)


def switch_to_connector_insertion() -> None:
    global transition_insertion_runs
    transition_insertion_runs = False
    #    print("switch_to_connector_insertion")
    import connector_handling
    import main_window

    main_window.root.config(cursor="dot")
    main_window.canvas.bind("<Button-1>", connector_handling.insert_connector)


def switch_to_reset_entry_insertion() -> None:
    global transition_insertion_runs
    transition_insertion_runs = False
    #    print("switch_to_reset_entry_insertion")
    import main_window
    import reset_entry_handling

    main_window.root.config(cursor="center_ptr")
    main_window.canvas.bind("<Button-1>", reset_entry_handling.insert_reset_entry)


def switch_to_state_action_default_insertion() -> None:
    global transition_insertion_runs
    transition_insertion_runs = False
    #    print("switch_to_state_action_default_insertion")
    import global_actions_handling
    import main_window

    main_window.root.config(cursor="bogosity")
    main_window.canvas.bind("<Button-1>", global_actions_handling.insert_state_actions_default)


def switch_to_global_action_clocked_insertion() -> None:
    global transition_insertion_runs
    transition_insertion_runs = False
    #    print("switch_to_global_action_clocked_insertion")
    import global_actions_handling
    import main_window

    main_window.root.config(cursor="bogosity")
    main_window.canvas.bind("<Button-1>", global_actions_handling.insert_global_actions_clocked)


def switch_to_global_action_combinatorial_insertion() -> None:
    global transition_insertion_runs
    transition_insertion_runs = False
    #    print("switch_to_global_action_combinatorial_insertion")
    import global_actions_handling
    import main_window

    main_window.root.config(cursor="bogosity")
    main_window.canvas.bind("<Button-1>", global_actions_handling.insert_global_actions_combinatorial)


def switch_to_move_mode() -> None:
    global transition_insertion_runs
    transition_insertion_runs = False
    #    print("switch_to_move_mode")
    import main_window
    import move_handling_initialization

    main_window.root.config(cursor="arrow")
    main_window.canvas.focus_set()  # Removes the focus from the last used button.
    main_window.canvas.bind("<Button-1>", move_handling_initialization.move_initialization)


def switch_to_view_area() -> None:
    global transition_insertion_runs
    transition_insertion_runs = False
    #    print("switch_to_view_area")
    import canvas_editing
    import main_window

    main_window.root.config(cursor="plus")
    main_window.canvas.bind("<Button-1>", canvas_editing.start_view_rectangle)
