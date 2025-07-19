"""
This module contains methods used at HDL generation.
"""

import contextlib
import re
import tkinter as tk
from tkinter import messagebox

import canvas_editing
import condition_action_handling
import global_actions
import global_actions_combinatorial
import global_actions_handling
import main_window
import state_comment


def indent_text_by_the_given_number_of_tabs(number_of_tabs, text):
    keep_newline_at_each_line_end = True
    list_of_lines = text.splitlines(keep_newline_at_each_line_end)
    result_string = ""
    for line in list_of_lines:
        for _ in range(number_of_tabs):
            line = "    " + line
        result_string += line
    return result_string


def get_text_from_text_widget(wiget_id):
    text = wiget_id.get("1.0", tk.END)
    if text != "\n":
        return text
    return ""


def get_a_list_of_all_state_names():
    state_name_list = []
    first_state_name = ""
    all_canvas_items = main_window.canvas.find_all()
    reg_ex_for_state_tag = re.compile("^state[0-9]+$")
    for item in all_canvas_items:
        all_item_tags = main_window.canvas.gettags(item)
        for tag in all_item_tags:
            if reg_ex_for_state_tag.match(tag):
                state_name_list.append(main_window.canvas.itemcget(tag + "_name", "text"))
            if tag == "coming_from_reset_entry":
                tags_of_reset_transition = main_window.canvas.gettags(item)
                for tag in tags_of_reset_transition:
                    if tag.startswith("going_to_state"):
                        first_state_name = main_window.canvas.itemcget(tag[9:] + "_name", "text")
    state_name_list_sorted = sorted(state_name_list)
    with contextlib.suppress(Exception):
        state_name_list_sorted.remove(first_state_name)
    state_name_list_sorted = [first_state_name] + state_name_list_sorted
    return state_name_list_sorted


def _get_target_state_name(all_reset_transition_tags):
    target_state_tag = ""
    for t in all_reset_transition_tags:
        if t.startswith("going_to_state"):
            target_state_tag = t[9:]
    target_state_name = main_window.canvas.itemcget(target_state_tag + "_name", "text")
    return target_state_name


def create_reset_condition_and_reset_action():
    reset_transition_tag = _get_reset_transition_tag()
    ref = _get_condition_action_reference_of_transition(reset_transition_tag)
    if ref is None:
        reference_to_reset_condition_custom_text = None
        reference_to_reset_action_custom_text = None
        action = ""
        condition = ""
        messagebox.showerror(
            "Error",
            """No reset condition is specified,
therefore the generated HDL will be corrupted.
Please specify the reset condition by using the right
mouse button at the transition from the reset-connector
to the state, which shall be reached by active reset.""",
        )
    else:
        reference_to_reset_condition_custom_text = ref.condition_id
        condition = reference_to_reset_condition_custom_text.get(
            "1.0", tk.END + "-1 chars"
        )  # without "return" at the end
        all_reset_transition_tags = main_window.canvas.gettags(reset_transition_tag)
        target_state_name = _get_target_state_name(all_reset_transition_tags)
        action = "state <= " + target_state_name + ";\n"
        reference_to_reset_action_custom_text = ref.action_id
        action_text = reference_to_reset_action_custom_text.get(
            "1.0", tk.END
        )  # action_text will always have a return as last character.
        if action_text != "\n":  # check for empty line
            action += action_text
    return [condition, action, reference_to_reset_condition_custom_text, reference_to_reset_action_custom_text]


def _get_reset_transition_tag():
    reset_entry_tags = main_window.canvas.gettags("reset_entry")
    reset_transition_tag = ""
    for t in reset_entry_tags:
        if t.startswith("transition"):  # look for transition<n>_start
            reset_transition_tag = t[:-6]
    return reset_transition_tag


def _get_transition_target_condition_action(transition_tag):
    tags = main_window.canvas.gettags(transition_tag)
    transition_condition = ""
    transition_action = ""
    condition_action_reference = ""
    transition_target = ""
    for tag in tags:
        if tag.startswith("going_to_state"):
            transition_target_tag = tag[9:]
            transition_target = main_window.canvas.itemcget(transition_target_tag + "_name", "text")
        elif tag.startswith("going_to_connector"):
            transition_target = tag[9:]
        elif tag.startswith("ca_connection"):  # Complete tag: ca_connection<n>_end
            condition_action_number = tag[13:-4]
            condition_action_tag = "condition_action" + condition_action_number
            condition_action_canvas_item_id = main_window.canvas.find_withtag(condition_action_tag)[0]
            condition_action_reference = condition_action_handling.ConditionAction.dictionary[
                condition_action_canvas_item_id
            ]
            if condition_action_reference is not None:
                transition_condition = _get_transition_condition(condition_action_reference)
                transition_action = _get_transition_action(condition_action_reference)
    return transition_target, transition_condition, transition_action, condition_action_reference


