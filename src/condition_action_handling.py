"""
This class handles the condition&action box which can be activated for each transition.

"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

import canvas_editing
import custom_text
import move_handling_canvas_window
import undo_handling


class ConditionAction:
    """This class handles the condition&action box which can be activated for each transition."""

    conditionaction_id: int = 0
    dictionary: dict[int, "ConditionAction"] = {}

    def __init__(
        self,
        canvas: tk.Canvas,
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
        self.difference_x = 0.0
        self.difference_y = 0.0
        self.line_id: Optional[int] = None
        self.line_coords: Optional[list[float]] = None
        self.action_text: Optional[str] = None
        self.condition_text: Optional[str] = None
        self.frame_enter_func_id: Optional[str] = None
        self.canvas_enter_func_id: Optional[str] = None
        # Create frame:
        self.canvas = canvas
        self.frame_id = ttk.Frame(self.canvas, relief=tk.FLAT, borderwidth=0, padding=padding, style="Window.TFrame")
        # The method deactivate_frame() can not be bound to the Frame-leave-Event, because otherwise at moving the
        # cursor exactly at the frame would cause a flickering because of toggling between shrinked and full box.
        # Instead the method deactivate_frame() is bound dynamically to the Canvas-Enter event in activate_frame():
        self.frame_enter_func_id = self.frame_id.bind("<Enter>", lambda event: self.activate_frame())
        self.canvas_enter_func_id = None

        # Create objects inside frame:
        if connected_to_reset_entry:
            label_action_text = "Transition actions (asynchronous):"
        else:
            label_action_text = "Transition actions (clocked):"
        self.condition_label = ttk.Label(
            self.frame_id,
            text="Transition condition: ",
            font=("Arial", int(canvas_editing.label_fontsize)),
            style="Window.TLabel",
        )
        self.condition_label.bind("<Enter>", lambda event: self.activate_window())
        self.condition_label.bind("<Leave>", lambda event: self.deactivate_window())
        self.action_label = ttk.Label(
            self.frame_id,
            text=label_action_text,
            font=("Arial", int(canvas_editing.label_fontsize)),
            style="Window.TLabel",
        )
        self.action_label.bind("<Enter>", lambda event: self.activate_window())
        self.action_label.bind("<Leave>", lambda event: self.deactivate_window())
        self.action_id = custom_text.ActionCustomText(
            self.frame_id,
            text_type="action",
            takefocus=0,
            height=height,
            width=width,
            undo=True,
            maxundo=-1,
            font=("Courier", int(canvas_editing.fontsize)),
        )
        self.condition_id = custom_text.ConditionCustomText(
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
        self.action_id.bind("<Control-e>", lambda event: self._edit_action_in_external_editor())
        self.condition_id.bind("<Control-z>", lambda event: self.condition_id.undo())
        self.condition_id.bind("<Control-Z>", lambda event: self.condition_id.redo())
        self.condition_id.bind("<Control-e>", lambda event: self._edit_condition_in_external_editor())
        self.action_id.bind("<Control-s>", lambda event: self.update_action())
        self.action_id.bind("<Control-g>", lambda event: self.update_action())
        self.condition_id.bind("<Control-s>", lambda event: self.update_condition())
        self.condition_id.bind("<Control-g>", lambda event: self.update_condition())
        self.action_id.bind("<<TextModified>>", lambda event: undo_handling.update_window_title())
        self.condition_id.bind("<<TextModified>>", lambda event: undo_handling.update_window_title())
        self.action_id.bind("<FocusIn>", lambda event: self.canvas.unbind_all("<Delete>"))
        self.action_id.bind(
            "<FocusOut>", lambda event: self.canvas.bind_all("<Delete>", lambda event: canvas_editing.delete())
        )
        self.condition_id.bind("<FocusIn>", lambda event: self.canvas.unbind_all("<Delete>"))
        self.condition_id.bind(
            "<FocusOut>", lambda event: self.canvas.bind_all("<Delete>", lambda event: canvas_editing.delete())
        )
        # Define layout:
        self.show_complete_box()

        # Create canvas window for the frame:
        self.window_id = self.canvas.create_window(menu_x, menu_y, window=self.frame_id, anchor=tk.W)

        self.frame_id.bind(
            "<Button-1>",
            lambda event: move_handling_canvas_window.MoveHandlingCanvasWindow(event, self.frame_id, self.window_id),
        )
        self.condition_label.bind(
            "<Button-1>",
            lambda event: move_handling_canvas_window.MoveHandlingCanvasWindow(
                event, self.condition_label, self.window_id
            ),
        )
        self.action_label.bind(
            "<Button-1>",
            lambda event: move_handling_canvas_window.MoveHandlingCanvasWindow(
                event, self.action_label, self.window_id
            ),
        )

        # Create dictionary for translating the canvas-id of the canvas-window into a reference to this object:
        ConditionAction.dictionary[self.window_id] = self

    def _edit_action_in_external_editor(self) -> None:
        self.action_id.edit_in_external_editor()
        self.update_action()

    def _edit_condition_in_external_editor(self) -> None:
        self.condition_id.edit_in_external_editor()
        self.update_condition()

    def update_action(self) -> None:
        # Update self.action_text, so that the <Leave>-check in deactivate() does not signal a design-change and
        # that save_in_file_new() already reads the new text, entered into the textbox before Control-s/g.
        # To ensure this, save_in_file_new() waits for idle.
        self.action_text = self.action_id.get("1.0", tk.END)

    def update_condition(self) -> None:
        # Update self.condition_text, so that the <Leave>-check in deactivate() does not signal a design-change and
        # that save_in_file_new() already reads the new text, entered into the textbox before Control-s/g.
        # To ensure this, save_in_file_new() waits for idle.
        self.condition_text = self.condition_id.get("1.0", tk.END)

    def show_complete_box(self) -> None:
        self.condition_label.grid(row=0, column=0, sticky="we")
        self.condition_id.grid(row=1, column=0, sticky="we")
        self.action_label.grid(row=2, column=0, sticky="we")
        self.action_id.grid(row=3, column=0, sticky="we")

    def tag(self, connected_to_reset_entry: bool) -> None:
        if connected_to_reset_entry is True:
            tag = [
                f"condition_action{ConditionAction.conditionaction_id}",
                f"ca_connection{ConditionAction.conditionaction_id}_anchor",
                "connected_to_reset_transition",
            ]
        else:
            tag = [
                f"condition_action{ConditionAction.conditionaction_id}",
                f"ca_connection{ConditionAction.conditionaction_id}_anchor",
            ]
        self.canvas.itemconfigure(self.window_id, tags=tag)

    def change_descriptor_to(self, text: str) -> None:
        self.action_label.config(
            text=text
        )  # Used for switching between "asynchronous" and "synchron" (clocked) transition.

    def draw_line(self, transition_id: int, menu_x: float, menu_y: float) -> None:
        # Draw a line from the transition start point to the condition_action block which is added to the transition:
        transition_coords = self.canvas.coords(transition_id)
        transition_tags = self.canvas.gettags(transition_id)
        self.line_id = self.canvas.create_line(
            menu_x,
            menu_y,
            transition_coords[0],
            transition_coords[1],
            dash=(2, 2),
            state=tk.HIDDEN,
            tags=[f"ca_connection{ConditionAction.conditionaction_id}", f"connected_to_{transition_tags[0]}"],
        )
        self.canvas.addtag_withtag(f"ca_connection{ConditionAction.conditionaction_id}_end", transition_id)
        self.canvas.tag_lower(self.line_id, transition_id)

    def activate_frame(self) -> None:
        self.activate_window()
        self.show_complete_box()
        self.action_text = self.action_id.get("1.0", tk.END)
        self.condition_text = self.condition_id.get("1.0", tk.END)
        if self.frame_enter_func_id is not None:
            self.canvas.unbind(self.frame_enter_func_id)
            self.frame_enter_func_id = None
        self.canvas_enter_func_id = self.canvas.bind("<Enter>", lambda event: self.deactivate_frame())

    def activate_window(self) -> None:
        self.frame_id.configure(borderwidth=1, style="WindowSelected.TFrame")
        self.condition_label.configure(style="WindowSelected.TLabel")
        self.action_label.configure(style="WindowSelected.TLabel")

    def deactivate_frame(self) -> None:
        self.deactivate_window()
        if self.canvas_enter_func_id is not None:
            self.canvas.unbind("<Enter>", self.canvas_enter_func_id)
            self.canvas_enter_func_id = None
        self.frame_enter_func_id = self.frame_id.bind("<Enter>", lambda event: self.activate_frame())
        self.shrink_box()

    def deactivate_window(self) -> None:
        self.frame_id.configure(borderwidth=0, style="Window.TFrame")
        self.condition_label.configure(style="Window.TLabel")
        self.action_label.configure(style="Window.TLabel")

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

    def move_to(self, event_x: float, event_y: float, first: bool) -> None:
        if first is True:
            # Calculate the difference between the "anchor" point and the event:
            coords = self.canvas.coords(self.window_id)
            self.difference_x, self.difference_y = -event_x + coords[0], -event_y + coords[1]
        # Keep the distance between event and anchor point constant:
        event_x, event_y = event_x + self.difference_x, event_y + self.difference_y
        self.canvas.coords(self.window_id, event_x, event_y)
        # Move the line which connects the window to the transition:
        window_tags = self.canvas.gettags(self.window_id)
        for tag in window_tags:
            if tag.startswith("ca_connection"):
                line_tag = tag[:-7]
                self.line_coords = self.canvas.coords(line_tag)
                self.line_coords[0] = event_x
                self.line_coords[1] = event_y
                self.canvas.coords(line_tag, self.line_coords)
                self.canvas.itemconfig(line_tag, state=tk.NORMAL)

    def hide_line(self) -> None:
        window_tags = self.canvas.gettags(self.window_id)
        for t in window_tags:
            if t.startswith("ca_connection"):
                line_tag = t[:-7]
                self.canvas.itemconfig(line_tag, state=tk.HIDDEN)
