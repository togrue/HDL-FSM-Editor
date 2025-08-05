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
import undo_handling


class GlobalActions:
    """
    Handles the global actions window in the diagram.
    """

    global_actions_number: int = 1
    dictionary: dict[int, "GlobalActions"] = {}

    def __init__(self, menu_x: float, menu_y: float, height: int, width: int, padding: int) -> None:
        self.frame_id = ttk.Frame(
            main_window.canvas, relief=tk.FLAT, padding=padding, style="GlobalActionsWindow.TFrame"
        )
        self.text_before_content: Optional[str] = None
        self.text_after_content: Optional[str] = None
        self.frame_id.bind("<Enter>", lambda event, self=self: self.activate())
        self.frame_id.bind("<Leave>", lambda event, self=self: self.deactivate())
        # Create label object inside frame:
        self.label_before = ttk.Label(
            self.frame_id,
            text="Global actions clocked (executed before running the state machine):",
            font=("Arial", int(canvas_editing.label_fontsize)),
            style="GlobalActionsWindow.TLabel",
        )
        self.label_after = ttk.Label(
            self.frame_id,
            text="Global actions clocked (executed after running the state machine):",
            font=("Arial", int(canvas_editing.label_fontsize)),
            style="GlobalActionsWindow.TLabel",
        )
        self.text_before_id = custom_text.CustomText(
            self.frame_id,
            text_type="action",
            height=height,
            width=width,
            undo=True,
            maxundo=-1,
            font=("Courier", int(canvas_editing.fontsize)),
        )
        self.text_after_id = custom_text.CustomText(
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
        self.text_after_id.bind("<Control-z>", lambda event: self.text_after_id.undo())
        self.text_after_id.bind("<Control-Z>", lambda event: self.text_after_id.redo())
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
        self.difference_x = 0
        self.difference_y = 0
        self.move_rectangle: Optional[int] = None

        # Create canvas window for frame and text:
        self.window_id = main_window.canvas.create_window(menu_x, menu_y, window=self.frame_id, anchor=tk.W)
        main_window.canvas.tag_bind(
            self.window_id, "<Enter>", lambda event: self.__draw_polygon_around_window()
        )  # See description in condition_action_handling.py.
        GlobalActions.dictionary[self.window_id] = self
        canvas_modify_bindings.switch_to_move_mode()

    def update_before(self) -> None:
        # Update self.text_before_content, so that the <Leave>-check in deactivate() does not signal a design-change and
        # that save_in_file_new() already reads the new text, entered into the textbox before Control-s/g.
        # To ensure this, save_in_file_new() waits for idle.
        self.text_before_content = self.text_before_id.get("1.0", tk.END)

    def update_after(self) -> None:
        # Update self.text_after_content, so that the <Leave>-check in deactivate() does not signal a design-change and
        # that save_in_file_new() already reads the new text, entered into the textbox before Control-s/g.
        # To ensure this, save_in_file_new() waits for idle.
        self.text_after_content = self.text_after_id.get("1.0", tk.END)

    def __draw_polygon_around_window(self) -> None:
        bbox_coords = main_window.canvas.bbox(self.window_id)
        polygon_coords = []
        polygon_coords.append(bbox_coords[0] - 3)
        polygon_coords.append(bbox_coords[1] - 3)
        polygon_coords.append(bbox_coords[2] + 3)
        polygon_coords.append(bbox_coords[1] - 3)
        polygon_coords.append(bbox_coords[2] + 3)
        polygon_coords.append(bbox_coords[3] + 3)
        polygon_coords.append(bbox_coords[0] - 3)
        polygon_coords.append(bbox_coords[3] + 3)
        # It is "fill=<color> used instead of "width=3, outline=<color> as then the 4 edges are sharp and not round:
        self.move_rectangle = main_window.canvas.create_polygon(
            polygon_coords, width=1, fill="PaleGreen2", tags="polygon_for_move"
        )
        # make a captured local copy, so that move_rect gets the same id in the lambda function.
        move_rect = self.move_rectangle
        main_window.canvas.tag_bind(move_rect, "<Leave>", lambda event: main_window.canvas.delete(move_rect))

    def tag(self) -> None:
        main_window.canvas.itemconfigure(
            self.window_id, tag="global_actions" + str(GlobalActions.global_actions_number)
        )

    def activate(self) -> None:
        self.frame_id.configure(padding=3)  # increase the width of the line around the box
        self.text_before_content = self.text_before_id.get("1.0", tk.END)
        self.text_after_content = self.text_after_id.get("1.0", tk.END)

    def deactivate(self) -> None:
        self.frame_id.configure(padding=1)  # decrease the width of the line around the box
        self.frame_id.focus()  # "unfocus" the Text, when the mouse leaves the text.
        # self.text_before_id.format() # needed sometimes, when undo or redo happened.
        # self.text_after_id.format()
        if self.text_before_id.get("1.0", tk.END) != self.text_before_content:
            undo_handling.design_has_changed()
        if self.text_after_id.get("1.0", tk.END) != self.text_after_content:
            undo_handling.design_has_changed()

    def move_to(self, event_x: float, event_y: float, first: bool, last: bool) -> None:
        assert self.move_rectangle is not None
        main_window.canvas.delete(self.move_rectangle)
        self.frame_id.configure(padding=1)  # Set the width of the line around the box
        if first:
            self.frame_id.configure(padding=4)  # increase the width of the line around the box
            # Calculate the difference between the "anchor" point and the event:
            coords = main_window.canvas.coords(self.window_id)
            self.difference_x, self.difference_y = -event_x + coords[0], -event_y + coords[1]
        # Keep the distance between event and anchor point constant:
        event_x, event_y = event_x + self.difference_x, event_y + self.difference_y
        # if last==True:
        #     event_x = canvas_editing.state_radius * round(event_x/canvas_editing.state_radius)
        #     event_y = canvas_editing.state_radius * round(event_y/canvas_editing.state_radius)
        main_window.canvas.coords(self.window_id, event_x, event_y)