def _get_condition_action_reference_of_transition(transition_tag):
    tags = main_window.canvas.gettags(transition_tag)
    for tag in tags:
        if tag.startswith("ca_connection"):  # Complete tag: ca_connection<n>_end
            condition_action_number = tag[13:-4]
            condition_action_tag = "condition_action" + condition_action_number
            condition_action_canvas_item_id = main_window.canvas.find_withtag(condition_action_tag)[0]
            condition_action_reference = condition_action_handling.ConditionAction.dictionary[
                condition_action_canvas_item_id
            ]
            return condition_action_reference
    return None


def _get_target_tag_of_transition(transition_tag):
    transition_tags = main_window.canvas.gettags(transition_tag)
    for transition_tag in transition_tags:
        if transition_tag.startswith("going_to_"):
            return transition_tag[9:]


def extract_transition_specifications_from_the_graph():
    list_of_all_state_tags = _get_a_list_of_all_state_tags()  # list_of_all_state_tags = ["state1", "state2", ...]
    transition_specifications = []
    for state_tag in list_of_all_state_tags:
        state_name = main_window.canvas.itemcget(state_tag + "_name", "text")
        all_tags_of_state = main_window.canvas.gettags(state_tag)
        if state_tag + "_comment_line_end" in all_tags_of_state:
            canvas_id_of_comment_window = main_window.canvas.find_withtag(state_tag + "_comment")[0]
            reference_to_state_comment_window = state_comment.StateComment.dictionary[canvas_id_of_comment_window]
            canvas_id_of_comment_text_widget = reference_to_state_comment_window.text_id
            state_comments = reference_to_state_comment_window.text_id.get("1.0", "end")
        else:
            canvas_id_of_comment_text_widget = None
            state_comments = ""
        condition_level = 0
        moved_actions = []
        trace = []  # Is temporarily used when a path from a state to a target state passes connectors.
        trace_array = []
        # Each entry of trace_array shall describe a path from this state to a target state (target state is always also this state).
        # The entries of trace_array are ordered regarding their priority in the HDL, the first entry has the highest priority.
        # Each entry is a ordered list of dictionaries.
        # The order of the dictionaries is defined by the order in which the HDL lines must be generated.
        # Each dictionary contains all information to create one or several HDL lines.
        _extract_conditions_for_all_outgoing_transitions_of_the_state(
            state_name, state_tag, moved_actions, condition_level, trace, trace_array
        )
        transition_specifications.append(
            {
                "state_name": state_name,
                "command": "when",
                "state_comments": state_comments,
                "state_comments_canvas_id": canvas_id_of_comment_text_widget,
            }
        )
        # The separated paths of trace_array are merged together by adding "else" commands,
        # so if the first trace depends on an "if", then the inserted "else" path of the first trace contains the second trace and so on:
        transition_specifications += _merge_trace_array(trace_array)
    _optimize_transition_specifications(transition_specifications)
    return transition_specifications


def _optimize_transition_specifications(transition_specifications):
    # Add an unique if-identifier to each transition_specification of the transition_specifications.
    # At each if, the identifier is incremented, at each end-if it is decremented.
    # Also add to each end-if transition specification the number of branches of this ending if-construct:
    _expand_transition_specifications_by_if_identifier(transition_specifications)
    # action_target_array is a dictionary with the state name as key.
    # It contains for each state name a dictionary which describes the actions to a specific target state:
    action_target_array, branchnumber_array = _create_action_and_branch_array_for_each_if_construct(
        transition_specifications
    )
    changes_were_implemented = False
    index_of_if_in_transition_specifications = 0
    for state_name, action_target_if_dictionary in action_target_array.items():
        for if_identifier in action_target_if_dictionary:
            if if_identifier != 0:  # if_identifier==0 means this is an entry caused by a "when"-command.
                if (
                    len(
                        action_target_array[state_name][if_identifier]
                    )  # This is the number of different actions&targets which exist for the if_identifier.
                    == branchnumber_array[state_name][
                        if_identifier
                    ]  # This is the number of branches which exist for the if_identifier.
                    != 1
                ):  # There is more than 1 branch for the if_identifier.
                    moved_actions = []
                    moved_target = []  # will get only 1 entry
                    for action_target_dict in action_target_array[state_name][if_identifier]:
                        for action in action_target_dict["actions"]:
                            if _action_is_present_in_each_branch(action, state_name, if_identifier, action_target_array):
                                index_of_if_in_transition_specifications = _remove_action_from_branches(
                                    transition_specifications, state_name, if_identifier, action, moved_actions
                                )
                                changes_were_implemented = True
                        target = action_target_dict["target"]
                        if target != "":
                            if _target_is_present_in_each_branch(target, state_name, if_identifier, action_target_array):
                                index_of_if_in_transition_specifications = _remove_target_from_branches(
                                    transition_specifications, state_name, if_identifier, target, moved_target
                                )
                                changes_were_implemented = True
                    if moved_actions or moved_target:
                        target = "" if not moved_target else moved_target[0]
                        # Insert a new entry into the list of transition_specifications:
                        transition_specifications[
                            index_of_if_in_transition_specifications:index_of_if_in_transition_specifications
                        ] = [
                            {
                                "state_name": state_name,
                                "command": "action",
                                "condition": "",
                                "actions": moved_actions,
                                "target": target,
                                "if_identifier": if_identifier - 1,
                            }
                        ]
    if changes_were_implemented:
        _optimize_transition_specifications(transition_specifications)
    return


