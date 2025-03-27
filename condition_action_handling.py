"""
    This class handles the condition&action box which can be activated for each transition.
"""
import tkinter as tk
from tkinter import ttk

import canvas_editing
import undo_handling
import custom_text
import main_window

class ConditionAction():
    conditionaction_id = 0
    dictionary = {}
    def __init__(self, menu_x, menu_y, connected_to_reset_entry, height, width, padding, increment):
        if increment is True:
            ConditionAction.conditionaction_id += 1
        self.difference_x              = 0
        self.difference_y              = 0
        self.line_id                   = None
        self.line_coords               = None
        self.move_rectangle            = None
        self.last_action_was_shrinking = False
        self.action                    = False
        self.condition                 = False
        self.move_rectangle            = None
        # Create frame:
        self.frame_id = ttk.Frame(main_window.canvas, relief=tk.FLAT, padding=padding, style='Window.TFrame')
        self.frame_id.bind("<Enter>", lambda event : self.extend_box())
        self.frame_id.bind("<Leave>", lambda event : self.shrink_box())
        # Create objects inside frame:
        if connected_to_reset_entry:
            label_action_text = "Transition actions (asynchronous):"
        else:
            label_action_text = "Transition actions (clocked):"
        self.condition_label = ttk.Label             (self.frame_id, text="Transition condition: ", font=("Arial",int(canvas_editing.label_fontsize)))
        self.action_label    = ttk.Label             (self.frame_id, text=label_action_text       , font=("Arial",int(canvas_editing.label_fontsize)))
        self.action_id       = custom_text.CustomText(self.frame_id, text_type="action"   , takefocus=0, height=height, width=width, undo=True, maxundo=-1,
                                                      font=("Courier",int(canvas_editing.fontsize)))
        self.condition_id    = custom_text.CustomText(self.frame_id, text_type="condition", takefocus=0, height=height, width=width, undo=True, maxundo=-1,
                                                      font=("Courier",int(canvas_editing.fontsize)))
        # Create bindings for Undo/Redo:
        self.action_id      .bind("<Control-z>"     , lambda event : self.action_id.undo())
        self.action_id      .bind("<Control-Z>"     , lambda event : self.action_id.redo())
        self.condition_id   .bind("<Control-z>"     , lambda event : self.condition_id.undo())
        self.condition_id   .bind("<Control-Z>"     , lambda event : self.condition_id.redo())
        self.action_id      .bind("<<TextModified>>", lambda event : undo_handling.modify_window_title())
        self.condition_id   .bind("<<TextModified>>", lambda event : undo_handling.modify_window_title())
        self.action_id      .bind("<FocusIn>"       , lambda event : main_window.canvas.unbind_all("<Delete>"))
        self.action_id      .bind("<FocusOut>"      , lambda event : main_window.canvas.bind_all  ('<Delete>', lambda event: canvas_editing.delete()))
        self.condition_id   .bind("<FocusIn>"       , lambda event : main_window.canvas.unbind_all("<Delete>"))
        self.condition_id   .bind("<FocusOut>"      , lambda event : main_window.canvas.bind_all  ('<Delete>', lambda event: canvas_editing.delete()))
        # Define layout:
        self.register_all_widgets_at_grid()
        # Create canvas window for the frame:
        self.window_id = main_window.canvas.create_window(menu_x, menu_y, window=self.frame_id, anchor=tk.W)
        # Moving a condition&action block had the problem, that the block could only be picked up at
        # a small distance away from its borders which is difficult for the user to handle.
        # To improve the moving a method (move_item) was built, which allowed picking up also inside the block.
        # But with this solution selecting text by the mousepointer could not be used anymore.
        # And this solution showed very bad moving behaviour under Linux Mint.
        # So a new solution was implemented which draws a rectangle around the block to move which
        # signals the user, that picking the block for moving is now possible.
        # Instead of a real rectangle, a polygon was used, because then a "leave" binding was possible,
        # when the mouse pointer enters the condition&action block:
        main_window.canvas.tag_bind(self.window_id, "<Enter>", lambda event : self.__draw_polygon_around_window())
        # Create dictionary for translating the canvas-id of the canvas-window into a reference to this object:
        ConditionAction.dictionary[self.window_id] = self

    def register_all_widgets_at_grid(self):
        self.condition_label.grid (row=0, column=0, sticky=(tk.W,tk.E))
        self.condition_id.grid    (row=1, column=0, sticky=(tk.W,tk.E))
        self.action_label.grid    (row=2, column=0, sticky=(tk.W,tk.E))
        self.action_id.grid       (row=3, column=0, sticky=(tk.W,tk.E))

    def tag(self, connected_to_reset_entry):
        if connected_to_reset_entry is True:
            tag=('condition_action'+str(ConditionAction.conditionaction_id), "ca_connection"+str(ConditionAction.conditionaction_id) + "_anchor", "connected_to_reset_transition")
        else:
            tag=('condition_action'+str(ConditionAction.conditionaction_id), "ca_connection"+str(ConditionAction.conditionaction_id) + "_anchor")
        main_window.canvas.itemconfigure(self.window_id, tag=tag)

    def change_descriptor_to(self, text):
        self.action_label.config(text=text) # Used for switching between "asynchronous" and "synchron" (clocked) transition.

    def draw_line(self, transition_id, menu_x, menu_y):
        # Draw a line from the transition start point to the condition_action block which is added to the transition:
        transition_coords = main_window.canvas.coords (transition_id)
        transition_tags   = main_window.canvas.gettags(transition_id)
        self.line_id = main_window.canvas.create_line(menu_x, menu_y, transition_coords[0], transition_coords[1], dash=(2,2), state=tk.HIDDEN,
                       tag=('ca_connection'+str(ConditionAction.conditionaction_id),'connected_to_' + transition_tags[0]))
        main_window.canvas.addtag_withtag("ca_connection"+str(ConditionAction.conditionaction_id)+"_end", transition_id)
        main_window.canvas.tag_lower(self.line_id,transition_id)

    def __draw_polygon_around_window(self):
        # When the window is entered from "outside" and is extended,
        # then no window-leaving-event is detected and the polygon is removed by extend_box().
        # When the window is entered from "inside" of an extended box (after a editing action),
        # then the window will be shrinked, if it still has no condition.
        # As in this case the move_polygon is sometimes (depending on the mouse speed) also
        # drawn (unnecessarily), this shall not happen before the window has been shrinked,
        # otherwise the polygon would have wrong dimensions:
        if not self.last_action_was_shrinking:
            main_window.canvas.after_idle(self.__draw_polygon_around_window_delayed)
    def __draw_polygon_around_window_delayed(self):
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
        self.move_rectangle = main_window.canvas.create_polygon(polygon_coords, width=1, fill="blue", tag="polygon_for_move")
        main_window.canvas.tag_bind(self.move_rectangle, "<Leave>", lambda event: main_window.canvas.delete(self.move_rectangle))

    def extend_box(self):
        # When a small box is extendend the self-destroying mechanism of the move_rectangle does not work,
        # as the extended box is bigger than the move_polygon and no polygon-leave-event happens.
        # So in this case the polygon must be removed explicetly:
        main_window.canvas.delete(self.move_rectangle)
        self.action    = self.action_id.get   ("1.0", tk.END)
        self.condition = self.condition_id.get("1.0", tk.END)
        self.register_all_widgets_at_grid()

    def shrink_box(self):
        self.frame_id.focus() # "unfocus" the Text, when the mouse leaves the text.
        if (self.condition_id.get("1.0", tk.END)!= self.condition or
            self.action_id.get   ("1.0", tk.END)!= self.action):
            undo_handling.design_has_changed()
        # When at leaving the box, the box is not shrinked, the mouse-pointer "passes" the canvas-window and the move_polygon is drawn/removed again.
        # But when the box is shrinked the situation is complicated, as several things happen at about the same time:
        # Because the box is shrinked, the canvas-window is shrinked.
        # The mouse-pointer, which was first in the box, is now outside of it without any mouse-pointer moving.
        # Although, depending on the speed of the mouse-pointer, the canvas-window sometimes recognizes an enter-event.
        # Then a move-polygon is drawn around the shrinked box.
        # This move-polygon sometimes is not removed, if no window-leaving-event is triggered anymore.
        # To avoid this case, the flag last_action_was_shrinking is used.
        # It is raised, when the box is shrinked, so that at a possible canvas-window-enter-event no move-polygon is drawn.
        # But to clear this flag is difficult, as when the mouse-pointer is outside of the shrinked box, no event regarding the box is triggered anymore.
        # So it is automatically cleared after a short time.
        self.last_action_was_shrinking = False
        if self.condition_id.get("1.0", tk.END)=="\n" and self.action_id.get("1.0", tk.END)!="\n":
            self.condition_label.grid_forget()
            self.condition_id.grid_forget()
            self.last_action_was_shrinking = True
            main_window.canvas.after(500, self.__clear_last_action_was_shrinking)
        if self.condition_id.get("1.0", tk.END)!="\n" and self.action_id.get("1.0", tk.END)=="\n":
            self.action_label.grid_forget()
            self.action_id.grid_forget()
            self.last_action_was_shrinking = True
            main_window.canvas.after(500, self.__clear_last_action_was_shrinking)

    def __clear_last_action_was_shrinking(self):
        self.last_action_was_shrinking = False

    def move_to(self, event_x, event_y, first, last):
        main_window.canvas.delete(self.move_rectangle) # During moving there might be no move-polygon-leave-event, so for delete it hear for clean graphics.
        self.frame_id.configure(padding=1) # decrease the width of the line around the box
        if first is True:
            self.frame_id.configure(padding=4) # increase the width of the line around the box
            # Calculate the difference between the "anchor" point and the event:
            coords = main_window.canvas.coords(self.window_id)
            self.difference_x, self.difference_y = - event_x + coords[0], - event_y + coords[1]
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
                self.line_coords[0] = event_x
                self.line_coords[1] = event_y
                main_window.canvas.coords(line_tag, self.line_coords)
                main_window.canvas.itemconfig(line_tag, state=tk.NORMAL)

    def hide_line(self):
        window_tags = main_window.canvas.gettags(self.window_id)
        for t in window_tags:
            if t.startswith("ca_connection"):
                line_tag = t[:-7]
                main_window.canvas.itemconfig(line_tag, state=tk.HIDDEN)
