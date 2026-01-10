"""
Methods needed for highlighting signals, which are not read, not written, not defined
"""

import constants
import custom_text
import global_actions_combinatorial
from project_manager import project_manager

recreate_after_id = None
update_highlight_tags_id = None

highlight_pattern_dict: dict[str, list[str]] = constants.VHDL_HIGHLIGHT_PATTERN_DICT


def recreate_keyword_list_of_unused_signals() -> None:
    global recreate_after_id
    if recreate_after_id is not None:
        project_manager.root.after_cancel(recreate_after_id)
    recreate_after_id = project_manager.root.after(300, _recreate_keyword_list_of_unused_signals_after_idle)


def _recreate_keyword_list_of_unused_signals_after_idle() -> None:
    global highlight_pattern_dict
    highlight_pattern_dict["not_read"].clear()
    highlight_pattern_dict["not_written"].clear()

    variables_to_write = _get_all_read_variables()
    variables_to_read = _get_all_written_variables()
    variables_to_write = _store_not_read_input_ports(variables_to_write)
    variables_to_read, variables_to_write = _store_not_written_output_ports(variables_to_read, variables_to_write)
    variables_to_read, variables_to_write = _store_not_written_not_read_signals(variables_to_read, variables_to_write)
    variables_to_read, variables_to_write = _detect_not_written_constants(variables_to_read, variables_to_write)
    variables_to_write = _remove_port_types(variables_to_write)
    variables_to_read, variables_to_write = _remove_generics(variables_to_read, variables_to_write)
    highlight_pattern_dict["not_written"] += variables_to_write
    highlight_pattern_dict["not_read"] += variables_to_read


def _get_all_read_variables():
    variables_to_write = []
    for _, read_variables_of_window in custom_text.CustomText.read_variables_of_all_windows.items():
        variables_to_write += read_variables_of_window
    variables_to_write = list(set(variables_to_write))  # remove duplicates
    return variables_to_write


def _get_all_written_variables():
    variables_to_read = []
    for _, written_variables_of_window in custom_text.CustomText.written_variables_of_all_windows.items():
        variables_to_read += written_variables_of_window
    variables_to_read = list(set(variables_to_read))  # remove duplicates
    return variables_to_read


def _store_not_read_input_ports(variables_to_write):
    for input_port in project_manager.interface_ports_text.readable_ports_list:
        if input_port in variables_to_write:
            # Input is read but must not be written:
            variables_to_write.remove(input_port)
        else:
            if input_port != project_manager.clock_signal_name.get():
                highlight_pattern_dict["not_read"].append(input_port)
    return variables_to_write


def _store_not_written_output_ports(variables_to_read, variables_to_write):
    for output in project_manager.interface_ports_text.writable_ports_list:
        if output in variables_to_read:
            # Outputs is written but must not be read:
            variables_to_read.remove(output)
        else:
            highlight_pattern_dict["not_written"].append(output)
        if project_manager.language.get() != "VHDL" and output in variables_to_write:  # A Verilog output is read.
            # Writing of outputs is checked by the variables_to_read list:
            variables_to_write.remove(output)
    return variables_to_read, variables_to_write


def _store_not_written_not_read_signals(variables_to_read, variables_to_write):
    # Check if each signal or variable is written and is read:
    process_variable_list = []
    for _, ref in global_actions_combinatorial.GlobalActionsCombinatorial.dictionary.items():
        process_variable_list += ref.text_id.signals_list
    for signal in (
        project_manager.internals_architecture_text.signals_list
        + project_manager.internals_process_combinatorial_text.signals_list
        + project_manager.internals_process_clocked_text.signals_list
        + process_variable_list
    ):
        if signal in variables_to_read and signal in variables_to_write:
            variables_to_read.remove(signal)
            variables_to_write.remove(signal)
        elif signal in variables_to_read:
            highlight_pattern_dict["not_read"].append(signal)
        else:
            highlight_pattern_dict["not_written"].append(signal)
    return variables_to_read, variables_to_write


def _detect_not_written_constants(variables_to_read, variables_to_write):
    for constant in (
        project_manager.internals_architecture_text.constants_list
        + project_manager.internals_process_combinatorial_text.constants_list
        + project_manager.internals_process_clocked_text.constants_list
    ):
        # variables_to_read = [value for value in variables_to_read if value != constant]  # remove constant from list
        if constant in variables_to_read:
            variables_to_read.remove(constant)
        if constant not in variables_to_write:  # Then the constant is not read.
            highlight_pattern_dict["not_read"].append(constant)
        else:
            variables_to_write.remove(constant)
    return variables_to_read, variables_to_write


def _remove_port_types(variables_to_write):
    for port_type in project_manager.interface_ports_text.port_types_list:
        if port_type in variables_to_write:
            variables_to_write.remove(port_type)
    return variables_to_write


def _remove_generics(variables_to_read, variables_to_write):
    for generic in project_manager.interface_generics_text.generics_list:
        if generic in variables_to_read:
            variables_to_read.remove(generic)
        if generic in variables_to_write:
            variables_to_write.remove(generic)
    return variables_to_read, variables_to_write


def update_highlight_tags_in_all_windows_for_not_read_not_written_and_comment() -> None:
    global update_highlight_tags_id
    if update_highlight_tags_id is not None:
        project_manager.root.after_cancel(update_highlight_tags_id)
    update_highlight_tags_id = project_manager.root.after(
        300, _update_highlight_tags_in_all_windows_for_not_read_not_written_and_comment_after_idle
    )


def _update_highlight_tags_in_all_windows_for_not_read_not_written_and_comment_after_idle() -> None:
    # Comment must be the last, because in the range of a comment all other tags are deleted:
    for text_ref in custom_text.CustomText.read_variables_of_all_windows:
        text_ref.update_highlight_tags(project_manager.fontsize, ["not_read", "not_written", "comment"])
    text_refs_fixed = [
        project_manager.interface_generics_text,
        project_manager.interface_package_text,
        project_manager.interface_ports_text,
        project_manager.internals_architecture_text,
        project_manager.internals_process_clocked_text,
        project_manager.internals_process_combinatorial_text,
        project_manager.internals_package_text,
    ]
    for text_ref in text_refs_fixed:
        text_ref.update_highlight_tags(10, ["not_read", "not_written", "comment"])