def _expand_transition_specifications_by_if_identifier(transition_specifications):
    if_identifier = 0
    if_identifier_max = 0
    for transition_specification in transition_specifications:
        if transition_specification["command"] == "when":
            if_identifier_max = max(if_identifier_max, if_identifier)
            if_identifier = 0
            stack_of_if_identifier = [0]
            stack_of_branch_number = [0]
            transition_specification["if_identifier"] = if_identifier
        elif transition_specification["command"] == "if":
            if_identifier += 1
            transition_specification["if_identifier"] = if_identifier
            stack_of_if_identifier.append(if_identifier)
            stack_of_branch_number.append(1)
        elif transition_specification["command"] == "endif":
            transition_specification["if_identifier"] = stack_of_if_identifier[-1]
            transition_specification["branch_number"] = stack_of_branch_number[
                -1
            ]  # This entry counts how many branches an "if" has, starting with 1.
            stack_of_if_identifier.pop()
            stack_of_branch_number.pop()
        elif transition_specification["command"] == "elsif" or transition_specification["command"] == "else":
            transition_specification["if_identifier"] = stack_of_if_identifier[-1]
            stack_of_branch_number[-1] += 1
        else:  # "action"
            transition_specification["if_identifier"] = stack_of_if_identifier[-1]


def _create_action_and_branch_array_for_each_if_construct(transition_specifications):
    # The return dictionary action_target_array[state_name][if_identifier][0..n] is an dictionary with the keys "actions" and "target".
    # The key "actions" stores a list of actions which are executed in this branch.
    # The key "target" stores the target state of this branch.
    # The return dictionary branchnumber_array contains for each state a dictionary with transition_specification["if_identifier"] as key,
    # where the value is the number of branches the "if" has.
    action_target_array_of_state = {}
    branchnumber_array_of_state = {}
    action_target_array = {}
    branchnumber_array = {}
    for transition_specification in transition_specifications:
        if transition_specification["command"] == "when":
            if action_target_array_of_state:  # The analysis of a state is ready.
                action_target_array[state_name] = action_target_array_of_state
                branchnumber_array[state_name] = branchnumber_array_of_state
                action_target_array_of_state = {}
                branchnumber_array_of_state = {}
            state_name = transition_specification["state_name"]  # start new analysis
        elif transition_specification["command"] == "action":
            if_identifier = transition_specification["if_identifier"]
            if if_identifier not in action_target_array_of_state:
                action_target_array_of_state[if_identifier] = []
            copy_of_actions = []
            for entry in transition_specification["actions"]:
                copy_of_actions.append(
                    entry
                )  # Create a copy because later on the list transition_specification["actions"] is modified and would modify if_array also.
            action_target_array_of_state[if_identifier].append(
                {"actions": copy_of_actions, "target": transition_specification["target"]}
            )
        elif transition_specification["command"] == "endif":
            branchnumber_array_of_state[transition_specification["if_identifier"]] = transition_specification[
                "branch_number"
            ]
    if action_target_array_of_state:  # Needed for the last state, as no new "when" will come after the last state.
        action_target_array[state_name] = action_target_array_of_state
        branchnumber_array[state_name] = branchnumber_array_of_state
    return action_target_array, branchnumber_array


def _action_is_present_in_each_branch(action, state_name, if_identifier, action_target_array):
    for action_target_dict_check in action_target_array[state_name][if_identifier]:
        if action not in action_target_dict_check["actions"]:
            return False
    return True


def _remove_action_from_branches(transition_specifications, state_name, if_identifier, action, moved_actions):
    index_of_if_in_transition_specifications = 0
    for index, transition_specification in enumerate(transition_specifications):
        if (
            transition_specification["state_name"] == state_name
            and transition_specification["if_identifier"] == if_identifier
        ):
            if transition_specification["command"] == "if":
                index_of_if_in_transition_specifications = index
            elif transition_specification["command"] == "action":
                if action in transition_specification["actions"]:
                    # This creates problems:
                    # transition_specification["actions"].remove(action)
                    # The reason is, that when the entry "action" is removed from the list, also in another transition_specification["actions"]
                    # a entry disappears, if it is identical to action.
                    # The solution is to create a new list:
                    transition_specification["actions"] = [
                        x for x in transition_specification["actions"] if x != action
                    ]
                if action not in moved_actions:
                    moved_actions.append(action)
    return index_of_if_in_transition_specifications


