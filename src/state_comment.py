"""
This class handles "state-comments".
"""

import tkinter as tk
from tkinter import ttk

import canvas_editing
import custom_text
import main_window
import undo_handling


class StateComment:
    dictionary = {}

    def __init__(
        self,
        menu_x,
        menu_y,  # coordinates for placing the StateComment-Window "near" the clicked menu-entry
        height,
        width,
        padding,
    ):
        # Create frame:
        self.frame_id = ttk.Frame(
            main_window.canvas, relief=tk.FLAT, style="StateActionsWindow.TFrame", padding=padding
        )
        self.frame_id.bind("<Enter>", lambda event, self=self: self.activate())
        self.frame_id.bind("<Leave>", lambda event, self=self: self.deactivate())
        # Create label object inside frame:
        self.label_id = ttk.Label(
            self.frame_id,
            text="State-Comment: ",
            font=("Arial", int(canvas_editing.label_fontsize)),
            style="StateActionsWindow.TLabel",
        )
        # Create text object inside frame:
        self.text = ""
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
        self.text_id.bind("<<TextModified>>", lambda event: undo_handling.update_window_title())
        self.text_id.bind("<FocusIn>", lambda event: main_window.canvas.unbind_all("<Delete>"))
        self.text_id.bind(
            "<FocusOut>", lambda event: main_window.canvas.bind_all("<Delete>", lambda event: canvas_editing.delete())
        )
        # Create canvas window for frame and text:
        self.window_id = main_window.canvas.create_window(menu_x + 100, menu_y, window=self.frame_id, anchor=tk.W)
        main_window.canvas.tag_bind(
            self.window_id, "<Enter>", lambda event: self.__draw_polygon_around_window()
        )  # See description in condition_action_handling.py.
        StateComment.dictionary[self.window_id] = self  # Store the object-reference with the Canvas-id as key.
        self.label_id.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E))
        self.text_id.grid(column=0, row=1, sticky=(tk.S, tk.W, tk.E))
        self.difference_x = 0
        self.difference_y = 0
        self.move_rectangle = None
        self.line_id = None
        self.line_coords = []

    def activate(self):
        self.frame_id.configure(style="Window.TFrame", padding=3)  # increase the width of the line around the box
        self.text = self.text_id.get("1.0", tk.END)

    def deactivate(self):
        self.frame_id.configure(style="Window.TFrame", padding=1)  # decrease the width of the line around the box
        self.frame_id.focus()  # "unfocus" the Text, when the mouse leaves the text.
        if self.text_id.get("1.0", tk.END) != self.text:
            undo_handling.design_has_changed()

    def __draw_polygon_around_window(self):
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
            polygon_coords, width=1, fill="blue", tag="polygon_for_move"
        )
        main_window.canvas.tag_bind(
            self.move_rectangle, "<Leave>", lambda event: main_window.canvas.delete(self.move_rectangle)
        )

    def move_to(self, event_x, event_y, first, _):
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
        # Move the connection line:
        window_tags = main_window.canvas.gettags(self.window_id)
        for t in window_tags:
            if t.endswith("_comment"):
                line_tag = t + "_line"
                self.line_coords = main_window.canvas.coords(line_tag)
                self.line_coords[0] = event_x
                self.line_coords[1] = event_y
                main_window.canvas.coords(line_tag, self.line_coords)

    def add_line(self, menu_x, menu_y, state_identifier):  # Called by state_handling.evaluate_menu().
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
        main_window.canvas.tag_bind(self.line_id, "<Enter>", lambda event, self=self: self.activate_line())
        main_window.canvas.tag_bind(self.line_id, "<Leave>", lambda event, self=self: self.deactivate_line())
        main_window.canvas.tag_lower(self.line_id, state_identifier)

    def tag(self, state_identifier):  # Called by state_handling.evaluate_menu().
        main_window.canvas.addtag_withtag(state_identifier + "_comment_line_end", state_identifier)
        main_window.canvas.itemconfigure(
            self.window_id, tag=(state_identifier + "_comment", state_identifier + "_comment_line_start")
        )

    def activate_line(self):
        main_window.canvas.itemconfigure(self.line_id, width=3)  # increase the width of the line around the box

    def deactivate_line(self):
        main_window.canvas.itemconfigure(self.line_id, width=1)  # decrease the width of the line around the box
