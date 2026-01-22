"""
Class for combinatorial actions independent from the state machine
"""

import tkinter as tk
from tkinter import ttk

import canvas_delete
import canvas_editing
import canvas_modify_bindings
import custom_text
import move_handling_canvas_window
import undo_handling
from project_manager import project_manager


class GlobalActionsCombinatorial:
    """
    Class for combinatorial actions independent from the state machine
    """

    dictionary = {}

    def __init__(self, menu_x, menu_y, height, width, padding, tags) -> None:
        self.text_content = None
        self.difference_x = 0
        self.difference_y = 0

        self.frame_id = ttk.Frame(
            project_manager.canvas, relief=tk.FLAT, borderwidth=0, padding=padding, style="GlobalActionsWindow.TFrame"
        )
        self.label = ttk.Label(
            self.frame_id,
            text="Global actions combinatorial: ",
            font=("Arial", int(project_manager.label_fontsize)),
            style="GlobalActionsWindow.TLabel",
        )
        self.text_id = custom_text.CustomText(
            self.frame_id,
            text_type="action",
            height=height,
            width=width,
            undo=True,
            maxundo=-1,
            font=("Courier", int(project_manager.fontsize)),
        )
        self.label.grid(row=0, column=0, sticky=(tk.N, tk.W, tk.E))
        self.text_id.grid(row=1, column=0, sticky=(tk.E, tk.W))
        # Create canvas window for frame:
        self.window_id = project_manager.canvas.create_window(
            menu_x, menu_y, window=self.frame_id, anchor=tk.W, tags=tags
        )

        self.frame_id.bind("<Enter>", lambda event: self.activate_frame())
        self.frame_id.bind("<Leave>", lambda event: self.deactivate_frame())
        self.frame_id.bind(
            "<Button-1>",
            lambda event: move_handling_canvas_window.MoveHandlingCanvasWindow(event, self.frame_id, self.window_id),
        )
        self.label.bind("<Enter>", lambda event: self.activate_window())
        self.label.bind("<Leave>", lambda event: self.deactivate_window())
        self.label.bind(
            "<Button-1>",
            lambda event: move_handling_canvas_window.MoveHandlingCanvasWindow(event, self.label, self.window_id),
        )
        self.text_id.bind("<Control-z>", lambda event: self.text_id.undo())
        self.text_id.bind("<Control-Z>", lambda event: self.text_id.redo())
        self.text_id.bind("<Control-e>", lambda event: self._edit_in_external_editor())
        self.text_id.bind("<Control-s>", lambda event: self.update_text())
        self.text_id.bind("<Control-g>", lambda event: self.update_text())
        self.text_id.bind("<<TextModified>>", lambda event: undo_handling.update_window_title())
        self.text_id.bind("<FocusIn>", lambda event: project_manager.canvas.unbind_all("<Delete>"))
        self.text_id.bind(
            "<FocusOut>",
            lambda event: project_manager.canvas.bind_all("<Delete>", lambda event: canvas_delete.CanvasDelete()),
        )
        self.frame_id.lower()
        GlobalActionsCombinatorial.dictionary[self.window_id] = self
        canvas_modify_bindings.switch_to_move_mode()

    def _edit_in_external_editor(self):
        self.text_id.edit_in_external_editor()
        self.update_text()

    def update_text(self):
        # Update self.text_content, so that the <Leave>-check in deactivate() does not signal a design-change and
        # that save_in_file() already reads the new text, entered into the textbox before Control-s/g.
        # To ensure this, save_in_file() waits for idle.
        self.text_content = self.text_id.get("1.0", tk.END)

    def activate_frame(self) -> None:
        self.activate_window()
        self.text_content = self.text_id.get("1.0", tk.END)

    def activate_window(self) -> None:
        self.frame_id.configure(borderwidth=1, style="GlobalActionsWindowSelected.TFrame")
        self.label.configure(style="GlobalActionsWindowSelected.TLabel")

    def deactivate_frame(self) -> None:
        self.deactivate_window()
        if self.text_id.get("1.0", tk.END) != self.text_content:
            undo_handling.design_has_changed()

    def deactivate_window(self) -> None:
        project_manager.canvas.focus_set()  # "unfocus" the Text, when the mouse leaves the text.
        self.frame_id.configure(borderwidth=0, style="GlobalActionsWindow.TFrame")
        self.label.configure(style="GlobalActionsWindow.TLabel")

    def move_to(self, event_x, event_y, first) -> None:
        if first:
            # Calculate the difference between the "anchor" point and the event:
            coords = project_manager.canvas.coords(self.window_id)
            self.difference_x, self.difference_y = -event_x + coords[0], -event_y + coords[1]
        # Keep the distance between event and anchor point constant:
        event_x, event_y = event_x + self.difference_x, event_y + self.difference_y
        project_manager.canvas.coords(self.window_id, event_x, event_y)

    def delete(self):
        del custom_text.CustomText.read_variables_of_all_windows[self.text_id]
        del custom_text.CustomText.written_variables_of_all_windows[self.text_id]
        project_manager.canvas.delete(self.window_id)  # delete window
        del GlobalActionsCombinatorial.dictionary[self.window_id]
        project_manager.global_action_combinatorial_button.config(state=tk.NORMAL)

    @classmethod
    def insert_global_actions_combinatorial(cls, event) -> None:
        project_manager.global_action_combinatorial_button.config(state=tk.DISABLED)
        canvas_grid_coordinates_of_the_event = (
            canvas_editing.translate_window_event_coordinates_in_exact_canvas_coordinates(event)
        )
        GlobalActionsCombinatorial(
            canvas_grid_coordinates_of_the_event[0],
            canvas_grid_coordinates_of_the_event[1],
            height=1,
            width=8,
            padding=1,
            tags=("global_actions_combinatorial1"),
        )
        undo_handling.design_has_changed()