def _remove_target_from_branches(transition_specifications, state_name, if_identifier, target, moved_target):
    index_of_if_in_transition_specifications = 0
    for index, transition_specification in enumerate(transition_specifications):
        if (
            transition_specification["state_name"] == state_name
            and transition_specification["if_identifier"] == if_identifier
        ):
            if transition_specification["command"] == "if":
                index_of_if_in_transition_specifications = index
            elif transition_specification["command"] == "action":
                if target == transition_specification["target"]:
                    transition_specification["target"] = ""
                    if target not in moved_target:
                        moved_target.append(target)
    return index_of_if_in_transition_specifications


def _target_is_present_in_each_branch(target, state_name, if_identifier, action_target_array):
    for action_target_dict_check in action_target_array[state_name][if_identifier]:
        if target != action_target_dict_check["target"]:
            return False
    return True


def _check_for_wrong_priorities(trace_array):
    condition_array = []
    for trace in trace_array:
        # Each trace starts like this:
        # [{'state_name': 'filled', 'command': 'if'    , 'condition': "read_fifo_i='1'"           , ...
        #  {'state_name': 'filled', 'command': 'if'    , 'condition': 'read_address=write_address', ...
        #  {'state_name': 'filled', 'command': 'action', 'condition': ''                          , ...]
        # All the conditions of a trace together determine, if the action is executed.
        # If a next trace starts with the same conditions, then this next trace is obsolete, as it will never be reached.
        # This is checked here:
        condition_sequence = []
        for trace_dict in trace:
            if trace_dict["command"] == "if":
                condition_sequence.append(trace_dict["condition"])
        condition_array.append(condition_sequence)
    for index, condition_sequence in enumerate(condition_array):
        if index < len(condition_array) - 1 and (
            condition_sequence == condition_array[index + 1][0 : len(condition_sequence)]
        ):  # Check if the next trace starts with the same conditions.
            condition_sequence_string = ""
            for single_condition in condition_sequence:
                condition_sequence_string += single_condition + ","
            if condition_sequence_string != "":
                condition_sequence_string = condition_sequence_string[:-1]
                messagebox.showerror(
                    "Error in HDL-FSM-Editor",
                    "A transition starting at state "
                    + trace_array[index][0]["state_name"]
                    + "\n"
                    + "with the condition sequence "
                    + condition_sequence_string
                    + "\n"
                    + "hides a transition with lower priority."
                    + "\n"
                    + "This is not allowed and will corrupt the HDL.",
                )
            else:
                messagebox.showerror(
                    "Error in HDL-FSM-Editor",
                    "A transition starting at state "
                    + trace_array[index][0]["state_name"]
                    + "\n"
                    + "with no condition hides a transition with lower priority."
                    + "\n"
                    + "This is not allowed and will corrupt the HDL.",
                )


