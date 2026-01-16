import tkinter as tk

import canvas_delete
import canvas_editing
import condition_action
import constants
import move_handling_initialization
import undo_handling
import vector_handling
from project_manager import project_manager
from widgets.OptionMenu import OptionMenu


class TransitionLine:
    transition_number = 0
    transition_dict = {}

    def __init__(self, transition_coords, tags, priority, new_transition=False) -> None:
        if new_transition:
            TransitionLine.transition_number += 1
        self.difference_x = 0
        self.difference_y = 0
        # tags = ["transition"+str(transition_number), "coming_from_"+start_object_tag, "going_to_"+end_object_tag]
        transition_tag = tags[0]
        rectangle_coords = self._determine_position_of_priority_rectangle(transition_coords)

        transition_id = project_manager.canvas.create_line(
            transition_coords, arrow="last", fill="blue", smooth=True, tags=tags
        )

        canvas_id_priority_text = project_manager.canvas.create_text(
            rectangle_coords,
            text=priority,
            tag=transition_tag + "priority",
            font=project_manager.state_name_font,
        )

        project_manager.canvas.create_rectangle(
            project_manager.canvas.bbox(canvas_id_priority_text),
            tag=transition_tag + "rectangle",
            fill=constants.STATE_COLOR,
        )

        project_manager.canvas.tag_bind(
            transition_id,
            "<Enter>",
            lambda event, transition_id=transition_id: project_manager.canvas.itemconfig(transition_id, width=3),
        )
        project_manager.canvas.tag_bind(
            transition_id,
            "<Leave>",
            lambda event, transition_id=transition_id: project_manager.canvas.itemconfig(transition_id, width=1),
        )
        project_manager.canvas.tag_bind(
            transition_id,
            "<Button-3>",
            lambda event, transition_id=transition_id: self._show_menu(event, transition_id),
        )
        project_manager.canvas.tag_bind(
            canvas_id_priority_text,
            "<Double-Button-1>",
            lambda event: self.edit_priority(event, transition_tag),
        )

        project_manager.canvas.tag_raise(canvas_id_priority_text)
        TransitionLine.transition_dict[transition_id] = self

    def _determine_position_of_priority_rectangle(self, transition_coords):
        # Determine middle of the priority rectangle position by calculating a shortened transition:
        priority_middle_x, priority_middle_y, _, _ = vector_handling.shorten_vector(
            project_manager.priority_distance,
            transition_coords[0],
            transition_coords[1],
            0,
            transition_coords[2],
            transition_coords[3],
            1,
            0,
        )
        return priority_middle_x, priority_middle_y

    def _show_menu(self, event, transition_id) -> None:
        listbox = OptionMenu(
            project_manager.canvas,
            ["add condition&action", "straighten shape"],
            height=2,
            bg="lightgrey",
            width=21,
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
            transition_id=transition_id: self._evaluate_menu(event, window, listbox, menu_x, menu_y, transition_id),
        )
        listbox.bind("<Leave>", lambda event, window=window, listbox=listbox: self._close_menu(event, window, listbox))

    def _evaluate_menu(self, event, window, listbox, menu_x, menu_y, transition_id) -> None:
        design_was_changed = False
        selected_entry = listbox.get(listbox.curselection())
        if selected_entry == "add condition&action":
            transition_tags = project_manager.canvas.gettags(transition_id)
            has_condition_action = False
            connected_to_reset_entry = False
            for tag in transition_tags:
                if tag.startswith("ca_connection"):
                    has_condition_action = True
                elif tag == "coming_from_reset_entry":
                    connected_to_reset_entry = True
            if has_condition_action is False:
                condition_action_ref = condition_action.ConditionAction(
                    menu_x, menu_y, connected_to_reset_entry, height=1, width=8, padding=1, increment=True
                )
                condition_action_ref.tag(connected_to_reset_entry)
                condition_action_ref.draw_line(transition_id, menu_x, menu_y)
                condition_action_ref.condition_id.focus()  # Puts the text input cursor into the text box.
                design_was_changed = True
        elif selected_entry == "straighten shape":
            transition_tags = project_manager.canvas.gettags(transition_id)
            start_state_radius = 0
            end_state_radius = 0
            for tag in transition_tags:
                if tag.startswith("transition"):
                    transition_tag = tag
                    TransitionLine.extend_transition_to_state_middle_points(transition_tag)
                elif tag.startswith("coming_from_"):
                    start_state = tag.replace("coming_from_", "")
                    if start_state == "reset_entry":
                        start_state_radius = 0
                    else:
                        start_state_coords = project_manager.canvas.coords(start_state)
                        start_state_radius = abs(start_state_coords[2] - start_state_coords[0]) / 2
                elif tag.startswith("going_to_"):
                    end_state = tag.replace("going_to_", "")
                    end_state_coords = project_manager.canvas.coords(end_state)
                    end_state_radius = abs(end_state_coords[2] - end_state_coords[0]) / 2
            old_coords = project_manager.canvas.coords(transition_id)
            new_coords = []
            new_coords.append(old_coords[0])
            new_coords.append(old_coords[1])
            new_coords.append(old_coords[-2])
            new_coords.append(old_coords[-1])
            new_coords = vector_handling.shorten_vector(
                start_state_radius, new_coords[0], new_coords[1], end_state_radius, new_coords[2], new_coords[3], 1, 1
            )
            project_manager.canvas.coords(transition_id, new_coords)
            # Calculates the position of the priority rectangle by shortening the distance between the first point of
            # the transition and the second point of the transition.
            [priority_middle_x, priority_middle_y, _, _] = vector_handling.shorten_vector(
                project_manager.priority_distance, new_coords[0], new_coords[1], 0, new_coords[2], new_coords[3], 1, 0
            )
            [rectangle_width_half, rectangle_height_half] = self._get_rectangle_dimensions(transition_tag + "rectangle")
            project_manager.canvas.coords(
                transition_tag + "rectangle",
                priority_middle_x - rectangle_width_half,
                priority_middle_y - rectangle_height_half,
                priority_middle_x + rectangle_width_half,
                priority_middle_y + rectangle_height_half,
            )
            project_manager.canvas.coords(transition_tag + "priority", priority_middle_x, priority_middle_y)
            project_manager.canvas.tag_raise(transition_tag + "rectangle", transition_tag)
            project_manager.canvas.tag_raise(transition_tag + "priority", transition_tag + "rectangle")
            design_was_changed = True
        listbox.destroy()
        project_manager.canvas.delete(window)
        if design_was_changed:
            undo_handling.design_has_changed()  # It must be waited until the window for the menu is deleted.

    def _close_menu(self, event, window, listbox) -> None:
        listbox.destroy()
        project_manager.canvas.delete(window)

    def edit_priority(self, event, transition_tag) -> None:
        project_manager.canvas.unbind("<Button-1>")
        project_manager.canvas.unbind_all("<Delete>")
        priority_tag = transition_tag + "priority"
        old_text = project_manager.canvas.itemcget(priority_tag, "text")
        text_box = tk.Entry(project_manager.canvas, width=10, justify=tk.CENTER)
        text_box.insert(tk.END, old_text)
        text_box.select_range(0, tk.END)
        text_box.bind(
            "<Return>",
            lambda event, transition_tag=transition_tag, text_box=text_box: self._update_priority(
                transition_tag, text_box
            ),
        )
        text_box.bind(
            "<Escape>",
            lambda event, transition_tag=transition_tag, text_box=text_box, old_text=old_text: self._abort_edit_text(
                transition_tag, text_box, old_text
            ),
        )
        [event_x, event_y] = canvas_editing.translate_window_event_coordinates_in_exact_canvas_coordinates(event)
        project_manager.canvas.create_window(event_x, event_y, window=text_box, tag="entry-window")
        text_box.focus_set()

    def _update_priority(self, transition_tag, text_box) -> None:
        project_manager.canvas.delete("entry-window")
        project_manager.canvas.itemconfig(transition_tag + "priority", text=text_box.get())
        text_rectangle = project_manager.canvas.bbox(transition_tag + "priority")
        project_manager.canvas.coords(transition_tag + "rectangle", text_rectangle)
        text_box.destroy()
        project_manager.canvas.tag_raise(transition_tag + "rectangle", transition_tag)
        project_manager.canvas.tag_raise(transition_tag + "priority", transition_tag + "rectangle")
        undo_handling.design_has_changed()
        project_manager.canvas.bind("<Button-1>", move_handling_initialization.move_initialization)
        project_manager.canvas.bind_all("<Delete>", lambda event: canvas_delete.CanvasDelete(project_manager.canvas))

    def _abort_edit_text(self, transition_tag, text_box, old_text) -> None:
        project_manager.canvas.delete("entry-window")
        project_manager.canvas.itemconfig(transition_tag + "priority", text=old_text)
        text_box.destroy()
        project_manager.canvas.tag_raise(transition_tag + "rectangle", transition_tag)
        project_manager.canvas.tag_raise(transition_tag + "priority", transition_tag + "rectangle")
        project_manager.canvas.bind("<Button-1>", move_handling_initialization.move_initialization)
        project_manager.canvas.bind_all("<Delete>", lambda event: canvas_delete.CanvasDelete(project_manager.canvas))

    def move_to(self, event_x, event_y, transition_id, point, first, move_list, last) -> None:
        if project_manager.canvas.type(move_list[0][0]) == "line" and (move_list[0][1] in ("start", "end")):
            middle_of_line_is_moved = False
        else:
            middle_of_line_is_moved = True
        if middle_of_line_is_moved is True:
            if first is True:
                # Calculate the difference between the "anchor" point and the event:
                coords = project_manager.canvas.coords(transition_id)
                if point == "start":
                    point_to_move = [coords[0], coords[1]]
                elif point == "next_to_start":
                    point_to_move = [coords[2], coords[3]]
                elif point == "next_to_end":
                    point_to_move = [coords[-4], coords[-3]]
                elif point == "end":
                    point_to_move = [coords[-2], coords[-1]]
                else:
                    print("transition_handling: Fatal, unknown point =", point)
                    return
                self.difference_x, self.difference_y = -event_x + point_to_move[0], -event_y + point_to_move[1]
        else:
            self.difference_x = 0
            self.difference_y = 0
        # Keep the distance between event and anchor point constant:
        event_x, event_y = event_x + self.difference_x, event_y + self.difference_y
        if last is True:
            event_x = project_manager.state_radius * round(event_x / project_manager.state_radius)
            event_y = project_manager.state_radius * round(event_y / project_manager.state_radius)
        all_transition_tags = project_manager.canvas.gettags(transition_id)
        for single_transition_tag in all_transition_tags:
            if (
                single_transition_tag.startswith("transition")
                or single_transition_tag.startswith("connection")
                or single_transition_tag.endswith("comment_line")
            ):
                transition_tag = single_transition_tag
                project_manager.canvas.tag_lower(transition_tag)
        # Move transition:
        transition_coords = project_manager.canvas.coords(transition_tag)
        if point == "start":
            project_manager.canvas.coords(transition_tag, event_x, event_y, *transition_coords[2:])
        elif point == "next_to_start":
            project_manager.canvas.coords(
                transition_tag, *transition_coords[0:2], event_x, event_y, *transition_coords[4:]
            )
        elif point == "next_to_end":
            project_manager.canvas.coords(
                transition_tag, *transition_coords[-8:-4], event_x, event_y, *transition_coords[-2:]
            )
        elif point == "end":
            project_manager.canvas.coords(transition_tag, *transition_coords[-8:-2], event_x, event_y)
        else:
            print("transition_handling: Fatal, unknown point =", point)
        if project_manager.grid_drawer.show_grid:
            list_of_grid_line_canvas_ids = project_manager.canvas.find_withtag("grid_line")
            if list_of_grid_line_canvas_ids:
                project_manager.canvas.tag_raise(transition_tag, "grid_line")
        # Move priority rectangle:
        if transition_tag.startswith("transition"):  # There is no priority rectangle at a "connection".
            # The tag "transition_tag + '_start'" is already removed from the old start state when
            #  the transition start-point is moved. In all other cases the tag exists.
            # So try to get the coordinates of the start state (there the priority rectangle is positioned):
            start_state_coords = project_manager.canvas.coords(transition_tag + "_start")
            if point == "start":
                if (
                    start_state_coords == [] or project_manager.canvas.type(transition_tag + "_start") == "polygon"
                ):  # Transition start point is disconnected from its start state and moved alone.
                    start_state_radius = 0
                else:  #  State with connected transition is moved.
                    start_state_radius = abs(start_state_coords[2] - start_state_coords[0]) / 2
                # Calculates the position of the priority rectangle by shortening the vector from the
                # event (= first point of transition) to the second point of the transition.
                [priority_middle_x, priority_middle_y, _, _] = vector_handling.shorten_vector(
                    start_state_radius + project_manager.priority_distance,
                    event_x,
                    event_y,
                    0,
                    transition_coords[2],
                    transition_coords[3],
                    1,
                    0,
                )
            else:
                # Calculates the position of the priority rectangle by shortening the first point of the
                # transition to the second point of the transition.
                start_state_radius = abs(start_state_coords[2] - start_state_coords[0]) / 2
                # Because the transition is already extended to the start-state middle, the length of the
                # vector must be shortened additionally by the start state radius,
                # to keep the priority outside of the start-state.
                [priority_middle_x, priority_middle_y, _, _] = vector_handling.shorten_vector(
                    start_state_radius + project_manager.priority_distance,
                    transition_coords[0],
                    transition_coords[1],
                    0,
                    transition_coords[2],
                    transition_coords[3],
                    1,
                    0,
                )
            [rectangle_width_half, rectangle_height_half] = TransitionLine._get_rectangle_dimensions(
                transition_tag + "rectangle"
            )
            project_manager.canvas.coords(
                transition_tag + "rectangle",
                priority_middle_x - rectangle_width_half,
                priority_middle_y - rectangle_height_half,
                priority_middle_x + rectangle_width_half,
                priority_middle_y + rectangle_height_half,
            )
            project_manager.canvas.coords(transition_tag + "priority", priority_middle_x, priority_middle_y)
            project_manager.canvas.tag_raise(transition_tag + "rectangle", transition_tag)
            project_manager.canvas.tag_raise(transition_tag + "priority", transition_tag + "rectangle")

    @classmethod
    def extend_transition_to_state_middle_points(cls, transition_tag) -> None:
        transition_coords = project_manager.canvas.coords(transition_tag)
        end_state_coords = project_manager.canvas.coords(transition_tag + "_end")
        if transition_tag.startswith(
            "transition"
        ):  # When transition_tag starts with "connection" no start point is needed.
            start_coords = project_manager.canvas.coords(
                transition_tag + "_start"
            )  # Coords are from a circle (state) or from a connector (rectangle) or from the reset entry (polygon).
            if (
                project_manager.canvas.type(transition_tag + "_start") != "polygon"
            ):  # At the reset entry the transition start point is not modified for moving.
                transition_coords[0] = (start_coords[0] + start_coords[2]) // 2
                transition_coords[1] = (start_coords[1] + start_coords[3]) // 2
        transition_coords[-2] = (end_state_coords[0] + end_state_coords[2]) // 2
        transition_coords[-1] = (end_state_coords[1] + end_state_coords[3]) // 2
        project_manager.canvas.coords(transition_tag, *transition_coords)
        # Hide the line "under" the states:
        project_manager.canvas.tag_lower(transition_tag, transition_tag + "_start")
        project_manager.canvas.tag_lower(transition_tag, transition_tag + "_end")

    @classmethod
    def determine_priorities_of_outgoing_transitions(cls, start_state_canvas_id) -> dict:
        priority_dict = {}
        all_tags = project_manager.canvas.gettags(start_state_canvas_id)
        for tag in all_tags:
            if tag.startswith("transition") and tag.endswith("_start"):
                transition_tag = tag[:-6]
                priority_dict[transition_tag] = project_manager.canvas.itemcget(transition_tag + "priority", "text")
        return priority_dict

    @classmethod
    def shorten_to_state_border(cls, transition_tag) -> None:
        transition_coords = project_manager.canvas.coords(transition_tag)
        tag_list = project_manager.canvas.gettags(transition_tag)
        connection = False
        start_state_tag = None
        end_state_tag = None
        for tag in tag_list:
            if tag.startswith("coming_from_"):
                start_state_tag = tag[12:]
            elif tag.startswith("going_to_"):
                end_state_tag = tag[9:]
            elif tag.startswith("connected_to_"):
                connection = True
                end_state_tag = tag[13:]
        if connection is False:
            start_state_coords = project_manager.canvas.coords(start_state_tag)
            end_state_coords = project_manager.canvas.coords(end_state_tag)
            if start_state_tag == "reset_entry":
                start_state_radius = 0
            else:
                start_state_radius = (start_state_coords[2] - start_state_coords[0]) / 2
            end_state_radius = (end_state_coords[2] - end_state_coords[0]) / 2
            transition_start_coords = vector_handling.shorten_vector(
                start_state_radius,
                transition_coords[0],
                transition_coords[1],
                0,
                transition_coords[2],
                transition_coords[3],
                1,
                0,
            )
            transition_end_coords = vector_handling.shorten_vector(
                0,
                transition_coords[-4],
                transition_coords[-3],
                end_state_radius,
                transition_coords[-2],
                transition_coords[-1],
                0,
                1,
            )
            transition_coords[0] = transition_start_coords[0]
            transition_coords[1] = transition_start_coords[1]
            transition_coords[-2] = transition_end_coords[-2]
            transition_coords[-1] = transition_end_coords[-1]
            transition_coords = TransitionLine.remove_duplicate_points(transition_coords)
            project_manager.canvas.coords(transition_tag, transition_coords)
            project_manager.canvas.tag_lower(transition_tag)
            # Move priority rectangle:
            start_state_radius = abs(start_state_coords[2] - start_state_coords[0]) / 2
            [priority_middle_x, priority_middle_y, _, _] = vector_handling.shorten_vector(
                0 + project_manager.priority_distance,
                transition_coords[0],
                transition_coords[1],
                0,
                transition_coords[2],
                transition_coords[3],
                1,
                0,
            )
            [rectangle_width_half, rectangle_height_half] = TransitionLine._get_rectangle_dimensions(
                transition_tag + "rectangle"
            )
            project_manager.canvas.coords(
                transition_tag + "rectangle",
                priority_middle_x - rectangle_width_half,
                priority_middle_y - rectangle_height_half,
                priority_middle_x + rectangle_width_half,
                priority_middle_y + rectangle_height_half,
            )
            project_manager.canvas.coords(transition_tag + "priority", priority_middle_x, priority_middle_y)
            list_of_grid_line_canvas_ids = project_manager.canvas.find_withtag("grid_line")
            if list_of_grid_line_canvas_ids:
                project_manager.canvas.tag_raise(transition_tag, "grid_line")
        else:
            end_state_coords = project_manager.canvas.coords(end_state_tag)
            end_state_radius = (end_state_coords[2] - end_state_coords[0]) / 2

            transition_end_coords = vector_handling.shorten_vector(
                0,
                transition_coords[-4],
                transition_coords[-3],
                end_state_radius,
                transition_coords[-2],
                transition_coords[-1],
                0,
                1,
            )
            transition_coords[-2] = transition_end_coords[-2]
            transition_coords[-1] = transition_end_coords[-1]
            project_manager.canvas.coords(transition_tag, transition_coords)
            project_manager.canvas.tag_lower(transition_tag)

    @classmethod
    def remove_duplicate_points(cls, transition_coords) -> list:
        new_transition_coords = []
        new_transition_coords.append(transition_coords[0])
        new_transition_coords.append(transition_coords[1])
        for i in range(int(len(transition_coords) / 2) - 1):
            if (
                transition_coords[2 * i] != transition_coords[2 * i + 2]
                or transition_coords[2 * i + 1] != transition_coords[2 * i + 3]
            ):
                new_transition_coords.append(transition_coords[2 * i + 2])
                new_transition_coords.append(transition_coords[2 * i + 3])
        return new_transition_coords

    @classmethod
    def _get_rectangle_dimensions(cls, canvas_id) -> list:
        rectangle_coords = project_manager.canvas.coords(canvas_id)
        rectangle_width_half = (rectangle_coords[2] - rectangle_coords[0]) / 2
        rectangle_height_half = (rectangle_coords[3] - rectangle_coords[1]) / 2
        return [rectangle_width_half, rectangle_height_half]

    @classmethod
    def hide_priority_of_single_outgoing_transitions(cls) -> None:
        canvas_ids = project_manager.canvas.find_all()
        for canvas_id in canvas_ids:
            if project_manager.canvas.type(canvas_id) == "oval":  # found state
                tags = project_manager.canvas.gettags(canvas_id)
                outgoing_transition_tags = []
                for tag in tags:
                    if tag.startswith("transition") and tag.endswith("_start"):
                        outgoing_transition_tags.append(tag[:-6])
                if len(outgoing_transition_tags) == 1:
                    project_manager.canvas.itemconfigure(outgoing_transition_tags[0] + "priority", state=tk.HIDDEN)
                    project_manager.canvas.itemconfigure(outgoing_transition_tags[0] + "rectangle", state=tk.HIDDEN)
                else:
                    for outgoing_transition_tag in outgoing_transition_tags:
                        project_manager.canvas.itemconfigure(outgoing_transition_tag + "priority", state=tk.NORMAL)
                        project_manager.canvas.itemconfigure(outgoing_transition_tag + "rectangle", state=tk.NORMAL)
