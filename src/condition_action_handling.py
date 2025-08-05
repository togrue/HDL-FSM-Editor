"""
This class handles the condition&action box which can be activated for each transition.

A condition&action box which has only an condition and no action (or vice versa) shows only the condition.
When this condition&action box is entered by the mouse pointer it increases and shows also the action-entry.
This increasing is triggered by a enter-binding of the surrounding frame of the condition&action box.
The enter-binding of this frame is removed at entering in order to prevent the enter-binding from being
senseless triggered again when the box is left.
At entering the condition&action box a enter-canvas-binding is defined for the way back.
When the condition&action box is left the enter-canvas-binding is triggered and unbinds itself and
defines the enter-binding of the surrounding frame again.
When the mouse-pointer is moved slow, these events happen in this order:
1. Enter the canvas-window of the condition&action box (the blue polygon arround the window is drawn to
   signal that it can be moved now)
2. Leave the polygon (which deletes the polygon)
3. Enter the canvas-frame (which surrounds the canvas-widgets of the condition&action box)
4. Enter the canvas (when leaving the condition&action box)
Depending on the mouse-speed when the condition&action box is entered, the event 1, 2 or 3 may be missing.
If event 2 is missing, then the polygon exists under the extended condition&action box.
That is the reason, why the polygon must always also be removed at event 4.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

import canvas_editing
import custom_text
import main_window
import undo_handling


class ConditionAction:
    """This class handles the condition&action box which can be activated for each transition."""

    conditionaction_id: int = 0
    dictionary: dict[int, "ConditionAction"] = {}

    def __init__(
        self,
        menu_x: float,
        menu_y: float,
        connected_to_reset_entry: bool,
        height: int,
        width: int,
        padding: int,
        increment: bool,
    ) -> None:
        if increment is True:
            ConditionAction.conditionaction_id += 1
        self.difference_x = 0
        self.difference_y = 0
        self.line_id: Optional[int] = None
        self.line_coords: Optional[list[float]] = None
        self.canvas_enter_func_id: Optional[str] = None
        self.window_enter_func_id: str = ""
        self.debug_events = False
        self.action_text: Optional[str] = None
        self.condition_text: Optional[str] = None
        self.move_rectangle: Optional[int] = None
        # Create frame:
        self.frame_id = ttk.Frame(main_window.canvas, relief=tk.FLAT, padding=padding, style="Window.TFrame")
        self.condition_action_enter_func_id = self.frame_id.bind("<Enter>", lambda event: self.enter_box())

        # Create objects inside frame:
        if connected_to_reset_entry:
            label_action_text = "Transition actions (asynchronous):"
        else:
            label_action_text = "Transition actions (clocked):"
        self.condition_label = ttk.Label(
            self.frame_id, text="Transition condition: ", font=("Arial", int(canvas_editing.label_fontsize))
        )
        self.action_label = ttk.Label(
            self.frame_id, text=label_action_text, font=("Arial", int(canvas_editing.label_fontsize))
        )
        self.action_id = custom_text.CustomText(
            self.frame_id,
            text_type="action",
            takefocus=0,
            height=height,
            width=width,
            undo=True,
            maxundo=-1,
            font=("Courier", int(canvas_editing.fontsize)),
        )
        self.condition_id = custom_text.CustomText(
            self.frame_id,
            text_type="condition",
            takefocus=0,
            height=height,
            width=width,
            undo=True,
            maxundo=-1,
            font=("Courier", int(canvas_editing.fontsize)),
        )
        # Create bindings for Undo/Redo:
        self.action_id.bind("<Control-z>", lambda event: self.action_id.undo())
        self.action_id.bind("<Control-Z>", lambda event: self.action_id.redo())
        self.condition_id.bind("<Control-z>", lambda event: self.condition_id.undo())
        self.condition_id.bind("<Control-Z>", lambda event: self.condition_id.redo())
        self.action_id.bind("<Control-s>", lambda event: self.update_action())
        self.action_id.bind("<Control-g>", lambda event: self.update_action())
        self.condition_id.bind("<Control-s>", lambda event: self.update_condition())
        self.condition_id.bind("<Control-g>", lambda event: self.update_condition())
        self.action_id.bind("<<TextModified>>", lambda event: undo_handling.update_window_title())
        self.condition_id.bind("<<TextModified>>", lambda event: undo_handling.update_window_title())
        self.action_id.bind("<FocusIn>", lambda event: main_window.canvas.unbind_all("<Delete>"))
        self.action_id.bind(
            "<FocusOut>", lambda event: main_window.canvas.bind_all("<Delete>", lambda event: canvas_editing.delete())
        )
        self.condition_id.bind("<FocusIn>", lambda event: main_window.canvas.unbind_all("<Delete>"))
        self.condition_id.bind(
            "<FocusOut>", lambda event: main_window.canvas.bind_all("<Delete>", lambda event: canvas_editing.delete())
        )
        # Define layout:
        self.register_all_widgets_at_grid()
        # Create canvas window for the frame:
        self.window_id = main_window.canvas.create_window(menu_x, menu_y, window=self.frame_id, anchor=tk.W)
        self.window_enter_func_id = str(
            main_window.canvas.tag_bind(self.window_id, "<Enter>", lambda event: self.__draw_polygon_around_window())
        )
        # Create dictionary for translating the canvas-id of the canvas-window into a reference to this object:
        ConditionAction.dictionary[self.window_id] = self

    def update_action(self) -> None:
        # Update self.action_text, so that the <Leave>-check in deactivate() does not signal a design-change and
        # that save_in_file_new() already reads the new text, entered into the textbox before Control-s/g.
        # To ensure this, save_in_file_new() waits for idle.
        self.action_text = str(self.action_id.get("1.0", tk.END))

    def update_condition(self) -> None:
        # Update self.condition_text, so that the <Leave>-check in deactivate() does not signal a design-change and
        # that save_in_file_new() already reads the new text, entered into the textbox before Control-s/g.
        # To ensure this, save_in_file_new() waits for idle.
        self.condition_text = str(self.condition_id.get("1.0", tk.END))

    def register_all_widgets_at_grid(self) -> None:
        self.condition_label.grid(row=0, column=0, sticky="we")
        self.condition_id.grid(row=1, column=0, sticky="we")
        self.action_label.grid(row=2, column=0, sticky="we")
        self.action_id.grid(row=3, column=0, sticky="we")

    def tag(self, connected_to_reset_entry: bool) -> None:
        if connected_to_reset_entry is True:
            tag = [
                "condition_action" + str(ConditionAction.conditionaction_id),
                "ca_connection" + str(ConditionAction.conditionaction_id) + "_anchor",
                "connected_to_reset_transition",
            ]
        else:
            tag = [
                "condition_action" + str(ConditionAction.conditionaction_id),
                "ca_connection" + str(ConditionAction.conditionaction_id) + "_anchor",
            ]
        main_window.canvas.itemconfigure(self.window_id, tag=tag)

    def change_descriptor_to(self, text: str) -> None:
        self.action_label.config(
            text=text
        )  # Used for switching between "asynchronous" and "synchron" (clocked) transition.

    def draw_line(self, transition_id: int, menu_x: float, menu_y: float) -> None:
        # Draw a line from the transition start point to the condition_action block which is added to the transition:
        transition_coords = main_window.canvas.coords(transition_id)
        transition_tags = main_window.canvas.gettags(transition_id)
        self.line_id = main_window.canvas.create_line(
            menu_x,
            menu_y,
            transition_coords[0],
            transition_coords[1],
            dash=(2, 2),
            state=tk.HIDDEN,
            tags=["ca_connection" + str(ConditionAction.conditionaction_id), "connected_to_" + transition_tags[0]],
        )
        main_window.canvas.addtag_withtag(
            "ca_connection" + str(ConditionAction.conditionaction_id) + "_end", transition_id
        )
        if self.line_id is not None:
            main_window.canvas.tag_lower(self.line_id, transition_id)

    def __draw_polygon_around_window(self) -> None:
        # Instead of a real rectangle, a polygon was used, because then a "leave" binding was possible,
        # when the mouse pointer enters the condition&action block.
        if self.debug_events is True:
            print("event 1: enter-window")
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
        # It is "fill="blue" used instead of "width=3, outline="blue" as then the 4 edges are sharp and not round:
        self.move_rectangle = main_window.canvas.create_polygon(
            polygon_coords, width=1.0, fill="blue", tags="polygon_for_move"
        )
        main_window.canvas.tag_bind(self.move_rectangle, "<Leave>", self.delete_polygon)
        if self.window_enter_func_id is not None:
            main_window.canvas.tag_unbind(self.window_id, "<Enter>", self.window_enter_func_id)
            self.window_enter_func_id = ""

    def delete_polygon(self, event: tk.Event) -> None:
        if self.debug_events is True:
            print("event 3: leave-polygon: delete polygon")
        assert self.move_rectangle is not None
        main_window.canvas.delete(self.move_rectangle)

    def enter_box(self) -> None:
        self.frame_id.configure(padding=3)  # increase the width of the line around the box
        if self.debug_events is True:
            print("event 2: enter-frame: extend box")
        self.action_text = str(self.action_id.get("1.0", tk.END))
        self.condition_text = str(self.condition_id.get("1.0", tk.END))
        self.register_all_widgets_at_grid()
        self.canvas_enter_func_id = str(main_window.canvas.bind("<Enter>", self.leave_box))

    def leave_box(self, event: tk.Event) -> None:
        self.frame_id.configure(padding=1)
        if self.debug_events is True:
            print("event 4: canvas-enter: shrink-box")
        if self.canvas_enter_func_id is not None:
            main_window.canvas.unbind("<Enter>", self.canvas_enter_func_id)
            self.canvas_enter_func_id = None
        self.shrink_box()
        self.window_enter_func_id = str(
            main_window.canvas.tag_bind(self.window_id, "<Enter>", lambda event: self.__draw_polygon_around_window())
        )
        assert self.move_rectangle is not None
        main_window.canvas.delete(self.move_rectangle)

    def shrink_box(self) -> None:
        self.frame_id.focus()  # "unfocus" the Text, when the mouse leaves the text.
        if (
            self.condition_id.get("1.0", tk.END) != self.condition_text
            or self.action_id.get("1.0", tk.END) != self.action_text
        ):
            undo_handling.design_has_changed()
        if self.condition_id.get("1.0", tk.END) == "\n" and self.action_id.get("1.0", tk.END) != "\n":
            self.condition_label.grid_forget()
            self.condition_id.grid_forget()
        if self.condition_id.get("1.0", tk.END) != "\n" and self.action_id.get("1.0", tk.END) == "\n":
            self.action_label.grid_forget()
            self.action_id.grid_forget()

    def move_to(self, event_x: float, event_y: float, first: bool, last: bool) -> None:
        # During moving there might be no polygon-leave-event (which deletes the polygon),
        # so for delete it hear for clean graphics.
        if self.move_rectangle is not None:
            main_window.canvas.delete(self.move_rectangle)

        if last is True:
            self.frame_id.configure(padding=1)  # decrease the width of the line around the box
        if first is True:
            self.frame_id.configure(padding=3)  # increase the width of the line around the box
            # Calculate the difference between the "anchor" point and the event:
            coords = main_window.canvas.coords(self.window_id)
            self.difference_x, self.difference_y = -event_x + coords[0], -event_y + coords[1]
        # Keep the distance between event and anchor point constant:
        event_x, event_y = event_x + self.difference_x, event_y + self.difference_y
        # if last==True:
        #     event_x = canvas_editing.state_radius * round(event_x/canvas_editing.state_radius)
        #     event_y = canvas_editing.state_radius * round(event_y/canvas_editing.state_radius)
        main_window.canvas.coords(self.window_id, event_x, event_y)
        # Move the line which connects the window to the transition:
        window_tags = main_window.canvas.gettags(self.window_id)
        for tag in window_tags:
            if tag.startswith("ca_connection"):
                line_tag = tag[:-7]
                self.line_coords = main_window.canvas.coords(line_tag)
                if self.line_coords is not None:
                    self.line_coords[0] = event_x
                    self.line_coords[1] = event_y
                if self.line_coords is not None:
                    main_window.canvas.coords(line_tag, self.line_coords)
                main_window.canvas.itemconfig(line_tag, state=tk.NORMAL)

    def hide_line(self) -> None:
        window_tags = main_window.canvas.gettags(self.window_id)
        for t in window_tags:
            if t.startswith("ca_connection"):
                line_tag = t[:-7]
                main_window.canvas.itemconfig(line_tag, state=tk.HIDDEN)