def _merge_trace_array(trace_array):
    _check_for_wrong_priorities(trace_array)
    traces_of_a_state_reversed = list(reversed(trace_array))  # Start with the trace, which has lowest priority.
    for trace_index, trace in enumerate(traces_of_a_state_reversed):
        if (
            trace_index == len(traces_of_a_state_reversed) - 1
        ):  # The last trace is the result of this for-loop and will only be checked for a condition:
            if (
                trace != [] and trace[0]["command"] != "if" and trace_index != 0
            ):  # Check is only done, when more than 1 trace exists.
                messagebox.showerror(
                    "Warning",
                    "There is a transition starting at state "
                    + trace[0]["state_name"]
                    + " which has no condition but does not have the lowest priority,\ntherefore the generated HDL may be corrupted.",
                )
        else:
            if trace:  # An empty trace may happen, when the transition with lowest priority has no condition and action (and has a connector?!).
                first_command_of_trace = trace[0]["command"] + trace[0]["condition"]
                first_command_of_next_trace = (
                    traces_of_a_state_reversed[trace_index + 1][0]["command"]
                    + traces_of_a_state_reversed[trace_index + 1][0]["condition"]
                )
                if (
                    trace_index != 0  # This trace is not the trace with the lowest priority
                    and trace[0]["command"] != "if"
                ):  # The first command of this trace has no condition.
                    # All traces except the trace with the lowest priority must start with an "if":
                    messagebox.showerror(
                        "Warning",
                        "There is a transition starting at state "
                        + trace[0]["state_name"]
                        + " which has no condition but does not have the lowest priority,\ntherefore the generated HDL may be corrupted.",
                    )
                if trace[0]["command"] == "action":
                    # insert before the endif, which's existence was tested here.
                    traces_of_a_state_reversed[trace_index + 1][-1:-1] = [
                        {
                            "state_name": trace[0]["state_name"],
                            "command": "else",
                            "condition": "",
                            "condition_action_reference": None,
                        }
                    ]
                    traces_of_a_state_reversed[trace_index + 1][-1:-1] = (
                        trace  # insert before the endif, which's existence was tested here.
                    )
                elif first_command_of_trace != first_command_of_next_trace:
                    trace[0]["command"] = "elsif"
                    traces_of_a_state_reversed[trace_index + 1] = traces_of_a_state_reversed[trace_index + 1][
                        :-1
                    ]  # remove endif
                    traces_of_a_state_reversed[trace_index + 1] += trace
                else:  # Both traces start with the same command.
                    search_index = 1  # Look into the next command of the two traces.
                    target_at_error = ""
                    while (trace[search_index]["command"] + trace[search_index]["condition"]) == (
                        traces_of_a_state_reversed[trace_index + 1][search_index]["command"]
                        + traces_of_a_state_reversed[trace_index + 1][search_index]["condition"]
                    ):
                        if trace[search_index]["target"] != "":
                            target_at_error = trace[search_index]["target"]
                        if (
                            search_index == len(trace) - 1
                            or search_index == len(traces_of_a_state_reversed[trace_index + 1]) - 1
                        ):
                            messagebox.showerror(
                                "Error",
                                "There is a transition starting at state "
                                + trace[0]["state_name"]
                                + " to state "
                                + target_at_error
                                + " which will never fire,\ntherefore the generated HDL may be corrupted.",
                            )
                            break
                        search_index += 1
                    # search_index selects a different command in trace[]:
                    if trace[search_index]["command"] == "if":
                        trace[search_index]["command"] = "elsif"
                        # The "endif"s of the identical commands and the new "elsif" are all copied:
                        traces_of_a_state_reversed[trace_index + 1][-(search_index + 1) : -(search_index + 1)] = trace[
                            search_index:
                        ]
                        # Remove superfluous (search_index+1)*"endifs", which were copied with trace:
                        traces_of_a_state_reversed[trace_index + 1] = traces_of_a_state_reversed[trace_index + 1][
                            : -(search_index + 1)
                        ]
                    else:  # The command is an "action" without any condition, so it must be converted into an "else".
                        traces_of_a_state_reversed[trace_index + 1][-(search_index + 1) : -(search_index + 1)] = [
                            {
                                "state_name": trace[search_index]["state_name"],
                                "command": "else",
                                "condition": "",
                                "condition_action_reference": None,
                            }
                        ]
                        traces_of_a_state_reversed[trace_index + 1][-(search_index + 1) : -(search_index + 1)] = trace[
                            search_index : search_index + 1
                        ]  # copy action to new "else" before "endif"
                        traces_of_a_state_reversed[trace_index + 1][-(search_index):-(search_index)] = trace[
                            search_index + 1 :
                        ]  # copy rest of trace after the endif
                        traces_of_a_state_reversed[trace_index + 1] = traces_of_a_state_reversed[trace_index + 1][
                            :-search_index
                        ]  # remove superfluous "endifs"
    transition_specifications = []
    if traces_of_a_state_reversed:
        for entry in traces_of_a_state_reversed[-1]:
            transition_specifications.append(entry)
    return transition_specifications


def _get_a_list_of_all_state_tags():
    state_tag_list = []
    reg_ex_for_state_tag = re.compile("^state[0-9]+$")
    all_canvas_items = main_window.canvas.find_all()
    for item in all_canvas_items:
        all_tags = main_window.canvas.gettags(item)
        for tag in all_tags:
            if reg_ex_for_state_tag.match(tag):
                state_tag_list.append(tag)
    return sorted(state_tag_list)


