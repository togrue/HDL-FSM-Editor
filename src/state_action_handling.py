"""
Handles the state action of a single state.
"""

import tkinter as tk
from tkinter import ttk

import canvas_editing
import undo_handling
import custom_text
import main_window


class MyText:
    mytext_id = 0
    mytext_dict = {}

    def __init__(self, menu_x, menu_y, height, width, padding, increment):
        if increment is True:
            MyText.mytext_id += 1
        self.difference_x = 0
        self.difference_y = 0
        self.move_rectangle = None
        self.line_id = None
        self.text_content = None
        # Create frame:
        self.frame_id = ttk.Frame(
            main_window.canvas,
            relief=tk.FLAT,
            padding=padding,
            style="StateActionsWindow.TFrame",
        )
        self.frame_id.bind("<Enter>", lambda event, self=self: self.activate())
        self.frame_id.bind("<Leave>", lambda event, self=self: self.deactivate())
        # Create label object inside frame:
        self.label_id = ttk.Label(
            self.frame_id,
            text="State actions (combinatorial): ",
            font=("Arial", int(canvas_editing.label_fontsize)),
            style="StateActionsWindow.TLabel",
        )
        # Create text object inside frame:
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
        self.text_id.bind(
            "<<TextModified>>", lambda event: undo_handling.modify_window_title()
        )
        self.text_id.bind(
            "<FocusIn>", lambda event: main_window.canvas.unbind_all("<Delete>")
        )
        self.text_id.bind(
            "<FocusOut>",
            lambda event: main_window.canvas.bind_all(
                "<Delete>", lambda event: canvas_editing.delete()
            ),
        )
        # Create canvas window for frame and text:
        self.window_id = main_window.canvas.create_window(
            menu_x + 100, menu_y, window=self.frame_id, anchor=tk.W
        )
        main_window.canvas.tag_bind(
            self.window_id, "<Enter>", lambda event: self.__draw_polygon_around_window()
        )  # See description in condition_action_handling.py.
        MyText.mytext_dict[self.window_id] = self
        self.label_id.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E))
        self.text_id.grid(column=0, row=1, sticky=(tk.S, tk.W, tk.E))

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
            self.move_rectangle,
            "<Leave>",
            lambda event: main_window.canvas.delete(self.move_rectangle),
        )

    def tag(self):
        main_window.canvas.itemconfigure(
            self.window_id,
            tag=(
                "state_action" + str(MyText.mytext_id),
                "connection" + str(MyText.mytext_id) + "_start",
            ),
        )

    def connect_to_state(self, menu_x, menu_y, state_id):
        # Draw a line from the state to the action block which is added to the state:
        state_coords = main_window.canvas.coords(state_id)
        main_window.canvas.addtag_withtag(
            "connection" + str(MyText.mytext_id) + "_end", state_id
        )
        state_tags = main_window.canvas.gettags(state_id)
        self.line_id = main_window.canvas.create_line(
            menu_x + 100,
            menu_y,
            (state_coords[2] + state_coords[0]) / 2,
            (state_coords[3] + state_coords[1]) / 2,
            dash=(2, 2),
            tag=("connection" + str(MyText.mytext_id), "connected_to_" + state_tags[0]),
        )
        main_window.canvas.tag_bind(
            self.line_id, "<Enter>", lambda event, self=self: self.activate_line()
        )
        main_window.canvas.tag_bind(
            self.line_id, "<Leave>", lambda event, self=self: self.deactivate_line()
        )
        main_window.canvas.tag_lower(self.line_id, state_id)

    def update_text(self):
        # Update self.text_content, so that the <Leave>-check in deactivate() does not signal a design-change and
        # that save_in_file_new() already reads the new text, entered into the textbox before Control-s/g.
        # To ensure this, save_in_file_new() waits for idle.
        self.text_content = self.text_id.get("1.0", tk.END)

    def activate(self):
        self.frame_id.configure(
            style="Window.TFrame", padding=3
        )  # increase the width of the line around the box
        self.text_content = self.text_id.get("1.0", tk.END)

    def deactivate(self):
        self.frame_id.configure(
            style="Window.TFrame", padding=1
        )  # decrease the width of the line around the box
        self.frame_id.focus()  # "unfocus" the Text, when the mouse leaves the text.
        if self.text_id.get("1.0", tk.END) != self.text_content:
            undo_handling.design_has_changed()

    def activate_line(self):
        main_window.canvas.itemconfigure(
            self.line_id, width=3
        )  # increase the width of the line around the box

    def deactivate_line(self):
        main_window.canvas.itemconfigure(
            self.line_id, width=1
        )  # decrease the width of the line around the box

    def move_to(self, event_x, event_y, first, last):
        main_window.canvas.delete(self.move_rectangle)
        self.frame_id.configure(
            padding=1
        )  # decrease the width of the line around the box
        if first:
            self.frame_id.configure(
                padding=4
            )  # increase the width of the line around the box
            # Calculate the difference between the "anchor" point and the event:
            coords = main_window.canvas.coords(self.window_id)
            self.difference_x, self.difference_y = (
                -event_x + coords[0],
                -event_y + coords[1],
            )
        # Keep the distance between event and anchor point constant:
        event_x, event_y = event_x + self.difference_x, event_y + self.difference_y
        # if last==True:
        #     event_x = canvas_editing.state_radius * round(event_x/canvas_editing.state_radius)
        #     event_y = canvas_editing.state_radius * round(event_y/canvas_editing.state_radius)
        main_window.canvas.coords(self.window_id, event_x, event_y)
        # Move the connection line:
        window_tags = main_window.canvas.gettags(self.window_id)
        for t in window_tags:
            if t.startswith("connection"):
                line_tag = t[:-6]
                line_coords = main_window.canvas.coords(line_tag)
                line_coords[0] = event_x
                line_coords[1] = event_y
                main_window.canvas.coords(line_tag, line_coords)
