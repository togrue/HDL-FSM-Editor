"""
All methods needed for the state action process in VHDL or Verilog
"""

import re

from codegen import hdl_generation_library, hdl_text_utils
from project_manager import project_manager

from .exceptions import GenerationError


def create_state_action_process(file_name, file_line_number, state_tag_list_sorted, design_data) -> tuple:
    """Returns the state action process as string and the updated file_line_number."""
    default_state_actions = _get_default_state_actions(design_data)
    state_action_list = design_data.state_action_list or []
    if default_state_actions == "" and _state_actions_contain_only_null_for_each_state(state_action_list):
        return "", file_line_number
    # Get from Interface/Ports and from Internals/Architecture Declarations:
    all_possible_sensitivity_entries = _create_a_list_with_all_possible_sensitivity_entries(design_data)
    variable_declarations = design_data.internals_process_combinatorial_text[0]
    if project_manager.language.get() == "VHDL":
        state_action_process, file_line_number = _create_state_action_process_for_vhdl(
            file_name,
            file_line_number,
            state_action_list,
            default_state_actions,
            all_possible_sensitivity_entries,
            variable_declarations,
            design_data,
        )
    else:
        state_action_process, file_line_number = _create_state_action_process_for_verilog(
            file_name,
            file_line_number,
            state_action_list,
            default_state_actions,
            all_possible_sensitivity_entries,
            variable_declarations,
            design_data,
        )
    return state_action_process, file_line_number


def _state_actions_contain_only_null_for_each_state(state_action_list) -> bool:
    return all(entry[1] == "null;\n" for entry in state_action_list)


def _create_state_action_process_for_vhdl(
    file_name,
    file_line_number,
    state_action_list,
    default_state_actions,
    all_possible_sensitivity_entries,
    variable_declarations,
    design_data,
) -> tuple:
    state_action_process = "p_state_actions: process "
    state_action_process += (
        _create_sensitivity_list(state_action_list, default_state_actions, all_possible_sensitivity_entries) + "\n"
    )
    file_line_number += 1

    state_action_process += hdl_generation_library.indent_text_by_the_given_number_of_tabs(1, variable_declarations)
    number_of_lines = variable_declarations.count("\n")
    comb_ref = design_data.internals_process_combinatorial_text[1]
    if number_of_lines != 0 and comb_ref is not None:
        project_manager.link_dict_ref.add(
            file_name,
            file_line_number,
            "custom_text_in_internals_tab",
            number_of_lines,
            comb_ref,
        )
        file_line_number += number_of_lines
    state_action_process += "begin\n"
    file_line_number += 1

    state_action_process += hdl_generation_library.indent_text_by_the_given_number_of_tabs(1, default_state_actions)
    number_of_lines = default_state_actions.count("\n")
    if number_of_lines != 0:
        default_ref = design_data.state_actions_default[1]
        file_line_number += 1  # default_state_actions starts always with "-- Default State Actions:"
        if default_ref is not None:
            project_manager.link_dict_ref.add(
                file_name,
                file_line_number,
                "custom_text_in_diagram_tab",
                number_of_lines - 1,
                default_ref,
            )
        file_line_number += number_of_lines - 1

    state_action_process += "    -- State Actions:\n"
    state_action_process += "    case state is\n"
    file_line_number += 2

    for state_action_entry in state_action_list:
        when_entry = _create_when_entry(state_action_entry)
        state_action_process += hdl_generation_library.indent_text_by_the_given_number_of_tabs(2, when_entry)
        file_line_number += 1  # A when_entry starts always with "when ..."
        number_of_lines = when_entry.count("\n")
        project_manager.link_dict_ref.add(
            file_name, file_line_number, "custom_text_in_diagram_tab", number_of_lines - 1, state_action_entry[2]
        )
        file_line_number += number_of_lines - 1

    state_action_process += "    end case;\n"
    state_action_process += "end process;\n"
    file_line_number += 2
    return state_action_process, file_line_number