def _extract_conditions_for_all_outgoing_transitions_of_the_state(
    state_name,
    start_point,
    moved_actions,
    condition_level,
    trace,
    trace_array,  # initialized by trace_array = []
):
    outgoing_transition_tags = _get_all_outgoing_transitions_in_priority_order(start_point)
    if not outgoing_transition_tags and start_point.startswith("connector"):
        if trace:
            messagebox.showerror(
                "Warning",
                "There is a connector reached from state "
                + trace[0]["state_name"]
                + " which has no outgoing transition,\ntherefore the generated HDL may be corrupted.",
            )
        else:
            messagebox.showerror(
                "Warning",
                "There is a connector "
                + "which has no outgoing transition,\ntherefore the generated HDL may be corrupted.",
            )
    for _, transition_tag in enumerate(outgoing_transition_tags):
        transition_target, transition_condition, transition_action, condition_action_reference = (
            _get_transition_target_condition_action(transition_tag)
        )
        # print("transition_target, transition_condition, transition_action", transition_target, '|' + transition_condition + '|', '|'+transition_action+'|')
        transition_condition_is_a_comment = _check_if_condition_is_a_comment(transition_condition)
        if transition_action != "" or transition_condition_is_a_comment:
            if transition_action != "":
                if transition_condition_is_a_comment:
                    if not transition_condition.endswith("\n"):
                        transition_condition = transition_condition + "\n"
                    transition_action = transition_condition + transition_action
                    moved_actions_dict = {
                        "moved_action": transition_action,
                        "moved_action_ref": condition_action_reference.action_id,
                        "moved_condition_ref": condition_action_reference.condition_id,
                        "moved_condition_lines": transition_condition.count("\n"),
                    }
                else:
                    moved_actions_dict = {
                        "moved_action": transition_action,
                        "moved_action_ref": condition_action_reference.action_id,
                    }
            else:  # transition condition is a comment.
                moved_actions_dict = {
                    "moved_action": transition_condition,
                    "moved_action_ref": condition_action_reference.condition_id,
                }
            transition_action_new = []
            for entry in moved_actions:
                transition_action_new.append(entry)
            transition_action_new.append(moved_actions_dict)
            # print("transition_action_new =", transition_action_new)
        else:
            transition_action_new = moved_actions
        if transition_target.startswith("connector"):
            trace_new = []
            for entry in trace:
                trace_new.append(entry)
            if transition_condition != "" and not transition_condition_is_a_comment:
                trace_new.append(
                    {
                        "state_name": state_name,
                        "command": "if",
                        "condition": transition_condition,
                        "target": transition_target,
                        "condition_level": condition_level,
                        "condition_action_reference": condition_action_reference.condition_id,
                    }
                )
                condition_level_new = condition_level + 1
            else:
                condition_level_new = condition_level
            _extract_conditions_for_all_outgoing_transitions_of_the_state(
                state_name,
                transition_target,
                transition_action_new,
                condition_level_new,
                trace_new,
                trace_array,  # initialized by transition_specifications = []
            )
        else:
            # print(state_name, transition_target, transition_condition, transition_action)
            trace_new = []
            for entry in trace:
                trace_new.append(entry)
            # print("start-point, trace", start_point, trace)
            if transition_condition != "" and not transition_condition_is_a_comment:
                condition_level_new = condition_level + 1
                trace_new.append(
                    {
                        "state_name": state_name,
                        "command": "if",
                        "condition": transition_condition,
                        "target": transition_target,
                        "condition_level": condition_level,
                        "condition_action_reference": condition_action_reference.condition_id,
                    }
                )
            else:
                condition_level_new = condition_level
            if state_name != transition_target:
                trace_new.append(
                    {
                        "state_name": state_name,
                        "command": "action",
                        "condition": "",
                        "actions": transition_action_new,
                        "target": transition_target,
                        "condition_level": condition_level,
                        "condition_action_reference": None,
                    }
                )
            elif transition_action_new != []:  # Create at jumps to itself only an entry, if actions are available.
                trace_new.append(
                    {
                        "state_name": state_name,
                        "command": "action",
                        "condition": "",
                        "actions": transition_action_new,
                        "target": "",
                        "condition_level": condition_level,
                        "condition_action_reference": None,
                    }
                )
            for _ in range(condition_level_new):
                trace_new.append(
                    {
                        "state_name": state_name,
                        "command": "endif",
                        "condition": "",
                        "actions": "",
                        "target": "",
                        "condition_level": condition_level,
                        "condition_action_reference": None,
                    }
                )
            trace_array.append(trace_new)


def _check_if_condition_is_a_comment(transition_condition):
    if transition_condition == "" or transition_condition.isspace():
        return False
    transition_condition_without_comments = remove_comments_and_returns(transition_condition)
    return bool(transition_condition_without_comments == "" or transition_condition_without_comments.isspace())


def _get_all_outgoing_transitions_in_priority_order(state_tag):
    transition_tags_and_priority = _create_outgoing_transition_list_with_priority_information(state_tag)
    transition_tags_and_priority_sorted = sorted(transition_tags_and_priority, key=lambda entry: entry[1])
    _check_for_equal_priorities(transition_tags_and_priority_sorted, state_tag)
    transition_tags_in_priority_order = _remove_priority_information(transition_tags_and_priority_sorted)
    return transition_tags_in_priority_order


def _create_outgoing_transition_list_with_priority_information(state_tag):
    all_tags_of_the_state = main_window.canvas.gettags(state_tag)
    transition_tag_and_priority = []
    for tag in all_tags_of_the_state:
        if tag.endswith("_start"):
            transition_tag = tag[:-6]
            transition_priority_text_tag = transition_tag + "priority"
            transition_priority_string = main_window.canvas.itemcget(transition_priority_text_tag, "text")
            transition_tag_and_priority.append([transition_tag, transition_priority_string])
    return transition_tag_and_priority


