"""
Gathers design data from elements and canvas for HDL generation.
Imports elements; callers pass DesignData into codegen.
"""

import re

from design_data import DesignData
from elements import (
    condition_action,
    global_actions_clocked,
    global_actions_combinatorial,
    state_action,
    state_actions_default,
    state_comment,
)
from project_manager import project_manager

_RE_CONDITION_ACTION = re.compile(r"^condition_action[0-9]+$")
_RE_TRANSITION_TAG = re.compile(r"^transition[0-9]+$")
_RE_STATE_TAG = re.compile(r"^state[0-9]+$")

# Tag prefix/suffix for parsing canvas tags (avoid magic indices)
_PREFIX_GOING_TO = "going_to_"
_SUFFIX_TRANSITION_START = "_start"
_PREFIX_CA_CONNECTION = "ca_connection"
_SUFFIX_TAG_END = "_end"


def _find_canvas_ids_by_tag_pattern(canvas, pattern: re.Pattern[str]) -> list[tuple[str, list[int]]]:
    """Return (tag, canvas_ids) for each tag matching the regex. Each tag once; ids = find_withtag(tag)."""
    seen: set[str] = set()
    result: list[tuple[str, list[int]]] = []
    for canvas_id in canvas.find_all():
        for tag in canvas.gettags(canvas_id):
            if tag in seen or not pattern.match(tag):
                continue
            seen.add(tag)
            result.append((tag, list(canvas.find_withtag(tag))))
            break
    return result


def _get_text_from_widget(widget, *, include_trailing_newline: bool = False) -> str:
    """Return widget contents; empty string if widget is None.
    If include_trailing_newline is True, use Tk 'end' (keeps trailing newline for block text);
    otherwise use 'end-1c' so codegen can add newlines explicitly."""
    if widget is None:
        return ""
    if include_trailing_newline:
        text = widget.get("1.0", "end")
        return "" if text == "\n" else text
    return widget.get("1.0", "end-1c")


def _get_reset_transition_tag() -> str:
    reset_entry_tags = project_manager.canvas.gettags("reset_entry")
    for t in reset_entry_tags:
        if t.startswith("transition") and t.endswith(_SUFFIX_TRANSITION_START):
            return t.removesuffix(_SUFFIX_TRANSITION_START)
    return ""


def _interface_text_tuple(widget) -> tuple[str, object]:
    """Return (content, widget_ref) with content normalized like get_text_from_text_widget."""
    if widget is None:
        return ("", None)
    content = _get_text_from_widget(widget, include_trailing_newline=True)
    return (content, widget)


def _gather_reset_data() -> tuple[tuple[str, str, object, object] | None, str | None]:
    """Return (reset_condition_action, reset_target_state_name)."""
    reset_transition_tag = _get_reset_transition_tag()
    if not reset_transition_tag:
        return (None, None)
    tags = project_manager.canvas.gettags(reset_transition_tag)
    reset_target_state_name: str | None = None
    for tag in tags:
        if tag.startswith("going_to_state"):
            state_tag_suffix = tag.removeprefix(_PREFIX_GOING_TO)
            reset_target_state_name = project_manager.canvas.itemcget(state_tag_suffix + "_name", "text")
            break
    reset_condition_action: tuple[str, str, object, object] | None = None
    for tag in tags:
        if tag.startswith(_PREFIX_CA_CONNECTION) and tag.endswith(_SUFFIX_TAG_END):
            condition_action_number = tag.removeprefix(_PREFIX_CA_CONNECTION).removesuffix(_SUFFIX_TAG_END)
            condition_action_tag = "condition_action" + condition_action_number
            canvas_ids = project_manager.canvas.find_withtag(condition_action_tag)
            if canvas_ids:
                ref = condition_action.ConditionAction.ref_dict.get(canvas_ids[0])
                if ref is not None:
                    reset_condition_action = (
                        _get_text_from_widget(ref.condition_id),
                        _get_text_from_widget(ref.action_id, include_trailing_newline=True),
                        ref.condition_id,
                        ref.action_id,
                    )
            break
    return (reset_condition_action, reset_target_state_name or "")


def _gather_condition_actions_by_canvas_id() -> dict[int, tuple[str, str, object, object]]:
    """Build condition_action_by_canvas_id from canvas."""
    condition_action_by_canvas_id: dict[int, tuple[str, str, object, object]] = {}
    canvas = project_manager.canvas
    for _, ids in _find_canvas_ids_by_tag_pattern(canvas, _RE_CONDITION_ACTION):
        ref = None
        for i in ids:
            ref = condition_action.ConditionAction.ref_dict.get(i)
            if ref is not None:
                break
        if ref is not None:
            entry = (
                _get_text_from_widget(ref.condition_id),
                _get_text_from_widget(ref.action_id),
                ref.condition_id,
                ref.action_id,
            )
            for i in ids:
                condition_action_by_canvas_id[i] = entry
    return condition_action_by_canvas_id


