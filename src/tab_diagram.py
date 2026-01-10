import tkinter as tk
from tkinter import ttk

import canvas_delete
import canvas_editing
import canvas_modify_bindings
import grid_drawing
import move_handling_initialization
import undo_handling
from constants import GuiTab
from project_manager import project_manager


class TabDiagram:
    """Module for creating the diagram tab in the notebook."""

    def __init__(self) -> None:
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
        h["command"] = self.__scroll_xview
        v["command"] = self.__scroll_yview
        button_frame = ttk.Frame(diagram_frame, padding="3 3 3 3", borderwidth=1)

        # Layout of the drawing area:
        canvas.grid(column=0, row=0, sticky="nsew")
        h.grid(
            column=0, row=1, sticky="ew"
        )  # The sticky argument extends the scrollbar, so that a "shift" is possible.
        v.grid(
            column=1, row=0, sticky="ns"
        )  # The sticky argument extends the scrollbar, so that a "shift" is possible.
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
        canvas.bind("<Configure>", self.__check_for_window_resize)

        canvas_editing.create_font_for_state_names()
        grid_drawer = grid_drawing.GridDraw(canvas)
        project_manager.grid_drawer = grid_drawer

    def __scroll_xview(self, *args) -> None:
        project_manager.grid_drawer.remove_grid()
        project_manager.canvas.xview(*args)
        project_manager.grid_drawer.draw_grid()

    def __scroll_yview(self, *args) -> None:
        project_manager.grid_drawer.remove_grid()
        project_manager.canvas.yview(*args)
        project_manager.grid_drawer.draw_grid()

    def __check_for_window_resize(self, _) -> None:
        project_manager.grid_drawer.remove_grid()
        project_manager.grid_drawer.draw_grid()
