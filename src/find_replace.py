"""
This class implements the "find" and "replace" feature.
"""

import re
import tkinter as tk
from tkinter import messagebox

import canvas_editing
import condition_action_handling
import global_actions
import global_actions_combinatorial
import main_window
import state_action_handling
import state_actions_default
import state_comment
import undo_handling
from constants import GuiTab


class FindReplace:
    """
    The method _search_in_canvas_text() uses <string>.find() and re.findall() and re.sub().
    All other search-methods use text_widget.search() for find and replace.
    In order to have identical behaviour in _search_in_canvas_text(),
    there the search_string/replace_string are "escaped".
    """

    def __init__(self, search_string, replace_string, replace) -> None:
        search_pattern = search_string.get()
        if search_pattern == "":
            messagebox.showinfo("HDL-FSM-Editor", "The search is aborted because you searched for an empty string.")
            return
        replace_pattern = replace_string.get()
        number_of_hits_all = 0
        continue_search, number_of_hits_all = self._search_in_diagram(
            search_pattern, replace_pattern, replace, number_of_hits_all
        )
        if continue_search:
            continue_search, number_of_hits_all = self._search_in_all_text_fields(
                search_pattern, replace_pattern, replace, number_of_hits_all
            )
            if continue_search:
                if replace:
                    undo_handling.design_has_changed()
                    messagebox.showinfo("HDL-FSM-Editor", "Number of replacements = " + str(number_of_hits_all))
                else:
                    messagebox.showinfo("HDL-FSM-Editor", "Number of hits = " + str(number_of_hits_all))

    def _search_in_diagram(self, search_pattern, replace_pattern, replace, number_of_hits_all) -> tuple[bool, int]:
        all_canvas_items = main_window.canvas.find_all()
        continue_search = True
        for item in all_canvas_items:
            if main_window.canvas.type(item) == "window":
                text_ids = self._get_text_ids_of_canvas_window(item)
                continue_search, number_of_hits = self._search_in_all_text_fields_of_canvas_window(
                    search_pattern, item, text_ids, replace, replace_pattern
                )
                number_of_hits_all += number_of_hits
            elif main_window.canvas.type(item) == "text":
                continue_search, number_of_hits = self._search_in_canvas_text(
                    item, search_pattern, replace, replace_pattern
                )
                number_of_hits_all += number_of_hits
            if continue_search is False:
                break
        return continue_search, number_of_hits_all

    def _search_in_all_text_fields(
        self, search_pattern, replace_pattern, replace, number_of_hits_all
    ) -> tuple[bool, int]:
        continue_search = True
        text_fields = []
        if main_window.language.get() == "VHDL":
            text_fields.append({"tab": GuiTab.INTERFACE, "ref": main_window.interface_package_text, "update": "Ports"})
        text_fields.append({"tab": GuiTab.INTERFACE, "ref": main_window.interface_generics_text, "update": "Generics"})
        text_fields.append({"tab": GuiTab.INTERFACE, "ref": main_window.interface_ports_text, "update": "Ports"})
        if main_window.language.get() == "VHDL":
            text_fields.append({"tab": GuiTab.INTERNALS, "ref": main_window.internals_package_text, "update": ""})
        text_fields.append({"tab": GuiTab.INTERNALS, "ref": main_window.internals_architecture_text, "update": ""})
        text_fields.append({"tab": GuiTab.INTERNALS, "ref": main_window.internals_process_clocked_text, "update": ""})
        text_fields.append(
            {"tab": GuiTab.INTERNALS, "ref": main_window.internals_process_combinatorial_text, "update": ""}
        )
        text_fields.append({"tab": GuiTab.GENERATED_HDL, "ref": main_window.hdl_frame_text, "update": ""})
        for text_field in text_fields:
            if continue_search:
                continue_search, number_of_hits = self._search_in_text_field(
                    text_field, search_pattern, replace, replace_pattern
                )
                number_of_hits_all += number_of_hits
        return continue_search, number_of_hits_all

    def _get_text_ids_of_canvas_window(self, item) -> list:
        text_ids = []
        if item in state_action_handling.MyText.mytext_dict:
            text_ids.append(state_action_handling.MyText.mytext_dict[item].text_id)
        elif item in condition_action_handling.ConditionAction.dictionary:
            text_ids.append(condition_action_handling.ConditionAction.dictionary[item].condition_id)
            text_ids.append(condition_action_handling.ConditionAction.dictionary[item].action_id)
        elif item in global_actions.GlobalActions.dictionary:
            text_ids.append(global_actions.GlobalActions.dictionary[item].text_before_id)
            text_ids.append(global_actions.GlobalActions.dictionary[item].text_after_id)
        elif item in global_actions_combinatorial.GlobalActionsCombinatorial.dictionary:
            text_ids.append(global_actions_combinatorial.GlobalActionsCombinatorial.dictionary[item].text_id)
        elif item in state_actions_default.StateActionsDefault.dictionary:
            text_ids.append(state_actions_default.StateActionsDefault.dictionary[item].text_id)
        elif item in state_comment.StateComment.dictionary:
            text_ids.append(state_comment.StateComment.dictionary[item].text_id)
        return text_ids

    def _search_in_all_text_fields_of_canvas_window(
        self, search_pattern, item, text_ids_of_actions, replace, replace_pattern
    ) -> tuple[bool, int]:
        number_of_hits_all = 0
        for text_id in text_ids_of_actions:
            text_field = {"tab": GuiTab.DIAGRAM, "ref": text_id, "update": "", "window_id": item}
            continue_search, number_of_hits = self._search_in_text_field(
                text_field, search_pattern, replace, replace_pattern
            )
            if not continue_search:
                break
            number_of_hits_all += number_of_hits
        return continue_search, number_of_hits_all

    def _search_in_canvas_text(self, item, search_pattern, replace, replace_pattern) -> tuple[bool, int]:
        text = main_window.canvas.itemcget(item, "text")
        start = 0
        number_of_hits = 0
        continue_search = True
        while True:
            hit_begin = text.find(search_pattern, start, len(text))
            if hit_begin == -1:
                break
            if replace:
                search_pattern = re.escape(search_pattern)
                replace_pattern = re.escape(replace_pattern)
                number_of_hits = len(re.findall(search_pattern, text, flags=re.IGNORECASE))
                text = re.sub(search_pattern, replace_pattern, text, flags=re.IGNORECASE)
                main_window.canvas.itemconfigure(item, text=text)
                start = len(text)  # The search-pattern cannot be found again in the next loop.
            else:
                number_of_hits += 1
                self._move_in_foreground(GuiTab.DIAGRAM)
                main_window.canvas.select_from(item, hit_begin)
                main_window.canvas.select_to(item, hit_begin + len(search_pattern) - 1)
                object_coords = main_window.canvas.bbox(item)
                canvas_editing.view_rectangle(object_coords, check_fit=False)
                object_center = main_window.canvas.coords(item)
                canvas_editing.canvas_zoom(object_center, 0.25)
                continue_search = messagebox.askyesno("Continue", "Find next")
                if continue_search is False:
                    break
                start = hit_begin + len(search_pattern)
            if start == hit_begin:
                messagebox.showinfo(
                    "HDL-FSM-Editor", "Search in canvas text is aborted as for unknown reason no progress happens."
                )
                break
        return continue_search, number_of_hits

    def _search_in_text_field(self, text_field, search_pattern, replace, replace_pattern) -> tuple[bool, int]:
        count = tk.IntVar()
        number_of_hits = 0
        start = "1.0"
        continue_search = True
        while True:
            index = text_field["ref"].search(
                search_pattern, start, tk.END, count=count, regexp=True, nocase=1
            )  # index = "line.column"
            if index == "" or count.get() == 0:
                break
            number_of_hits += 1
            if replace:
                end_index = index + "+" + str(len(search_pattern)) + " chars"
                text_field["ref"].delete(index, end_index)
                text_field["ref"].insert(index, replace_pattern)
                start = index + "+" + str(len(replace_pattern)) + " chars"
                if text_field["tab"] == GuiTab.INTERFACE:
                    if text_field["update"] == "Generics":
                        text_field["ref"].update_custom_text_class_generics_list()
                    else:  # kind=="ports"
                        text_field["ref"].update_custom_text_class_ports_list()
                elif text_field["tab"] == GuiTab.INTERNALS:
                    text_field["ref"].update_custom_text_class_signals_list()
                elif text_field["tab"] == GuiTab.DIAGRAM:
                    text_field["ref"].format_after_idle()
                else:  # tab=GuiTab.GENERATED_HDL
                    pass
                if text_field["ref"].cget("state") == tk.DISABLED:
                    number_of_hits -= 1  # no replace was possible
            else:
                self._move_in_foreground(text_field["tab"])
                text_field["ref"].tag_add("hit", index, index + " + " + str(count.get()) + " chars")
                text_field["ref"].tag_configure("hit", background="blue")
                start = index + " + " + str(count.get()) + " chars"
                if text_field["tab"] == GuiTab.DIAGRAM:
                    object_coords = main_window.canvas.bbox(text_field["window_id"])
                    canvas_editing.view_rectangle(object_coords, check_fit=False)
                else:
                    text_field["ref"].see(index)
                continue_search = messagebox.askyesno("Continue", "Find next")
                text_field["ref"].tag_remove("hit", index, index + " + " + str(count.get()) + " chars")
                if not continue_search:
                    break
        return continue_search, number_of_hits

    def _move_in_foreground(self, tab: GuiTab) -> None:
        notebook_ids = main_window.notebook.tabs()
        for notebook_id in notebook_ids:
            if main_window.notebook.tab(notebook_id, option="text") == tab.value:
                main_window.notebook.select(notebook_id)
