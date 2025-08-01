"""
Handles the combinatorial default actions for all states.
"""

import tkinter as tk
from tkinter import ttk

import canvas_editing
import canvas_modify_bindings
import custom_text
import main_window
import undo_handling


class StateActionsDefault:
    """
    Handles the combinatorial default actions for all states.
    """

    dictionary: dict[int, "StateActionsDefault"] = {}

    def __init__(self, menu_x, menu_y, height, width, padding) -> None:
        self.text_content: str | None = None
        self.frame_id = ttk.Frame(
            main_window.canvas, relief=tk.FLAT, padding=padding, style="StateActionsWindow.TFrame"
        )  # , borderwidth=10)
        self.frame_id.bind("<Enter>", lambda event, self=self: self.activate())
        self.frame_id.bind("<Leave>", lambda event, self=self: self.deactivate())
        # self.frame_id.bind("<Button-1>", self.hallo)
        # Create label object inside frame:
        self.label = ttk.Label(
            self.frame_id,
            text="Default state actions (combinatorial): ",
            font=("Arial", int(canvas_editing.label_fontsize)),
            style="StateActionsWindow.TLabel",
        )
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

        self.label.grid(row=0, column=0, sticky=f"{tk.N}{tk.W}{tk.E}")
        self.text_id.grid(row=1, column=0, sticky=f"{tk.E}{tk.W}")

        self.difference_x = 0
        self.difference_y = 0
        self.move_rectangle: int | None = None

        # Create canvas window for frame and text:
        self.window_id = main_window.canvas.create_window(menu_x, menu_y, window=self.frame_id, anchor=tk.W)
        main_window.canvas.tag_bind(
            self.window_id, "<Enter>", lambda event: self.__draw_polygon_around_window()
        )  # See description in condition_action_handling.py.
        StateActionsDefault.dictionary[self.window_id] = self
        canvas_modify_bindings.switch_to_move_mode()

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
            polygon_coords[0],
            polygon_coords[1],
            polygon_coords[2],
            polygon_coords[3],
            polygon_coords[4],
            polygon_coords[5],
            polygon_coords[6],
            polygon_coords[7],
            width=1,
            fill="cyan2",
            tags="polygon_for_move",
        )
        if self.move_rectangle is not None:
            main_window.canvas.tag_bind(
                self.move_rectangle,
                "<Leave>",
                lambda event: main_window.canvas.delete(self.move_rectangle)
                if self.move_rectangle is not None
                else None,
            )

    def tag(self) -> None:
        main_window.canvas.itemconfigure(self.window_id, tag="state_actions_default")

    def update_text(self) -> None:
        # Update self.text_content, so that the <Leave>-check in deactivate() does not signal a design-change and
        # that save_in_file_new() already reads the new text, entered into the textbox before Control-s/g.
        # To ensure this, save_in_file_new() waits for idle.
        self.text_content = self.text_id.get("1.0", tk.END)

    def activate(self) -> None:
        self.frame_id.configure(padding=3)  # increase the width of the line around the box
        self.text_content = self.text_id.get("1.0", tk.END)

    def deactivate(self) -> None:
        self.frame_id.configure(padding=1)  # decrease the width of the line around the box
        self.frame_id.focus()  # "unfocus" the Text, when the mouse leaves the text.
        if self.text_id.get("1.0", tk.END) != self.text_content:
            undo_handling.design_has_changed()

    def move_to(self, event_x, event_y, first, last) -> None:
        if self.move_rectangle is not None:
            main_window.canvas.delete(self.move_rectangle)
        self.frame_id.configure(padding=1)  # decrease the width of the line around the box
        if first:
            self.frame_id.configure(padding=4)  # increase the width of the line around the box
            # Calculate the difference between the "anchor" point and the event:
            coords = main_window.canvas.coords(self.window_id)
            self.difference_x, self.difference_y = -event_x + coords[0], -event_y + coords[1]
        # Keep the distance between event and anchor point constant:
        event_x, event_y = event_x + self.difference_x, event_y + self.difference_y
        main_window.canvas.coords(self.window_id, event_x, event_y)