def _remove_priority_information(transition_tag_and_priority_sorted):
    transition_tags_in_priority_order = []
    for transition_tag_and_priority in transition_tag_and_priority_sorted:
        transition_tags_in_priority_order.append(transition_tag_and_priority[0])
    return transition_tags_in_priority_order


def _check_for_equal_priorities(transition_tags_and_priority_sorted, state_tag):
    for n in range(len(transition_tags_and_priority_sorted) - 1):
        if transition_tags_and_priority_sorted[n][1] == transition_tags_and_priority_sorted[n + 1][1]:
            object_coords = main_window.canvas.coords(state_tag)
            canvas_editing.view_rectangle(
                [
                    object_coords[0] - 2 * (object_coords[2] - object_coords[0]),
                    object_coords[1] - 2 * (object_coords[3] - object_coords[1]),
                    object_coords[2] + 2 * (object_coords[2] - object_coords[0]),
                    object_coords[3] + 2 * (object_coords[3] - object_coords[1]),
                ],
                check_fit=False,
            )
            state_name = main_window.canvas.itemcget(state_tag + "_name", "text")
            if state_name == "":
                state_name = "a connector"
            messagebox.showerror(
                "Warning",
                "Two outgoing transition of "
                + state_name
                + " have the same priority with value "
                + transition_tags_and_priority_sorted[n + 1][1]
                + ".",
            )


def _get_transition_condition(condition_action_reference):
    return condition_action_reference.condition_id.get("1.0", tk.END + "-1 chars")  # without "return" at the end


def _get_transition_action(condition_action_reference):
    return condition_action_reference.action_id.get("1.0", tk.END + "-1 chars")  # without "return" at the end


def create_global_actions_before():
    if global_actions_handling.global_actions_clocked_number == 1:
        canvas_item_id = main_window.canvas.find_withtag("global_actions1")
        ref = global_actions.GlobalActions.dictionary[canvas_item_id[0]]
        return ref.text_before_id, ref.text_before_id.get("1.0", tk.END)
    return "", ""


def create_global_actions_after():
    if global_actions_handling.global_actions_clocked_number == 1:
        canvas_item_id = main_window.canvas.find_withtag("global_actions1")
        ref = global_actions.GlobalActions.dictionary[canvas_item_id[0]]
        return ref.text_after_id, ref.text_after_id.get("1.0", tk.END)
    return "", ""


def create_concurrent_actions():
    if global_actions_handling.global_actions_combinatorial_number == 1:
        canvas_item_id = main_window.canvas.find_withtag("global_actions_combinatorial1")
        ref = global_actions_combinatorial.GlobalActionsCombinatorial.dictionary[canvas_item_id[0]]
        return ref.text_id, ref.text_id.get("1.0", tk.END)
    return "", ""


def remove_comments_and_returns(hdl_text):
    if main_window.language.get() == "VHDL":
        hdl_text = remove_vhdl_block_comments(hdl_text)
    else:
        hdl_text = _remove_verilog_block_comments(hdl_text)
    lines_without_return = hdl_text.split("\n")
    text = ""
    for line in lines_without_return:
        if main_window.language.get() != "VHDL":
            line_without_comment = re.sub("//.*$", "", line)
        else:
            line_without_comment = re.sub("--.*$", "", line)
        text += (
            " " + line_without_comment
        )  # Add " " at the beginning of the line. Then it is possible to search for keywords surrounded by blanks also at the beginning of text.
    text += " "  # Add " " at the end, so that keywords at the end are also sourrounded by blanks.
    return text


def remove_functions(hdl_text):
    text = re.sub(
        r"(^|\s+)function\s+.*end(\s+function\s*;|function)", "", hdl_text
    )  # Regular expression for VHDL and Verilog function declaration
    return text


def remove_type_declarations(hdl_text):
    text = re.sub(
        r"(^|\s+)type\s+\w+\s+is\s+.*;", "", hdl_text
    )  # Regular expression for VHDL and Verilog function declaration
    return text


def remove_vhdl_block_comments(list_string):
    # block comments are replaced by blanks, so all remaining text holds its position.
    while True:
        match_object = re.search(r"/\*.*?\*/", list_string, flags=re.DOTALL)
        if match_object is None:
            break
        if match_object.start() == match_object.end():
            break
        list_string = (
            list_string[: match_object.start()]
            + " " * (match_object.end() - match_object.start())
            + list_string[match_object.end() :]
        )
    return list_string


def _remove_verilog_block_comments(hdl_text):
    return re.sub("/\\*.*\\*/", "", hdl_text, flags=re.DOTALL)


