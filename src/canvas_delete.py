"""
This class provides all methods needed to delete a Canvas item and
all its connected parts.
"""

import tkinter as tk
from tkinter import messagebox

import condition_action
import custom_text
import global_actions_clocked
import global_actions_combinatorial
import state_action
import state_actions_default
import undo_handling
from project_manager import project_manager


class CanvasDelete:
    """This class provides all methods needed to delete a Canvas item and all its connected parts."""

    canvas_x_coordinate = 0
    canvas_y_coordinate = 0

    def __init__(self, canvas):
        self.canvas = canvas
        self.design_was_changed = False
        ids = self._find_items_to_delete()
        for canvas_id in ids:
            self._delete_item(canvas_id)
        if self.design_was_changed:
            undo_handling.design_has_changed()

    def _find_items_to_delete(self):
        ids = self.canvas.find_overlapping(
            CanvasDelete.canvas_x_coordinate - 2,
            CanvasDelete.canvas_y_coordinate - 2,
            CanvasDelete.canvas_x_coordinate + 2,
            CanvasDelete.canvas_y_coordinate + 2,
        )
        return ids

    def _delete_item(self, canvas_id):
        item_type = self.canvas.type(canvas_id)
        if item_type is None:
            # This item i is a member of the list stored in ids but was already deleted,
            # when one of the items earlier in the list was deleted.
            return
        tags_of_item_i = self.canvas.gettags(canvas_id)
        if self._item_is_a_not_deletable_object(canvas_id, tags_of_item_i):
            return
        if item_type == "polygon":
            self._delete_reset_entry(tags_of_item_i)
        elif item_type == "window":
            self._delete_window(tags_of_item_i)
        elif item_type == "oval":
            self._delete_state(tags_of_item_i, canvas_id)
        elif item_type == "rectangle":
            self._delete_connector_or_transition(tags_of_item_i)
        elif item_type == "line":
            self._delete_transition_line(tags_of_item_i)
        else:
            messagebox.showerror(
                "Delete",
                "Fatal, cannot delete canvas_type "
                + str(self.canvas.type(canvas_id))
                + " with tags "
                + str(self.canvas.gettags(canvas_id)),
            )

    def _item_is_a_not_deletable_object(self, canvas_id, tags_of_item_i) -> bool:
        for single_tag in tags_of_item_i:
            if (
                single_tag == "grid_line"
                or (
                    self.canvas.type(canvas_id) == "line" and single_tag.startswith("connection")
                )  # line to state-action
                or single_tag.endswith("_comment_line")  # line to state-comment
            ):
                return True
        return False

    def _delete_reset_entry(self, tags_of_item_i):
        for tag in tags_of_item_i:  # Remove reset entry and connected transition.
            if tag.startswith("reset_entry"):
                self.canvas.delete(tag)  # delete polygon
                self.canvas.delete("reset_text")  # delete text item
                project_manager.reset_entry_button.config(state=tk.NORMAL)
                self.design_was_changed = True
            elif tag.startswith("transition") and tag.endswith("_start"):  # transition<n>_start
                transition = tag[0:-6]
                transition_tags = self.canvas.gettags(transition)
                for transition_tag in transition_tags:
                    if transition_tag.startswith("going_to_"):
                        state = transition_tag[9:]
                        self.canvas.dtag(state, transition + "_end")
                    elif transition_tag.startswith("ca_connection"):
                        condition_action_tag = transition_tag[:-4]
                        self.canvas.delete(condition_action_tag + "_anchor")
                self.canvas.delete(transition)
                self.canvas.delete(transition + "rectangle")  # delete priority rectangle
                self.canvas.delete(transition + "priority")  # delete priority
            elif tag == "polygon_for_move":
                self.canvas.delete(tag)  # delete move polygon

    def _delete_window(self, tags_of_item_i):
        # Delete the window and all tags which refer to this window:
        for tag in tags_of_item_i:
            item_id = self.canvas.find_withtag(tag)
            if tag.startswith("state_actions_default"):
                ref = state_actions_default.StateActionsDefault.dictionary[item_id[0]]
                del custom_text.CustomText.read_variables_of_all_windows[ref.text_id]
                del custom_text.CustomText.written_variables_of_all_windows[ref.text_id]
                self.canvas.delete(tag)  # delete window
                project_manager.state_action_default_button.config(state=tk.NORMAL)
            elif tag.startswith("state_action"):
                ref = state_action.StateAction.mytext_dict[item_id[0]]
                del custom_text.CustomText.read_variables_of_all_windows[ref.text_id]
                del custom_text.CustomText.written_variables_of_all_windows[ref.text_id]
                self.canvas.delete(tag)  # delete window
            elif tag.endswith("_comment"):
                self.canvas.delete(tag)  # delete window
                self.canvas.delete(tag + "_line")  # delete line to window
                self.canvas.dtag(
                    tag.replace("_comment", ""), tag + "_line_end"
                )  # delete at state: "state"<integer>"_comment_line_end"
            elif tag.startswith("condition_action"):
                ref = condition_action.ConditionAction.dictionary[item_id[0]]
                del custom_text.CustomText.read_variables_of_all_windows[ref.condition_id]
                del custom_text.CustomText.written_variables_of_all_windows[ref.condition_id]
                del custom_text.CustomText.read_variables_of_all_windows[ref.action_id]
                del custom_text.CustomText.written_variables_of_all_windows[ref.action_id]
                self.canvas.delete(tag)  # delete window
            elif tag == "global_actions1":
                ref = global_actions_clocked.GlobalActionsClocked.dictionary[item_id[0]]
                del custom_text.CustomText.read_variables_of_all_windows[ref.text_before_id]
                del custom_text.CustomText.written_variables_of_all_windows[ref.text_before_id]
                del custom_text.CustomText.read_variables_of_all_windows[ref.text_after_id]
                del custom_text.CustomText.written_variables_of_all_windows[ref.text_after_id]
                self.canvas.delete(tag)  # delete window
                project_manager.global_action_clocked_button.config(state=tk.NORMAL)
            elif tag == "global_actions_combinatorial1":
                ref = global_actions_combinatorial.GlobalActionsCombinatorial.dictionary[item_id[0]]
                del custom_text.CustomText.read_variables_of_all_windows[ref.text_id]
                del custom_text.CustomText.written_variables_of_all_windows[ref.text_id]
                self.canvas.delete(tag)  # delete window
                project_manager.global_action_combinatorial_button.config(state=tk.NORMAL)
            elif tag.startswith("connection"):  # connection<n>_start
                connection = tag[0:-6]
                connection_tags = self.canvas.gettags(connection)
                for connection_tag in connection_tags:
                    if connection_tag.startswith("connected_to_state"):
                        state = connection_tag[13:]  # delete tag "connection<n>_end" at state.
                        self.canvas.dtag(state, tag[0:-6] + "_end")
                self.canvas.delete(tag[0:-6])  # delete connection
            elif tag.startswith("ca_connection"):  # ca_connection<n>_anchor
                ca_connection = tag[0:-7]
                ca_connection_tags = self.canvas.gettags(ca_connection)
                for ca_connection_tag in ca_connection_tags:
                    if ca_connection_tag.startswith("connected_to_transition"):
                        transition = ca_connection_tag[13:]  # delete tag "ca_connection<n>_end" at state.
                        self.canvas.dtag(transition, tag[0:-7] + "_end")
                self.canvas.delete(tag[0:-7])  # delete connection
            self.design_was_changed = True

    def _delete_state(self, tags_of_item_i, canvas_id):
        for tag in tags_of_item_i:
            if tag.startswith("state") and not tag.endswith("_comment_line_end"):
                self.canvas.delete(tag)  # delete state
                self.canvas.delete(tag + "_name")  # delete state
            elif tag.startswith("connection") and tag.endswith("_end"):  # connection<n>_end
                connection = tag[0:-4]
                self.canvas.delete(connection)  # delete connection (line)
                self.canvas.delete(connection + "_start")  # delete action window
                self.canvas.dtag(canvas_id, connection + "_end")  # delete connection<n>_end tag from state
            elif tag.startswith("transition") and tag.endswith("_end"):  # transition<n>_end
                self._delete_ending_transition(tag)
            elif tag.startswith("transition") and tag.endswith("_start"):  # transition<n>_start
                self._delete_starting_transition(tag)
            elif tag.endswith("comment_line_end"):
                canvas_id_of_comment_line = tag[:-4]
                canvas_id_of_comment = tag[:-9]
                self.canvas.delete(canvas_id_of_comment_line)
                self.canvas.delete(canvas_id_of_comment)
        self.design_was_changed = True

    def _delete_connector_or_transition(self, tags_of_item_i):
        for tag in tags_of_item_i:
            if tag.startswith("connector"):
                self.canvas.delete(tag)  # delete connector
            elif tag.startswith("transition") and tag.endswith("_end"):  # transition<n>_end
                self._delete_ending_transition(tag)
            elif tag.startswith("transition") and tag.endswith("_start"):  # transition<n>_start
                self._delete_starting_transition(tag)
        self.design_was_changed = True

    def _delete_transition_line(self, tags_of_item_i):
        for tag in tags_of_item_i:
            if tag.startswith("transition"):
                self.canvas.delete(tag)  # delete transition
                self.canvas.delete(tag + "rectangle")  # delete priority rectangle
                self.canvas.delete(tag + "priority")  # delete priority
                transition = tag  # carries "transition<n>"
            elif tag.startswith("ca_connection"):  # Line to condition-action block
                condition_action_tag = tag[:-4]
                self.canvas.delete(condition_action_tag + "_anchor")
        # Now the tag of the transition is known and the tags of the start- and end-state can be adapted:
        for tag in tags_of_item_i:
            if tag.startswith("coming_from_"):
                start_state = tag[12:]
                self.canvas.dtag(start_state, transition + "_start")
            elif tag.startswith("going_to_"):
                end_state = tag[9:]
                self.canvas.dtag(end_state, transition + "_end")
        self._adapt_visibility_of_priority_rectangles_at_state(start_state)
        self.design_was_changed = True

    def _delete_ending_transition(self, tag):
        transition = tag[0:-4]
        transition_tags = self.canvas.gettags(transition)
        for transition_tag in transition_tags:
            if transition_tag.startswith("coming_from_"):
                state = transition_tag[12:]
                self.canvas.dtag(state, transition + "_start")
                self._adapt_visibility_of_priority_rectangles_at_state(state)
            elif transition_tag.startswith("ca_connection"):
                condition_action_tag = transition_tag[:-4]
                self.canvas.delete(condition_action_tag + "_anchor")  # delete the window
                self.canvas.delete(condition_action_tag)  # delete the line to the window
        self.canvas.delete(transition)
        self.canvas.delete(transition + "rectangle")  # delete priority rectangle
        self.canvas.delete(transition + "priority")  # delete priority

    def _delete_starting_transition(self, tag):
        transition = tag[0:-6]
        transition_tags = self.canvas.gettags(transition)
        for transition_tag in transition_tags:
            if transition_tag.startswith("going_to_"):
                state = transition_tag[9:]
                self.canvas.dtag(state, transition + "_end")
            elif transition_tag.startswith("ca_connection"):
                condition_action_tag = transition_tag[:-4]
                self.canvas.delete(condition_action_tag + "_anchor")
        self.canvas.delete(transition)
        self.canvas.delete(transition + "rectangle")  # delete priority rectangle
        self.canvas.delete(transition + "priority")  # delete priority

    def _adapt_visibility_of_priority_rectangles_at_state(self, start_state) -> None:
        tags_of_start_state = self.canvas.gettags(start_state)
        number_of_outgoing_transitions = 0
        tag_of_outgoing_transition = ""
        for start_state_tag in tags_of_start_state:
            if start_state_tag.startswith("transition") and start_state_tag.endswith("_start"):
                number_of_outgoing_transitions += 1
                tag_of_outgoing_transition = start_state_tag.replace("_start", "")
        if number_of_outgoing_transitions == 1:
            self.canvas.itemconfigure(tag_of_outgoing_transition + "rectangle", state=tk.HIDDEN)
            self.canvas.itemconfigure(tag_of_outgoing_transition + "priority", state=tk.HIDDEN)

    @classmethod
    def store_mouse_position(cls, event) -> None:
        cls.canvas_x_coordinate = project_manager.canvas.canvasx(event.x)
        cls.canvas_y_coordinate = project_manager.canvas.canvasy(event.y)
