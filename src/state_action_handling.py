"""
Handles the state action of a single state.
"""

import tkinter as tk
from tkinter import ttk

import canvas_delete
import custom_text
import move_handling_canvas_window
import undo_handling
from project_manager import project_manager


class MyText:
    """
    Handles the state action of a single state.
    """

    mytext_id = 0
    mytext_dict = {}

    def __init__(self, menu_x, menu_y, height, width, padding, increment) -> None:
        if increment is True:
            MyText.mytext_id += 1
        self.text_content = None
        self.difference_x = 0
        self.difference_y = 0
        self.line_id = None
        # Create frame:
        self.frame_id = ttk.Frame(
            project_manager.canvas, relief=tk.FLAT, borderwidth=0, padding=padding, style="StateActionsWindow.TFrame"
        )
        self.frame_id.bind("<Enter>", lambda event: self.activate_frame())
        self.frame_id.bind("<Leave>", lambda event: self.deactivate_frame())
        # Create label object inside frame:
        self.label_id = ttk.Label(
            self.frame_id,
            text="State actions (combinatorial): ",
            font=("Arial", int(project_manager.label_fontsize)),
            style="StateActionsWindow.TLabel",
        )
        self.label_id.bind("<Enter>", lambda event: self.activate_window())
        self.label_id.bind("<Leave>", lambda event: self.deactivate_window())
        # Create text object inside frame:
        self.text_id = custom_text.CustomText(
            self.frame_id,
            text_type="action",
            height=height,
            width=width,
            undo=True,
            maxundo=-1,
            font=("Courier", int(project_manager.fontsize)),
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
            lambda event: project_manager.canvas.bind_all(
                "<Delete>", lambda event: canvas_delete.CanvasDelete(project_manager.canvas)
            ),
        )

        self.label_id.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E))
        self.text_id.grid(column=0, row=1, sticky=(tk.S, tk.W, tk.E))

        # Create canvas window for frame and text:
        self.window_id = project_manager.canvas.create_window(menu_x + 100, menu_y, window=self.frame_id, anchor=tk.W)

        self.frame_id.bind(
            "<Button-1>",
            lambda event: move_handling_canvas_window.MoveHandlingCanvasWindow(event, self.frame_id, self.window_id),
        )
        self.label_id.bind(
            "<Button-1>",
            lambda event: move_handling_canvas_window.MoveHandlingCanvasWindow(event, self.label_id, self.window_id),
        )

        MyText.mytext_dict[self.window_id] = self

    def tag(self) -> None:
        project_manager.canvas.itemconfigure(
            self.window_id,
            tag=("state_action" + str(MyText.mytext_id), "connection" + str(MyText.mytext_id) + "_start"),
        )

    def connect_to_state(self, menu_x, menu_y, state_id) -> None:
        # Draw a line from the state to the action block which is added to the state:
        state_coords = project_manager.canvas.coords(state_id)
        project_manager.canvas.addtag_withtag("connection" + str(MyText.mytext_id) + "_end", state_id)
        state_tags = project_manager.canvas.gettags(state_id)
        self.line_id = project_manager.canvas.create_line(
            menu_x + 100,
            menu_y,
            (state_coords[2] + state_coords[0]) / 2,
            (state_coords[3] + state_coords[1]) / 2,
            dash=(2, 2),
            tag=("connection" + str(MyText.mytext_id), "connected_to_" + state_tags[0]),
        )
        project_manager.canvas.tag_lower(self.line_id, state_id)

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
            coords = project_manager.canvas.coords(self.window_id)
            self.difference_x, self.difference_y = -event_x + coords[0], -event_y + coords[1]
        # Keep the distance between event and anchor point constant:
        event_x, event_y = event_x + self.difference_x, event_y + self.difference_y
        project_manager.canvas.coords(self.window_id, event_x, event_y)
        # Move the connection line:
        window_tags = project_manager.canvas.gettags(self.window_id)
        for t in window_tags:
            if t.startswith("connection"):
                line_tag = t[:-6]
                line_coords = project_manager.canvas.coords(line_tag)
                line_coords[0] = event_x
                line_coords[1] = event_y
                project_manager.canvas.coords(line_tag, line_coords)