def _create_state_action_process_for_verilog(
    file_name,
    file_line_number,
    state_action_list,
    default_state_actions,
    all_possible_sensitivity_entries,
    variable_declarations,
    design_data,
) -> tuple:
    state_action_process = "always @"
    state_action_process += _create_sensitivity_list(
        state_action_list, default_state_actions, all_possible_sensitivity_entries
    )
    state_action_process += " begin: p_state_actions\n"
    file_line_number += 1

    if variable_declarations != "":
        state_action_process += hdl_generation_library.indent_text_by_the_given_number_of_tabs(1, variable_declarations)
        number_of_new_lines = variable_declarations.count("\n")
        comb_ref = design_data.internals_process_combinatorial_text[1]
        if comb_ref is not None:
            project_manager.link_dict_ref.add(
                file_name,
                file_line_number,
                "custom_text_in_internals_tab",
                number_of_new_lines,
                comb_ref,
            )
        file_line_number += number_of_new_lines

    state_action_process += hdl_generation_library.indent_text_by_the_given_number_of_tabs(1, default_state_actions)
    number_of_lines = default_state_actions.count("\n")
    if number_of_lines != 0:
        default_ref = design_data.state_actions_default[1]
        file_line_number += 1  # default_state_actions starts always with "-- Default State Actions:"
        if default_ref is not None:
            project_manager.link_dict_ref.add(
                file_name,
                file_line_number,
                "custom_text_in_diagram_tab",
                number_of_lines - 1,
                default_ref,
            )
        file_line_number += number_of_lines - 1

    state_action_process += "    // State Actions:\n"
    state_action_process += "    case (state)\n"
    file_line_number += 2

    for state_action_entry in state_action_list:
        when_entry = _create_when_entry(state_action_entry)
        number_of_lines = when_entry.count("\n")
        state_action_process += hdl_generation_library.indent_text_by_the_given_number_of_tabs(2, when_entry)
        if number_of_lines == 2 and when_entry.endswith("    ;\n"):  # Empty state action
            file_line_number += 2
        else:
            file_line_number += 1  # A when_entry starts always with "<State-Name: ..."
            project_manager.link_dict_ref.add(
                file_name,
                file_line_number,
                "custom_text_in_diagram_tab",
                number_of_lines - 2,  # a when entry always ends with "end"
                state_action_entry[2],
            )
            file_line_number += number_of_lines - 1

    state_action_process += "        default:\n"
    state_action_process += "            ;\n"
    state_action_process += "    endcase\n"
    state_action_process += "end\n"
    file_line_number += 4
    return state_action_process, file_line_number


def _create_a_list_with_all_possible_sensitivity_entries(design_data) -> list:
    all_port_declarations = design_data.interface_ports_text[0].lower()
    readable_ports_list = get_all_readable_ports(all_port_declarations, check=True)
    all_signal_declarations = design_data.internals_architecture_text[0].lower()
    signals_list = _get_all_signals(all_signal_declarations)
    signals_list.extend(readable_ports_list)
    return signals_list


def _create_sensitivity_list(state_action_list, default_state_actions, all_possible_sensitivity_entries) -> str:
    sensitivity_list = "("
    default_state_actions_separated = hdl_generation_library.convert_hdl_lines_into_a_searchable_string(
        default_state_actions
    )
    default_state_actions_separated = _remove_left_hand_sides(default_state_actions_separated)
    default_state_actions_separated = _remove_record_element_names(default_state_actions_separated)
    for entry in all_possible_sensitivity_entries:
        if " " + entry + " " in default_state_actions_separated:
            sensitivity_list += entry + ", "
    for list_entry in state_action_list:
        state_action_separated = hdl_generation_library.convert_hdl_lines_into_a_searchable_string(list_entry[1])
        state_action_separated = _remove_left_hand_sides(state_action_separated)
        state_action_separated = _remove_record_element_names(state_action_separated)
        for entry in all_possible_sensitivity_entries:
            if " " + entry + " " in state_action_separated and entry + ", " not in sensitivity_list:
                sensitivity_list += entry + ", "
    sensitivity_list += "state)"
    return sensitivity_list


def _remove_left_hand_sides(state_action_text) -> str:
    # Insert ";" for the search pattern later:
    state_action_text = ";" + state_action_text
    state_action_text = re.sub(" begin ", " ; ", state_action_text, flags=re.I)
    state_action_text = re.sub(" then ", " ; ", state_action_text, flags=re.I)
    state_action_text = re.sub(" else ", " ; ", state_action_text, flags=re.I)
    # Replace the left sides:
    state_action_text = re.sub(r";\s*[^\s]+\s*<=", "; <=", state_action_text)
    return state_action_text


def _remove_record_element_names(state_action_text) -> str:
    state_action_text = re.sub(r"\..*?\s", " ", state_action_text)
    return state_action_text


def _get_default_state_actions(design_data) -> str:
    return design_data.state_actions_default[0]


def _create_when_entry(state_action_entry) -> str:
    if project_manager.language.get() == "VHDL":
        when_entry = "when " + state_action_entry[0] + "=>\n"
        when_entry += hdl_generation_library.indent_text_by_the_given_number_of_tabs(1, state_action_entry[1])
    else:
        if state_action_entry[1].startswith("null;"):
            when_entry = state_action_entry[0] + ":\n"
            when_entry += "    ;\n"
        else:
            when_entry = state_action_entry[0] + ": begin\n"
            when_entry += hdl_generation_library.indent_text_by_the_given_number_of_tabs(1, state_action_entry[1])
            when_entry += "end\n"
    return when_entry


def get_all_readable_ports(all_port_declarations, check) -> list:
    """Returns a list with the names of all readable ports.
    If check is True, an error is raised if an illegal port declaration is found.
    """
    return hdl_text_utils.get_all_readable_ports(all_port_declarations, check)


def get_all_writable_ports(all_port_declarations) -> list:
    """Returns a list with the names of all writable ports."""
    return hdl_text_utils.get_all_writable_ports(all_port_declarations)


def _create_list_of_declarations(all_declarations):
    all_declarations_without_comments = hdl_generation_library.remove_comments_and_returns(all_declarations)
    all_declarations_separated = hdl_generation_library.surround_character_by_blanks(
        ":", all_declarations_without_comments
    )  # only needed for VHDL
    split_char = ";" if project_manager.language.get() == "VHDL" else ","
    return all_declarations_separated.split(split_char)