def convert_hdl_lines_into_a_searchable_string(text):
    without_comments = remove_comments_and_returns(text)
    separated = surround_character_by_blanks(";", without_comments)
    separated = surround_character_by_blanks(r"\(", separated)  # "\" is needed to be able to search for "("
    separated = surround_character_by_blanks(r"\)", separated)  # "\" is needed to be able to search for ")"
    separated = surround_character_by_blanks(":", separated)
    separated = surround_character_by_blanks("!=", separated)
    separated = surround_character_by_blanks("!", separated)
    separated = surround_character_by_blanks("/", separated)
    separated = surround_character_by_blanks("=", separated)
    separated = surround_character_by_blanks(">", separated)
    separated = surround_character_by_blanks("<", separated)
    separated = surround_character_by_blanks(",", separated)
    separated = surround_character_by_blanks("'", separated)
    separated = surround_character_by_blanks(r"\+", separated)
    separated = surround_character_by_blanks("-", separated)
    separated = re.sub("<  =", "<=", separated)  # restore this operator (assignment or comparison)
    separated = re.sub(">  =", ">=", separated)  # restore this operator (comparison)
    separated = re.sub("=  >", "=>", separated)  # restore this operator (when selector in VHDL)
    separated = re.sub("=  =", "==", separated)  # restore this operator (comparison)
    separated = re.sub("/  =", "/=", separated)  # restore this operator (comparison)
    separated = re.sub(":  =", ":=", separated)  # restore this operator (assignment)
    separated = re.sub("!  =", "!=", separated)  # restore this operator (comparison)
    separated = re.sub("'.*?'", "", separated)  # Remove strings '...' from report-commands (they might contain ';')
    separated = re.sub('".*?"', "", separated)  # Remove strings "..." from report-commands (they might contain ';')
    return separated


def surround_character_by_blanks(character, all_port_declarations_without_comments):
    if character.startswith("\\"):
        original_character = character[1:]  # remove "\"
    else:
        original_character = character
    return re.sub(character, " " + original_character + " ", all_port_declarations_without_comments)


def get_all_declared_signal_names(all_signal_declarations):
    all_signal_declarations = remove_comments_and_returns(all_signal_declarations)
    all_signal_declarations = remove_functions(all_signal_declarations)
    all_signal_declarations = remove_type_declarations(all_signal_declarations)
    all_signal_declarations_separated = surround_character_by_blanks(
        ":", all_signal_declarations
    )  # only needed for VHDL
    signal_declaration_list = all_signal_declarations_separated.split(";")
    signal_list = []
    for declaration in signal_declaration_list:
        if declaration != "" and not declaration.isspace():
            signals = _get_all_signal_names(declaration)
            if signals != "":
                signal_list.extend(signals.split(","))
    return signal_list


def get_all_declared_constant_names(all_signal_declarations):
    all_signal_declarations_without_comments = remove_comments_and_returns(all_signal_declarations)
    all_signal_declarations_separated = surround_character_by_blanks(
        ":", all_signal_declarations_without_comments
    )  # only needed for VHDL
    split_char = ";"
    signal_declaration_list = all_signal_declarations_separated.split(split_char)
    constant_list = []
    for declaration in signal_declaration_list:
        if declaration != "" and not declaration.isspace():
            signals = _get_all_constant_names(declaration)
            if signals != "":
                constant_list.extend(signals.split(","))
    return constant_list


def _get_all_signal_names(declaration):
    signal_names = ""
    if " signal " in declaration and main_window.language.get() == "VHDL":
        if ":" in declaration:
            signal_names = re.sub(":.*", "", declaration)
            signal_names = re.sub(" signal ", "", signal_names)
    elif " variable " in declaration and main_window.language.get() == "VHDL":
        if ":" in declaration:
            signal_names = re.sub(":.*", "", declaration)
            signal_names = re.sub(" variable ", "", signal_names)
    elif main_window.language.get() != "VHDL":
        declaration = re.sub(" integer ", " ", declaration, flags=re.I)
        declaration = re.sub(" logic ", " ", declaration, flags=re.I)
        declaration = re.sub(" reg ", " ", declaration, flags=re.I)
        signal_names = re.sub(" \\[.*?\\] ", " ", declaration)
    signal_names_without_blanks = re.sub(" ", "", signal_names)
    return signal_names_without_blanks


def _get_all_constant_names(declaration):
    constant_names = ""
    if " constant " in declaration and main_window.language.get() == "VHDL" and ":" in declaration:
        constant_names = re.sub(":.*", "", declaration)
        constant_names = re.sub(" constant ", "", constant_names)
    if " localparam " in declaration and main_window.language.get() != "VHDL":
        declaration = re.sub(" localparam ", " ", declaration, flags=re.I)
        constant_names = re.sub(" \\[.*?\\] ", " ", declaration)
    constant_names_without_blanks = re.sub(" ", "", constant_names)
    return constant_names_without_blanks
