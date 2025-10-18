"""
This class handles "state-comments".
"""

import tkinter as tk
from tkinter import ttk

import canvas_editing
import custom_text
import main_window
import move_handling_canvas_window
import undo_handling


class StateComment:
    """
    This class handles "state-comments".
    """

    dictionary = {}

    def __init__(
        self,
        menu_x,
        menu_y,  # coordinates for placing the StateComment-Window "near" the clicked menu-entry
        height,
        width,
        padding,
    ) -> None:
        self.text_content = None
        self.difference_x = 0
        self.difference_y = 0
        self.line_id = None
        self.line_coords = []
        # Create frame:
        self.frame_id = ttk.Frame(
            main_window.canvas, relief=tk.FLAT, borderwidth=0, style="StateActionsWindow.TFrame", padding=padding
        )
        self.frame_id.bind("<Enter>", lambda event: self.activate_frame())
        self.frame_id.bind("<Leave>", lambda event: self.deactivate_frame())
        # Create label object inside frame:
        self.label_id = ttk.Label(
            self.frame_id,
            text="State-Comment: ",
            font=("Arial", int(canvas_editing.label_fontsize)),
            style="StateActionsWindow.TLabel",
        )
        self.label_id.bind("<Enter>", lambda event: self.activate_window())
        self.label_id.bind("<Leave>", lambda event: self.deactivate_window())
        # Create text object inside frame:
        self.text_id = custom_text.CustomText(
            self.frame_id,
            text_type="comment",
            height=height,
            width=width,
            undo=True,
            maxundo=-1,
            font=("Courier", int(canvas_editing.fontsize)),
            foreground="blue",
        )
        self.text_id.bind("<Control-z>", lambda event: self.text_id.undo())
        self.text_id.bind("<Control-Z>", lambda event: self.text_id.redo())
        self.text_id.bind("<Control-e>", lambda event: self._edit_in_external_editor())
        self.text_id.bind("<Control-s>", lambda event: self.update_text())
        self.text_id.bind("<Control-g>", lambda event: self.update_text())
        self.text_id.bind("<<TextModified>>", lambda event: undo_handling.update_window_title())
        self.text_id.bind("<FocusIn>", lambda event: main_window.canvas.unbind_all("<Delete>"))
        self.text_id.bind(
            "<FocusOut>", lambda event: main_window.canvas.bind_all("<Delete>", lambda event: canvas_editing.delete())
        )

        self.label_id.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E))
        self.text_id.grid(column=0, row=1, sticky=(tk.S, tk.W, tk.E))

        # Create canvas window for frame and text:
        self.window_id = main_window.canvas.create_window(menu_x + 100, menu_y, window=self.frame_id, anchor=tk.W)

        self.frame_id.bind(
            "<Button-1>",
            lambda event: move_handling_canvas_window.MoveHandlingCanvasWindow(event, self.frame_id, self.window_id),
        )
        self.label_id.bind(
            "<Button-1>",
            lambda event: move_handling_canvas_window.MoveHandlingCanvasWindow(event, self.label_id, self.window_id),
        )
        StateComment.dictionary[self.window_id] = self  # Store the object-reference with the Canvas-id as key.

    def _edit_in_external_editor(self):
        self.text_id.edit_in_external_editor()
        self.update_text()

    def update_text(self) -> None:
        # Update self.text_content, so that the <Leave>-check in deactivate_frame() does not signal a design-change and
        # that save_in_file_new() already reads the new text, entered into the textbox before Control-s/g.
        # To ensure this, save_in_file_new() waits for idle.
        self.text_content = self.text_id.get("1.0", tk.END)

    def activate_frame(self) -> None:
        self.activate_window()
        self.text_content = self.text_id.get("1.0", tk.END)

    def activate_window(self) -> None:
        self.frame_id.configure(borderwidth=1, style="StateActionsWindowSelected.TFrame")
        self.label_id.configure(style="StateActionsWindowSelected.TLabel")

    def deactivate_frame(self) -> None:
        self.deactivate_window()
        self.frame_id.focus()  # "unfocus" the Text, when the mouse leaves the text.
        if self.text_id.get("1.0", tk.END) != self.text_content:
            undo_handling.design_has_changed()

    def deactivate_window(self) -> None:
        self.frame_id.configure(borderwidth=0, style="StateActionsWindow.TFrame")
        self.label_id.configure(style="StateActionsWindow.TLabel")

    def move_to(self, event_x, event_y, first) -> None:
        if first:
            # Calculate the difference between the "anchor" point and the event:
            coords = main_window.canvas.coords(self.window_id)
            self.difference_x, self.difference_y = -event_x + coords[0], -event_y + coords[1]
        # Keep the distance between event and anchor point constant:
        event_x, event_y = event_x + self.difference_x, event_y + self.difference_y
        main_window.canvas.coords(self.window_id, event_x, event_y)
        # Move the connection line:
        window_tags = main_window.canvas.gettags(self.window_id)
        for t in window_tags:
            if t.endswith("_comment"):
                line_tag = t + "_line"
                self.line_coords = main_window.canvas.coords(line_tag)
                self.line_coords[0] = event_x
                self.line_coords[1] = event_y
                main_window.canvas.coords(line_tag, self.line_coords)

    def add_line(self, menu_x, menu_y, state_identifier) -> None:  # Called by state_handling.evaluate_menu().
        # Draw a line from the state to the comment block which is added to the state:
        state_coords = main_window.canvas.coords(state_identifier)
        self.line_id = main_window.canvas.create_line(
            menu_x + 100,
            menu_y,
            (state_coords[2] + state_coords[0]) / 2,
            (state_coords[3] + state_coords[1]) / 2,
            dash=(2, 2),
            tag=state_identifier + "_comment_line",
        )
        main_window.canvas.tag_lower(self.line_id, state_identifier)

    def tag(self, state_identifier) -> None:  # Called by state_handling.evaluate_menu().
        main_window.canvas.addtag_withtag(state_identifier + "_comment_line_end", state_identifier)
        main_window.canvas.itemconfigure(
            self.window_id, tag=(state_identifier + "_comment", state_identifier + "_comment_line_start")
        )
