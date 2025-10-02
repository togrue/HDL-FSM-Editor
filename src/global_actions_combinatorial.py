"""
Class for combinatorial actions independent from the state machine
"""

import tkinter as tk
from tkinter import ttk

import canvas_editing
import canvas_modify_bindings
import custom_text
import main_window
import move_handling_canvas_window
import undo_handling


class GlobalActionsCombinatorial:
    """
    Class for combinatorial actions independent from the state machine
    """

    dictionary = {}

    def __init__(self, menu_x, menu_y, height, width, padding) -> None:
        self.text_content = None
        self.difference_x = 0
        self.difference_y = 0

        self.frame_id = ttk.Frame(
            main_window.canvas, relief=tk.FLAT, borderwidth=0, padding=padding, style="GlobalActionsWindow.TFrame"
        )
        self.frame_id.bind("<Enter>", lambda event: self.activate_frame())
        self.frame_id.bind("<Leave>", lambda event: self.deactivate_frame())
        # Create label object inside frame:
        self.label = ttk.Label(
            self.frame_id,
            text="Global actions combinatorial: ",
            font=("Arial", int(canvas_editing.label_fontsize)),
            style="GlobalActionsWindow.TLabel",
        )
        self.label.bind("<Enter>", lambda event: self.activate_window())
        self.label.bind("<Leave>", lambda event: self.deactivate_window())
        self.text_id = custom_text.CustomText(
            self.frame_id,
            text_type="action",
            height=height,
            width=width,
            undo=True,
            maxundo=-1,
            font=("Courier", int(canvas_editing.fontsize)),
        )
        self.text_id.bind("<Control-z>", lambda event: self.text_id.undo())
        self.text_id.bind("<Control-Z>", lambda event: self.text_id.redo())
        self.text_id.bind("<Control-s>", lambda event: self.update_text())
        self.text_id.bind("<Control-g>", lambda event: self.update_text())
        self.text_id.bind("<<TextModified>>", lambda event: undo_handling.update_window_title())
        self.text_id.bind("<FocusIn>", lambda event: main_window.canvas.unbind_all("<Delete>"))
        self.text_id.bind(
            "<FocusOut>", lambda event: main_window.canvas.bind_all("<Delete>", lambda event: canvas_editing.delete())
        )

        self.label.grid(row=0, column=0, sticky=(tk.N, tk.W, tk.E))
        self.text_id.grid(row=1, column=0, sticky=(tk.E, tk.W))

        # Create canvas window for frame and text:
        self.window_id = main_window.canvas.create_window(menu_x, menu_y, window=self.frame_id, anchor=tk.W)

        self.frame_id.bind(
            "<Button-1>",
            lambda event: move_handling_canvas_window.MoveHandlingCanvasWindow(event, self.frame_id, self.window_id),
        )
        self.label.bind(
            "<Button-1>",
            lambda event: move_handling_canvas_window.MoveHandlingCanvasWindow(event, self.label, self.window_id),
        )
        self.frame_id.lower()
        GlobalActionsCombinatorial.dictionary[self.window_id] = self
        canvas_modify_bindings.switch_to_move_mode()

    def update_text(self):
        # Update self.text_content, so that the <Leave>-check in deactivate() does not signal a design-change and
        # that save_in_file_new() already reads the new text, entered into the textbox before Control-s/g.
        # To ensure this, save_in_file_new() waits for idle.
        self.text_content = self.text_id.get("1.0", tk.END)

    def tag(self) -> None:
        main_window.canvas.itemconfigure(self.window_id, tag="global_actions_combinatorial1")

    def activate_frame(self) -> None:
        self.activate_window()
        self.text = self.text_id.get("1.0", tk.END)

    def activate_window(self) -> None:
        self.frame_id.configure(borderwidth=1, style="GlobalActionsWindowSelected.TFrame")
        self.label.configure(style="GlobalActionsWindowSelected.TLabel")

    def deactivate_frame(self) -> None:
        self.deactivate_window()
        self.frame_id.focus()  # "unfocus" the Text, when the mouse leaves the text.
        if self.text_id.get("1.0", tk.END) != self.text_content:
            undo_handling.design_has_changed()

    def deactivate_window(self) -> None:
        self.frame_id.configure(borderwidth=0, style="GlobalActionsWindow.TFrame")
        self.label.configure(style="GlobalActionsWindow.TLabel")

    def move_to(self, event_x, event_y, first, _) -> None:
        if first:
            # Calculate the difference between the "anchor" point and the event:
            coords = main_window.canvas.coords(self.window_id)
            self.difference_x, self.difference_y = -event_x + coords[0], -event_y + coords[1]
        # Keep the distance between event and anchor point constant:
        event_x, event_y = event_x + self.difference_x, event_y + self.difference_y
        main_window.canvas.coords(self.window_id, event_x, event_y)