def _gather_transition_data(
    condition_action_by_canvas_id: dict[int, tuple[str, str, object, object]],
) -> dict[str, tuple[str, str, str, object | None, object | None]]:
    """Build transition_data_by_transition_tag from canvas and condition_action map."""
    transition_data_by_transition_tag: dict[str, tuple[str, str, str, object | None, object | None]] = {}
    canvas = project_manager.canvas
    for transition_tag, ids in _find_canvas_ids_by_tag_pattern(canvas, _RE_TRANSITION_TAG):
        if not ids:
            continue
        tags = canvas.gettags(ids[0])
        target = ""
        cond_text = ""
        act_text = ""
        cond_ref: object | None = None
        action_ref: object | None = None
        for t in tags:
            if t.startswith("going_to_state"):
                state_tag_suffix = t.removeprefix(_PREFIX_GOING_TO)
                target = canvas.itemcget(state_tag_suffix + "_name", "text")
            elif t.startswith("going_to_connector"):
                target = t.removeprefix(_PREFIX_GOING_TO)
            elif t.startswith(_PREFIX_CA_CONNECTION) and t.endswith(_SUFFIX_TAG_END):
                condition_action_number = t.removeprefix(_PREFIX_CA_CONNECTION).removesuffix(_SUFFIX_TAG_END)
                condition_action_tag = "condition_action" + condition_action_number
                ca_ids = canvas.find_withtag(condition_action_tag)
                if ca_ids and ca_ids[0] in condition_action_by_canvas_id:
                    cond_text, act_text, cond_ref, action_ref = condition_action_by_canvas_id[ca_ids[0]]
        transition_data_by_transition_tag[transition_tag] = (
            target,
            cond_text,
            act_text,
            cond_ref,
            action_ref,
        )
    return transition_data_by_transition_tag


def _gather_global_actions() -> tuple[
    tuple[str, object],
    tuple[str, object],
    tuple[str, object],
]:
    """Return (global_actions_before, global_actions_after, concurrent_actions)."""
    global_actions_before: tuple[str, object] = ("", None)
    global_actions_after: tuple[str, object] = ("", None)
    concurrent_actions: tuple[str, object] = ("", None)
    canvas_item_ids_clocked = project_manager.canvas.find_withtag("global_actions1")
    if canvas_item_ids_clocked:
        ref = global_actions_clocked.GlobalActionsClocked.ref_dict.get(canvas_item_ids_clocked[0])
        if ref is not None:
            global_actions_before = (
                _get_text_from_widget(ref.text_before_id, include_trailing_newline=True),
                ref.text_before_id,
            )
            global_actions_after = (
                _get_text_from_widget(ref.text_after_id, include_trailing_newline=True),
                ref.text_after_id,
            )
    canvas_item_ids_comb = project_manager.canvas.find_withtag("global_actions_combinatorial1")
    if canvas_item_ids_comb:
        ref = global_actions_combinatorial.GlobalActionsCombinatorial.ref_dict.get(canvas_item_ids_comb[0])
        if ref is not None:
            concurrent_actions = (
                _get_text_from_widget(ref.text_id, include_trailing_newline=True),
                ref.text_id,
            )
    return (global_actions_before, global_actions_after, concurrent_actions)


def _parse_priority_from_comment_text(text: str) -> int | None:
    """If the first line of text is a non-empty number, return it as int; else None."""
    lines = text.strip().split("\n")
    first_line = lines[0].strip() if lines else ""
    if not first_line or not all(c in "0123456789" for c in first_line):
        return None
    return int(first_line)


def _gather_state_comments_and_ordering(
    warnings: list[str],
) -> tuple[
    dict[str, tuple[str | None, object | None]],
    list[str],
]:
    """Build state_comments_by_state_tag and ordered state_tag_list_sorted (priority then fallback)."""
    state_comments_by_state_tag: dict[str, tuple[str | None, object | None]] = {}
    state_tag_dict_with_prio: dict[int, str] = {}
    state_tag_list: list[str] = []
    canvas = project_manager.canvas

    for tag, ids in _find_canvas_ids_by_tag_pattern(canvas, _RE_STATE_TAG):
        single_element_list = canvas.find_withtag(tag + "_comment")
        if not single_element_list:
            state_tag_list.append(tag)
            state_comments_by_state_tag[tag] = ("", None)
            continue

        ref_sc = state_comment.StateComment.ref_dict.get(single_element_list[0])
        if ref_sc is not None:
            all_tags_of_state = canvas.gettags(ids[0]) if ids else []
            if tag + "_comment_line_end" in all_tags_of_state:
                state_comments_raw = _get_text_from_widget(ref_sc.text_id, include_trailing_newline=True)
                state_comments = re.sub(r"^\s*[0-9]*\s*", "", state_comments_raw)
                widget_ref = ref_sc.text_id if state_comments != "" else None
                state_comments_by_state_tag[tag] = (state_comments, widget_ref)
            else:
                state_comments_by_state_tag[tag] = ("", None)
            comment_text_for_prio = _get_text_from_widget(ref_sc.text_id)
        else:
            state_comments_by_state_tag[tag] = ("", None)
            comment_text_for_prio = ""

        prio = _parse_priority_from_comment_text(comment_text_for_prio)
        if prio is None:
            state_tag_list.append(tag)
        elif prio in state_tag_dict_with_prio:
            state_tag_list.append(tag)
            state_name = canvas.itemcget(tag + "_name", "text")
            warnings.append(
                "The state '"
                + state_name
                + "' uses the order-number "
                + str(prio)
                + " which is already used at another state."
            )
        else:
            state_tag_dict_with_prio[prio] = tag

    state_tag_list_sorted = [tag for _, tag in sorted(state_tag_dict_with_prio.items())]
    state_tag_list_sorted.extend(state_tag_list)
    return (state_comments_by_state_tag, state_tag_list_sorted)


