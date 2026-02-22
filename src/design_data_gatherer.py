"""
Gathers design data from elements and canvas for HDL generation.
Imports elements; callers pass DesignData into codegen.
"""

import re

from design_data import DesignData
from project_manager import project_manager


def _get_reset_transition_tag() -> str:
    reset_entry_tags = project_manager.canvas.gettags("reset_entry")
    for t in reset_entry_tags:
        if t.startswith("transition"):  # look for transition<n>_start
            return t[:-6]
    return ""


def _interface_text_tuple(widget) -> tuple[str, object]:
    """Return (content, widget_ref) with content normalized like get_text_from_text_widget."""
    if widget is None:
        return ("", None)
    text = widget.get("1.0", "end")
    content = "" if text == "\n" else text
    return (content, widget)


def gather_design_data(is_script_mode: bool = False) -> DesignData:
    """Build DesignData from canvas and element ref_dicts. Call before run_hdl_generation."""
    from tkinter import messagebox

    from elements import (
        condition_action,
        global_actions_clocked,
        global_actions_combinatorial,
        state_comment,
        state_action,
        state_actions_default,
    )

    reset_condition_action: tuple[str, str, object, object] | None = None
    reset_target_state_name: str | None = None
    reset_transition_tag = _get_reset_transition_tag()
    if reset_transition_tag:
        tags = project_manager.canvas.gettags(reset_transition_tag)
        for tag in tags:
            if tag.startswith("going_to_state"):
                reset_target_state_name = project_manager.canvas.itemcget(tag[9:] + "_name", "text")
                break
        for tag in tags:
            if tag.startswith("ca_connection"):  # ca_connection<n>_end
                condition_action_number = tag[13:-4]
                condition_action_tag = "condition_action" + condition_action_number
                canvas_ids = project_manager.canvas.find_withtag(condition_action_tag)
                if canvas_ids:
                    ref = condition_action.ConditionAction.ref_dict.get(canvas_ids[0])
                    if ref is not None:
                        condition_text = ref.condition_id.get("1.0", "end-1c")
                        action_text = ref.action_id.get("1.0", "end")
                        reset_condition_action = (
                            condition_text,
                            action_text,
                            ref.condition_id,
                            ref.action_id,
                        )
                break

    condition_action_by_canvas_id: dict[int, tuple[str, str, object, object]] = {}
    reg_ca = re.compile(r"^condition_action[0-9]+$")
    seen_tags: set[str] = set()
    for canvas_id in project_manager.canvas.find_all():
        for tag in project_manager.canvas.gettags(canvas_id):
            if reg_ca.match(tag) and tag not in seen_tags:
                seen_tags.add(tag)
                ids = project_manager.canvas.find_withtag(tag)
                ref = None
                for i in ids:
                    ref = condition_action.ConditionAction.ref_dict.get(i)
                    if ref is not None:
                        break
                if ref is not None:
                    cond_text = ref.condition_id.get("1.0", "end-1c")
                    act_text = ref.action_id.get("1.0", "end-1c")
                    entry = (cond_text, act_text, ref.condition_id, ref.action_id)
                    for i in ids:
                        condition_action_by_canvas_id[i] = entry
                break

    global_actions_before: tuple[str, object] = ("", None)
    global_actions_after: tuple[str, object] = ("", None)
    concurrent_actions: tuple[str, object] = ("", None)
    canvas_item_ids_clocked = project_manager.canvas.find_withtag("global_actions1")
    if canvas_item_ids_clocked:
        ref = global_actions_clocked.GlobalActionsClocked.ref_dict.get(canvas_item_ids_clocked[0])
        if ref is not None:
            global_actions_before = (ref.text_before_id.get("1.0", "end"), ref.text_before_id)
            global_actions_after = (ref.text_after_id.get("1.0", "end"), ref.text_after_id)
    canvas_item_ids_comb = project_manager.canvas.find_withtag("global_actions_combinatorial1")
    if canvas_item_ids_comb:
        ref = global_actions_combinatorial.GlobalActionsCombinatorial.ref_dict.get(canvas_item_ids_comb[0])
        if ref is not None:
            concurrent_actions = (ref.text_id.get("1.0", "end"), ref.text_id)

    state_comments_by_state_tag: dict[str, tuple[str | None, object | None]] = {}
    state_tag_dict_with_prio: dict[int, str] = {}
    state_tag_list: list[str] = []
    reg_ex_for_state_tag = re.compile("^state[0-9]+$")
    for canvas_id in project_manager.canvas.find_all():
        for tag in project_manager.canvas.gettags(canvas_id):
            if reg_ex_for_state_tag.match(tag):
                single_element_list = project_manager.canvas.find_withtag(tag + "_comment")
                if not single_element_list:
                    state_tag_list.append(tag)
                    state_comments_by_state_tag[tag] = ("", None)
                else:
                    ref_sc = state_comment.StateComment.ref_dict.get(single_element_list[0])
                    if ref_sc is not None:
                        all_tags_of_state = project_manager.canvas.gettags(canvas_id)
                        if tag + "_comment_line_end" in all_tags_of_state:
                            state_comments_raw = ref_sc.text_id.get("1.0", "end")
                            state_comments = re.sub(r"^\s*[0-9]*\s*", "", state_comments_raw)
                            widget_ref = ref_sc.text_id if state_comments != "" else None
                            state_comments_by_state_tag[tag] = (state_comments, widget_ref)
                        else:
                            state_comments_by_state_tag[tag] = ("", None)
                    else:
                        state_comments_by_state_tag[tag] = ("", None)
                    state_comments_for_prio = ref_sc.text_id.get("1.0", "end-1c") if ref_sc else ""
                    state_comments_list = state_comments_for_prio.split("\n")
                    first_line = state_comments_list[0].strip() if state_comments_list else ""
                    if first_line == "":
                        state_tag_list.append(tag)
                    else:
                        first_line_is_number = bool(all(c in "0123456789" for c in first_line))
                        if not first_line_is_number:
                            state_tag_list.append(tag)
                        else:
                            prio = int(first_line)
                            if prio in state_tag_dict_with_prio:
                                state_tag_list.append(tag)
                                if is_script_mode:
                                    print(
                                        "Warning in HDL-FSM-Editor: "
                                        + "The state '"
                                        + project_manager.canvas.itemcget(tag + "_name", "text")
                                        + "' uses the order-number "
                                        + first_line
                                        + " which is already used at another state."
                                    )
                                else:
                                    messagebox.showwarning(
                                        "Warning in HDL-FSM-Editor",
                                        "The state '"
                                        + project_manager.canvas.itemcget(tag + "_name", "text")
                                        + "' uses the order-number "
                                        + first_line
                                        + " which is already used at another state.",
                                    )
                            else:
                                state_tag_dict_with_prio[prio] = tag
                break

    state_tag_list_sorted = [tag for _, tag in sorted(state_tag_dict_with_prio.items())]
    state_tag_list_sorted.extend(state_tag_list)

    state_actions_default_tuple: tuple[str, object] = ("", None)
    item_ids = project_manager.canvas.find_withtag("state_actions_default")
    if item_ids:
        ref = state_actions_default.StateActionsDefault.ref_dict.get(item_ids[0])
        if ref is not None:
            comment = "--" if project_manager.language.get() == "VHDL" else "//"
            text = comment + " Default State Actions:\n" + ref.text_id.get("1.0", "end")
            state_actions_default_tuple = (text, ref.text_id)

    state_action_list_built: list[tuple[str, str, object]] = []
    for state_tag in state_tag_list_sorted:
        state_action_text = "null;\n"
        state_action_ref = None
        for tag_of_state in project_manager.canvas.gettags(state_tag):
            if tag_of_state.startswith("connection") and tag_of_state.endswith("_end"):
                connection_name = tag_of_state[:-4]
                state_action_ids = project_manager.canvas.find_withtag(connection_name + "_start")
                if state_action_ids:
                    ref = state_action.StateAction.ref_dict.get(state_action_ids[0])
                    if ref is not None:
                        state_action_text = ref.text_id.get("1.0", "end")
                        state_action_ref = ref.text_id
                    break
        state_name = project_manager.canvas.itemcget(state_tag + "_name", "text")
        state_action_list_built.append((state_name, state_action_text, state_action_ref))

    interface_package_text = _interface_text_tuple(project_manager.interface_package_text)
    interface_generics_text = _interface_text_tuple(project_manager.interface_generics_text)
    interface_ports_text = _interface_text_tuple(project_manager.interface_ports_text)
    internals_package_text = _interface_text_tuple(project_manager.internals_package_text)
    internals_architecture_text = _interface_text_tuple(project_manager.internals_architecture_text)
    internals_process_clocked_text = _interface_text_tuple(project_manager.internals_process_clocked_text)
    internals_process_combinatorial_text = _interface_text_tuple(project_manager.internals_process_combinatorial_text)

    return DesignData(
        reset_condition_action=reset_condition_action,
        reset_target_state_name=reset_target_state_name,
        interface_package_text=interface_package_text,
        interface_generics_text=interface_generics_text,
        interface_ports_text=interface_ports_text,
        internals_package_text=internals_package_text,
        internals_architecture_text=internals_architecture_text,
        internals_process_clocked_text=internals_process_clocked_text,
        internals_process_combinatorial_text=internals_process_combinatorial_text,
        global_actions_before=global_actions_before,
        global_actions_after=global_actions_after,
        concurrent_actions=concurrent_actions,
        state_comments_by_state_tag=state_comments_by_state_tag,
        state_tag_list_sorted=state_tag_list_sorted,
        condition_action_by_canvas_id=condition_action_by_canvas_id,
        state_actions_default=state_actions_default_tuple,
        state_action_list=state_action_list_built,
    )