def get_all_port_types(all_port_declarations) -> list:
    """Returns a list with the type-names of all ports."""
    return hdl_text_utils.get_all_port_types(all_port_declarations)


def get_all_generic_names(all_generic_declarations) -> list:
    """Returns a list with the names of all generics."""
    return hdl_text_utils.get_all_generic_names(all_generic_declarations)


def _get_all_readable_port_names(declaration, check) -> str:
    port_names = ""
    if " in " in declaration and project_manager.language.get() == "VHDL":
        if ":" not in declaration:
            if check is True:
                raise GenerationError(
                    "Error",
                    [
                        f'There is an illegal port declaration, which will be ignored: "{declaration}"',
                        "VHDL may be corrupted.",
                    ],
                )
        else:
            port_names = re.sub(":.*", "", declaration)
    elif " input " in declaration and project_manager.language.get() != "VHDL":
        declaration = re.sub(" input ", " ", declaration, flags=re.I)
        declaration = re.sub(" reg ", " ", declaration, flags=re.I)
        declaration = re.sub(" logic ", " ", declaration, flags=re.I)
        port_names = re.sub(" \\[.*?\\] ", " ", declaration)
    else:
        return ""
    port_names_without_blanks = re.sub(" ", "", port_names)
    return port_names_without_blanks


def _get_all_writable_port_names(declaration) -> str:
    port_names = ""
    if " out " in declaration and project_manager.language.get() == "VHDL":
        if ":" in declaration:
            port_names = re.sub(":.*", "", declaration)
    elif " output " in declaration and project_manager.language.get() != "VHDL":
        declaration = re.sub(" output ", " ", declaration, flags=re.I)
        declaration = re.sub(" reg ", " ", declaration, flags=re.I)
        declaration = re.sub(" logic ", " ", declaration, flags=re.I)
        declaration = re.sub(" unsigned ", " ", declaration, flags=re.I)
        declaration = re.sub(" signed ", " ", declaration, flags=re.I)
        port_names = re.sub(" \\[.*?\\] ", " ", declaration)
    else:
        return ""
    port_names_without_blanks = re.sub(" ", "", port_names)
    return port_names_without_blanks


def _get_all_signals(all_signal_declarations) -> list:
    all_signal_declarations_without_comments = hdl_generation_library.remove_comments_and_returns(
        all_signal_declarations
    )
    all_signal_declarations_without_comments = hdl_generation_library.remove_functions(
        all_signal_declarations_without_comments
    )
    all_signal_declarations_without_comments = hdl_generation_library.remove_type_declarations(
        all_signal_declarations_without_comments
    )
    all_signal_declarations_separated = hdl_generation_library.surround_character_by_blanks(
        ":", all_signal_declarations_without_comments
    )
    signal_declaration_list = all_signal_declarations_separated.split(";")
    signal_declaration_list_extended = _add_blank_at_the_beginning_of_each_line(
        signal_declaration_list
    )  # needed for search of " signal "
    signals_list = []
    if project_manager.language.get() == "VHDL":
        for declaration in signal_declaration_list_extended:
            if declaration != "" and not declaration.isspace():
                if " signal " not in declaration and " constant " not in declaration:
                    raise GenerationError(
                        "Error",
                        [
                            f'There is an illegal signal declaration, which will be ignored: "{declaration}"',
                            "VHDL may be corrupted.",
                        ],
                    )
                signals = _get_the_signal_names(declaration)
                if signals != "":
                    signals_list.extend(signals.split(","))
    else:
        for declaration in signal_declaration_list_extended:
            if declaration != "" and not declaration.isspace():
                if (
                    " integer " not in declaration
                    and " reg " not in declaration
                    and " wire " not in declaration
                    and " logic " not in declaration
                ):
                    raise GenerationError(
                        "Error",
                        [
                            f'There is an illegal signal declaration, which will be ignored: "{declaration}"',
                            "Verilog may be corrupted.",
                        ],
                    )
                declaration = re.sub(" reg ", " ", declaration, flags=re.I)
                declaration = re.sub(" wire ", " ", declaration, flags=re.I)
                declaration = re.sub(" logic ", " ", declaration, flags=re.I)
                declaration = re.sub(" \\[.*?\\]", " ", declaration, flags=re.I)
                if declaration != "":
                    signals_list.extend(declaration.split(","))
    return signals_list


def _add_blank_at_the_beginning_of_each_line(signal_declaration_list) -> list:
    signal_declaration_list_extended = []
    for d in signal_declaration_list:
        signal_declaration_list_extended.append(re.sub("^", " ", d))
    return signal_declaration_list_extended


def _get_the_signal_names(declaration):
    if " constant " in declaration:
        return ""
    signal_names = re.sub(":.*", "", declaration)
    signal_names_alone = re.sub(" signal ", "", signal_names, flags=re.I)
    signal_names_without_blanks = re.sub(" ", "", signal_names_alone)
    return signal_names_without_blanks