def _gather_state_actions_default() -> tuple[str, object]:
    """Return (state_actions_default_text, widget_ref)."""
    item_ids = project_manager.canvas.find_withtag("state_actions_default")
    if not item_ids:
        return ("", None)
    ref = state_actions_default.StateActionsDefault.ref_dict.get(item_ids[0])
    if ref is None:
        return ("", None)
    comment = "--" if project_manager.language.get() == "VHDL" else "//"
    text = comment + " Default State Actions:\n" + _get_text_from_widget(ref.text_id, include_trailing_newline=True)
    return (text, ref.text_id)


def _gather_state_action_list(
    state_tag_list_sorted: list[str],
) -> list[tuple[str, str, object]]:
    """Build list of (state_name, state_action_text, state_action_ref) in state order."""
    state_action_list_built: list[tuple[str, str, object]] = []
    for state_tag in state_tag_list_sorted:
        state_action_text = "null;\n"
        state_action_ref = None
        for tag_of_state in project_manager.canvas.gettags(state_tag):
            if tag_of_state.startswith("connection") and tag_of_state.endswith(_SUFFIX_TAG_END):
                connection_name = tag_of_state.removesuffix(_SUFFIX_TAG_END)
                state_action_ids = project_manager.canvas.find_withtag(connection_name + "_start")
                if state_action_ids:
                    ref = state_action.StateAction.ref_dict.get(state_action_ids[0])
                    if ref is not None:
                        state_action_text = _get_text_from_widget(ref.text_id, include_trailing_newline=True)
                        state_action_ref = ref.text_id
                break
        state_name = project_manager.canvas.itemcget(state_tag + "_name", "text")
        state_action_list_built.append((state_name, state_action_text, state_action_ref))
    return state_action_list_built


def gather_design_data() -> tuple[DesignData, list[str]]:
    """Build DesignData from canvas and element ref_dicts. Returns (data, warnings). Call before run_hdl_generation."""
    warnings: list[str] = []

    reset_condition_action, reset_target_state_name = _gather_reset_data()
    condition_action_by_canvas_id = _gather_condition_actions_by_canvas_id()
    transition_data_by_transition_tag = _gather_transition_data(condition_action_by_canvas_id)
    global_actions_before, global_actions_after, concurrent_actions = _gather_global_actions()
    state_comments_by_state_tag, state_tag_list_sorted = _gather_state_comments_and_ordering(warnings)
    state_name_by_state_tag = {
        tag: project_manager.canvas.itemcget(tag + "_name", "text") for tag in state_tag_list_sorted
    }
    state_actions_default_tuple = _gather_state_actions_default()
    state_action_list_built = _gather_state_action_list(state_tag_list_sorted)

    interface_package_text = _interface_text_tuple(project_manager.interface_package_text)
    interface_generics_text = _interface_text_tuple(project_manager.interface_generics_text)
    interface_ports_text = _interface_text_tuple(project_manager.interface_ports_text)
    internals_package_text = _interface_text_tuple(project_manager.internals_package_text)
    internals_architecture_text = _interface_text_tuple(project_manager.internals_architecture_text)
    internals_process_clocked_text = _interface_text_tuple(project_manager.internals_process_clocked_text)
    internals_process_combinatorial_text = _interface_text_tuple(project_manager.internals_process_combinatorial_text)

    design_data = DesignData(
        module_name=project_manager.module_name.get(),
        language=project_manager.language.get(),
        reset_signal_name=project_manager.reset_signal_name.get(),
        clock_signal_name=project_manager.clock_signal_name.get(),
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
        state_name_by_state_tag=state_name_by_state_tag,
        condition_action_by_canvas_id=condition_action_by_canvas_id,
        transition_data_by_transition_tag=transition_data_by_transition_tag,
        state_actions_default=state_actions_default_tuple,
        state_action_list=state_action_list_built,
    )
    return (design_data, warnings)
