"""
Handles the global actions window in the diagram.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

import canvas_editing
import canvas_modify_bindings
import custom_text
import main_window
import move_handling_canvas_window
import undo_handling


class GlobalActions:
    """
    Handles the global actions clocked window in the diagram.
    """

    global_actions_number: int = 1
    dictionary: dict[int, "GlobalActions"] = {}

    def __init__(self, menu_x: float, menu_y: float, height: int, width: int, padding: int) -> None:
        self.text_before_content: Optional[str] = None
        self.text_after_content: Optional[str] = None
        self.difference_x: float = 0.0
        self.difference_y: float = 0.0
        self.frame_id = ttk.Frame(
            main_window.canvas, relief=tk.FLAT, borderwidth=0, padding=padding, style="GlobalActionsWindow.TFrame"
        )
        self.frame_id.bind("<Enter>", lambda event: self.activate_frame())
        self.frame_id.bind("<Leave>", lambda event: self.deactivate_frame())
        # Create label object inside frame:
        self.label_before = ttk.Label(
            self.frame_id,
            text="Global actions clocked (executed before running the state machine):",
            font=("Arial", int(canvas_editing.label_fontsize)),
            style="GlobalActionsWindow.TLabel",
        )
        self.label_before.bind("<Enter>", lambda event: self.activate_window())
        self.label_before.bind("<Leave>", lambda event: self.deactivate_window())
        self.label_after = ttk.Label(
            self.frame_id,
            text="Global actions clocked (executed after running the state machine):",
            font=("Arial", int(canvas_editing.label_fontsize)),
            style="GlobalActionsWindow.TLabel",
        )
        self.label_after.bind("<Enter>", lambda event: self.activate_window())
        self.label_after.bind("<Leave>", lambda event: self.deactivate_window())
        self.text_before_id = custom_text.TextBeforeCustomText(
            self.frame_id,
            text_type="action",
            height=height,
            width=width,
            undo=True,
            maxundo=-1,
            font=("Courier", int(canvas_editing.fontsize)),
        )
        self.text_after_id = custom_text.TextAfterCustomText(
            self.frame_id,
            text_type="action",
            height=height,
            width=width,
            undo=True,
            maxundo=-1,
            font=("Courier", int(canvas_editing.fontsize)),
        )
        self.text_before_id.bind("<Control-z>", lambda event: self.text_before_id.undo())
        self.text_before_id.bind("<Control-Z>", lambda event: self.text_before_id.redo())
        self.text_before_id.bind("<Control-e>", lambda event: self._edit_before_in_external_editor())
        self.text_after_id.bind("<Control-z>", lambda event: self.text_after_id.undo())
        self.text_after_id.bind("<Control-Z>", lambda event: self.text_after_id.redo())
        self.text_after_id.bind("<Control-e>", lambda event: self._edit_after_in_external_editor())
        self.text_before_id.bind("<Control-s>", lambda event: self.update_before())
        self.text_before_id.bind("<Control-g>", lambda event: self.update_before())
        self.text_after_id.bind("<Control-s>", lambda event: self.update_after())
        self.text_after_id.bind("<Control-g>", lambda event: self.update_after())
        self.text_before_id.bind("<<TextModified>>", lambda event: undo_handling.update_window_title())
        self.text_after_id.bind("<<TextModified>>", lambda event: undo_handling.update_window_title())
        self.text_before_id.bind("<FocusIn>", lambda event: main_window.canvas.unbind_all("<Delete>"))
        self.text_before_id.bind(
            "<FocusOut>", lambda event: main_window.canvas.bind_all("<Delete>", lambda event: canvas_editing.delete())
        )
        self.text_after_id.bind("<FocusIn>", lambda event: main_window.canvas.unbind_all("<Delete>"))
        self.text_after_id.bind(
            "<FocusOut>", lambda event: main_window.canvas.bind_all("<Delete>", lambda event: canvas_editing.delete())
        )

        self.label_before.grid(row=0, column=0, sticky="nwe")
        self.text_before_id.grid(row=1, column=0, sticky="ew")
        self.label_after.grid(row=2, column=0, sticky="ew")
        self.text_after_id.grid(row=3, column=0, sticky="swe")

        # Create canvas window for frame and text:
        self.window_id = main_window.canvas.create_window(menu_x, menu_y, window=self.frame_id, anchor=tk.W)

        self.frame_id.bind(
            "<Button-1>",
            lambda event: move_handling_canvas_window.MoveHandlingCanvasWindow(event, self.frame_id, self.window_id),
        )
        self.label_before.bind(
            "<Button-1>",
            lambda event: move_handling_canvas_window.MoveHandlingCanvasWindow(
                event, self.label_before, self.window_id
            ),
        )
        self.label_after.bind(
            "<Button-1>",
            lambda event: move_handling_canvas_window.MoveHandlingCanvasWindow(event, self.label_after, self.window_id),
        )

        GlobalActions.dictionary[self.window_id] = self
        canvas_modify_bindings.switch_to_move_mode()

    def _edit_before_in_external_editor(self) -> None:
        self.text_before_id.edit_in_external_editor()
        self.update_before()

    def _edit_after_in_external_editor(self) -> None:
        self.text_after_id.edit_in_external_editor()
        self.update_after()

    def update_before(self) -> None:
        # Update self.text_before_content, so that the <Leave>-check in deactivate_frame() does not signal a design-
        # change and that save_in_file_new() already reads the new text, entered into the textbox before Control-s/g.
        # To ensure this, save_in_file_new() waits for idle.
        self.text_before_content = self.text_before_id.get("1.0", tk.END)

    def update_after(self) -> None:
        # Update self.text_after_content, so that the <Leave>-check in deactivate_frame() does not signal a design-
        # change and that save_in_file_new() already reads the new text, entered into the textbox before Control-s/g.
        # To ensure this, save_in_file_new() waits for idle.
        self.text_after_content = self.text_after_id.get("1.0", tk.END)

    def tag(self) -> None:
        main_window.canvas.itemconfigure(
            self.window_id, tag="global_actions" + str(GlobalActions.global_actions_number)
        )

    def activate_frame(self) -> None:
        self.activate_window()
        self.text_before_content = self.text_before_id.get("1.0", tk.END)
        self.text_after_content = self.text_after_id.get("1.0", tk.END)

    def activate_window(self) -> None:
        self.frame_id.configure(borderwidth=1, style="GlobalActionsWindowSelected.TFrame")
        self.label_before.configure(style="GlobalActionsWindowSelected.TLabel")
        self.label_after.configure(style="GlobalActionsWindowSelected.TLabel")

    def deactivate_frame(self) -> None:
        self.deactivate_window()
        self.frame_id.focus()  # "unfocus" the Text, when the mouse leaves the text.
        if self.text_before_id.get("1.0", tk.END) != self.text_before_content:
            undo_handling.design_has_changed()
        if self.text_after_id.get("1.0", tk.END) != self.text_after_content:
            undo_handling.design_has_changed()

    def deactivate_window(self) -> None:
        self.frame_id.configure(borderwidth=0, style="GlobalActionsWindow.TFrame")
        self.label_before.configure(style="GlobalActionsWindow.TLabel")
        self.label_after.configure(style="GlobalActionsWindow.TLabel")

    def move_to(self, event_x: float, event_y: float, first: bool) -> None:
        if first:
            # Calculate the difference between the "anchor" point and the event:
            coords = main_window.canvas.coords(self.window_id)
            self.difference_x, self.difference_y = -event_x + coords[0], -event_y + coords[1]
        # Keep the distance between event and anchor point constant:
        event_x, event_y = event_x + self.difference_x, event_y + self.difference_y
        main_window.canvas.coords(self.window_id, event_x, event_y)
