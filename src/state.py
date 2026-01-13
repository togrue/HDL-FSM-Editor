import tkinter as tk
from tkinter import messagebox

import canvas_delete
import canvas_editing
import constants
import move_handling_canvas_item
import move_handling_initialization
import state_action
import state_comment
import transition_handling
import undo_handling
from dialogs.color_changer import ColorChanger
from project_manager import project_manager
from widgets.OptionMenu import OptionMenu


class States:
    state_number = 0
    state_dict = {}

    def __init__(self, coords, tags, text, fill_color) -> None:
        self.difference_x = 0
        self.difference_y = 0
        States.state_number += 1
        self.state_id = project_manager.canvas.create_oval(
            coords,
            fill=fill_color,
            width=2,
            outline="blue",
            tags=tags,
        )
        project_manager.canvas.tag_bind(
            self.state_id, "<Enter>", lambda event, id=self.state_id: project_manager.canvas.itemconfig(id, width=4)
        )
        project_manager.canvas.tag_bind(
            self.state_id, "<Leave>", lambda event, id=self.state_id: project_manager.canvas.itemconfig(id, width=2)
        )
        project_manager.canvas.tag_bind(
            self.state_id, "<Button-3>", lambda event, id=self.state_id: self._show_menu(event, id)
        )
        project_manager.canvas.tag_bind(
            self.state_id,
            "<Button-1>",
            lambda event: move_handling_canvas_item.MoveHandlingCanvasItem(event, self.state_id),
        )
        middle = self._calculate_center(coords)
        for t in tags:
            if t.startswith("state") and not t.endswith("_comment_line_end"):
                state_name = t
                text_id = project_manager.canvas.create_text(
                    middle[0],
                    middle[1],
                    text=text,
                    tags=state_name + "_name",
                    font=project_manager.state_name_font,
                )
                project_manager.canvas.tag_bind(
                    text_id,
                    "<Button-1>",
                    lambda event, text_id=text_id: move_handling_canvas_item.MoveHandlingCanvasItem(event, text_id),
                )
                project_manager.canvas.tag_bind(
                    text_id, "<Double-Button-1>", lambda event, text_id=text_id: self._edit_state_name(event, text_id)
                )
                project_manager.canvas.tag_bind(
                    text_id, "<Button-3>", lambda event, text_id=text_id: self._show_menu_from_text(event, text_id)
                )
        # undo_handling.design_has_changed()
        States.state_dict[self.state_id] = self

    def _show_menu(self, event, state_id) -> None:
        listbox = OptionMenu(
            project_manager.canvas,
            ["add action", "add comment", "change color"],
            height=3,
            bg="lightgrey",
            width=14,
            activestyle="dotbox",
            relief=tk.RAISED,
        )
        [event_x, event_y] = canvas_editing.translate_window_event_coordinates_in_exact_canvas_coordinates(event)
        window = project_manager.canvas.create_window(event_x + 40, event_y, window=listbox)
        listbox.bind(
            "<Button-1>",
            lambda event,
            window=window,
            listbox=listbox,
            menu_x=event_x,
            menu_y=event_y,
            state_id=state_id: self._evaluate_menu(event, window, listbox, menu_x, menu_y, state_id),
        )
        listbox.bind("<Leave>", lambda event, window=window, listbox=listbox: self._close_menu(window, listbox))

    def _edit_state_name(self, event, text_id) -> None:
        project_manager.canvas.unbind("<Button-1>")
        project_manager.canvas.unbind_all("<Delete>")
        old_text = project_manager.canvas.itemcget(text_id, "text")
        text_box = tk.Entry(project_manager.canvas, width=10, justify=tk.CENTER)
        # text_box = Entry(None, width=10, justify=tk.CENTER) funktioniert auch, unklar, was richtig/besser ist.
        text_box.insert(tk.END, old_text)
        text_box.select_range(0, tk.END)
        text_box.bind(
            "<Return>", lambda event, text_id=text_id, text_box=text_box: self._update_state_name(text_id, text_box)
        )
        text_box.bind(
            "<Escape>",
            lambda event, text_id=text_id, text_box=text_box, old_text=old_text: self._abort_edit_text(
                text_id, text_box, old_text
            ),
        )
        event_x, event_y = canvas_editing.translate_window_event_coordinates_in_rounded_canvas_coordinates(event)
        project_manager.canvas.create_window(event_x, event_y, window=text_box, tag="entry-window")
        text_box.focus_set()

    def _show_menu_from_text(self, event, text_id):
        for tag in project_manager.canvas.gettags(text_id):
            if tag.endswith("_name"):
                state_tag = tag[:-5]
                self._show_menu(event, state_tag)

    def _close_menu(self, window, listbox) -> None:
        listbox.destroy()
        project_manager.canvas.delete(window)

    def _update_state_name(self, text_id, text_box) -> None:
        project_manager.canvas.delete("entry-window")
        new_text = text_box.get()
        text_box.destroy()
        tags = project_manager.canvas.gettags(text_id)
        for t in tags:
            if t.startswith("state"):  # Format of text_id tag: 'state' + str(state_number) + "_name"
                state_tag = t[:-5]
                self._show_new_state_name(new_text, text_id)
                self._resize_state(state_tag, text_id)
        undo_handling.design_has_changed()
        project_manager.canvas.bind("<Button-1>", move_handling_initialization.move_initialization)
        project_manager.canvas.bind_all("<Delete>", lambda event: canvas_delete.CanvasDelete(project_manager.canvas))
        tags = project_manager.canvas.gettags(state_tag)
        for t in tags:
            if t.endswith("_start"):
                transition_handling.extend_transition_to_state_middle_points(t[:-6])
                transition_handling.shorten_to_state_border(t[:-6])
            elif t.endswith("_end") and not t.endswith("_comment_line_end"):
                transition_handling.extend_transition_to_state_middle_points(t[:-4])
                transition_handling.shorten_to_state_border(t[:-4])

    def _evaluate_menu(self, event, window, listbox, menu_x, menu_y, state_id) -> None:
        selected_entry = listbox.get(listbox.curselection())
        listbox.destroy()
        project_manager.canvas.delete(window)
        if selected_entry == "add action":
            tags = project_manager.canvas.gettags(state_id)
            action_block_exists = False
            for tag in tags:
                if tag.startswith("connection"):
                    action_block_exists = True
            if not action_block_exists:
                action_ref = state_action.StateAction(menu_x, menu_y, height=1, width=8, padding=1, increment=True)
                action_ref.connect_to_state(menu_x, menu_y, state_id)
                action_ref.tag()
                undo_handling.design_has_changed()
        elif selected_entry == "add comment":
            tags = project_manager.canvas.gettags(state_id)
            for tag in tags:
                if tag.endswith("comment_line_end"):
                    return  # There is already a comment attached to this state.
            for tag in tags:
                if tag.startswith("state"):
                    state_identifier = tag
                    comment_ref = state_comment.StateComment(menu_x, menu_y, height=1, width=8, padding=1)
                    comment_ref.add_line(menu_x, menu_y, state_identifier)
                    comment_ref.tag(state_identifier)
                    undo_handling.design_has_changed()
        elif selected_entry == "change color":
            new_color = ColorChanger(constants.STATE_COLOR).ask_color()
            project_manager.canvas.itemconfigure(state_id, fill=new_color)
            undo_handling.design_has_changed()

    def move_to(self, event_x, event_y, state_id, first, last) -> None:
        if first is True:
            # Calculate the difference between the "anchor" point and the event:
            coords = project_manager.canvas.coords(state_id)
            center = self._calculate_center(coords)
            self.difference_x, self.difference_y = -event_x + center[0], -event_y + center[1]
        # When moving the center, keep the distance between event and anchor point constant:
        new_center_x, new_center_y = event_x + self.difference_x, event_y + self.difference_y
        if last is True:
            new_center_x, new_center_y = self._move_center_to_grid(new_center_x, new_center_y)
        text_tag = self._determine_the_tag_of_the_state_name(state_id)
        state_radius = self._determine_the_radius_of_the_state(state_id)
        project_manager.canvas.coords(
            state_id,
            new_center_x - state_radius,
            new_center_y - state_radius,
            new_center_x + state_radius,
            new_center_y + state_radius,
        )
        project_manager.canvas.coords(text_tag, new_center_x, new_center_y)
        project_manager.canvas.tag_raise(state_id, "all")
        project_manager.canvas.tag_raise(text_tag, state_id)

    def _calculate_center(self, coords) -> list:
        middle_x = (coords[0] + coords[2]) / 2
        middle_y = (coords[1] + coords[3]) / 2
        return [middle_x, middle_y]

    def _move_center_to_grid(self, new_center_x, new_center_y):
        new_center_x = project_manager.state_radius * round(new_center_x / project_manager.state_radius)
        new_center_y = project_manager.state_radius * round(new_center_y / project_manager.state_radius)
        return new_center_x, new_center_y

    def _determine_the_tag_of_the_state_name(self, state_id):
        state_tag = ""
        tags = project_manager.canvas.gettags(state_id)
        for tag in tags:
            if tag.startswith("state") and not tag.endswith("_comment_line_end"):
                state_tag = tag
        return state_tag + "_name"

    def _determine_the_radius_of_the_state(self, state_id):
        state_coords = project_manager.canvas.coords(state_id)
        return (state_coords[2] - state_coords[0]) / 2

    def draw_state_name(self, event_x, event_y, text, tags):
        text_id = project_manager.canvas.create_text(
            event_x,
            event_y,
            text=text,
            tags=tags,
            font=project_manager.state_name_font,
        )
        project_manager.canvas.tag_bind(
            text_id,
            "<Button-1>",
            lambda event: move_handling_canvas_item.MoveHandlingCanvasItem(event, text_id),
        )
        project_manager.canvas.tag_bind(
            text_id, "<Double-Button-1>", lambda event, text_id=text_id: edit_state_name(event, text_id)
        )
        project_manager.canvas.tag_bind(text_id, "<Button-3>", lambda event: _show_menu_from_text(event, text_id))

    @classmethod
    def _abort_edit_text(self, text_id, text_box, old_text) -> None:
        project_manager.canvas.delete("entry-window")
        project_manager.canvas.itemconfig(text_id, text=old_text)
        text_box.destroy()
        project_manager.canvas.bind("<Button-1>", move_handling_initialization.move_initialization)
        project_manager.canvas.bind_all("<Delete>", lambda event: canvas_delete.CanvasDelete(project_manager.canvas))

    @classmethod
    def _show_new_state_name(self, new_text, text_id) -> None:
        state_name_list = self.__get_list_of_state_names(text_id)
        if new_text != "":
            if new_text not in state_name_list:
                project_manager.canvas.itemconfig(text_id, text=new_text)
            else:
                messagebox.showerror("Error", "The state name\n" + new_text + "\nis already used at another state.")

    @classmethod
    def __get_list_of_state_names(text_id) -> list:
        state_name_list = []
        all_canvas_ids = project_manager.canvas.find_withtag("all")
        for canvas_id in all_canvas_ids:
            if project_manager.canvas.type(canvas_id) == "oval":
                state_tags = project_manager.canvas.gettags(canvas_id)
                for tag in state_tags:
                    if (
                        tag.startswith("state")
                        and not tag.endswith("_comment_line_end")
                        and project_manager.canvas.find_withtag(tag + "_name")[0] != text_id
                    ):
                        state_name_list.append(project_manager.canvas.itemcget(tag + "_name", "text"))
        return state_name_list

    @classmethod
    def _resize_state(self, state_tag, text_id) -> None:
        state_coords = project_manager.canvas.coords(state_tag)
        state_width = state_coords[2] - state_coords[0]
        size = project_manager.canvas.bbox(text_id)
        text_width = (
            size[2] - size[0] + 15
        )  # Make the text a little bit bigger, so that it does not touch the state circle.
        if text_width < 2 * project_manager.state_radius:
            text_width = 2 * project_manager.state_radius
        difference = text_width - state_width
        state_coords[0] = state_coords[0] - difference // 2
        state_coords[1] = state_coords[1] - difference // 2
        state_coords[2] = state_coords[2] + difference // 2
        state_coords[3] = state_coords[3] + difference // 2
        overlapping_list = project_manager.canvas.find_overlapping(*state_coords)
        state_is_too_big = False
        for canvas_item in overlapping_list:
            if (
                project_manager.canvas.type(canvas_item) not in ["text", "line", "rectangle"]
                and canvas_item != project_manager.canvas.find_withtag(state_tag)[0]
            ):
                state_is_too_big = True
        if not state_is_too_big:
            project_manager.canvas.coords(state_tag, state_coords)
