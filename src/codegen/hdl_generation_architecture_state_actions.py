"""
All methods needed for the state action process in VHDL or Verilog
"""

import re
import tkinter as tk

import codegen.hdl_generation_library as hdl_generation_library
import main_window
import state_action_handling
import state_actions_default
from link_dictionary import link_dict

from .exceptions import GenerationError


def create_state_action_process(file_name, file_line_number, state_tag_list_sorted) -> tuple:
    default_state_actions = _get_default_state_actions()
    state_action_list = _create_state_action_list(
        state_tag_list_sorted
    )  # Each entry is : ["state_name", "state_actions", "state_action_reference"]
    if default_state_actions == "" and _state_actions_contain_only_null_for_each_state(state_action_list):
        return "", file_line_number
    all_possible_sensitivity_entries = (
        _create_a_list_with_all_possible_sensitivity_entries()
    )  # from Interface/Ports and from Internals/Architecture Declarations
    variable_declarations = hdl_generation_library.get_text_from_text_widget(
        main_window.internals_process_combinatorial_text
    )
    if main_window.language.get() == "VHDL":
        state_action_process, file_line_number = _create_state_action_process_for_vhdl(
            file_name,
            file_line_number,
            state_action_list,
            default_state_actions,
            all_possible_sensitivity_entries,
            variable_declarations,
        )
    else:
        state_action_process, file_line_number = _create_state_action_process_for_verilog(
            file_name,
            file_line_number,
            state_action_list,
            default_state_actions,
            all_possible_sensitivity_entries,
            variable_declarations,
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
) -> tuple:
    state_action_process = "p_state_actions: process "
    state_action_process += (
        _create_sensitivity_list(state_action_list, default_state_actions, all_possible_sensitivity_entries) + "\n"
    )
    file_line_number += 1

    state_action_process += hdl_generation_library.indent_text_by_the_given_number_of_tabs(1, variable_declarations)
    number_of_lines = variable_declarations.count("\n")
    if number_of_lines != 0:
        link_dict().add(
            file_name,
            file_line_number,
            "custom_text_in_internals_tab",
            number_of_lines,
            main_window.internals_process_combinatorial_text,
        )
        file_line_number += number_of_lines
    state_action_process += "begin\n"
    file_line_number += 1

    state_action_process += hdl_generation_library.indent_text_by_the_given_number_of_tabs(1, default_state_actions)
    number_of_lines = default_state_actions.count("\n")
    if number_of_lines != 0:
        item_ids = main_window.canvas.find_withtag("state_actions_default")
        reference_to_default_state_actions_custom_text = state_actions_default.StateActionsDefault.dictionary[
            item_ids[0]
        ]
        file_line_number += 1  # default_state_actions starts always with "-- Default State Actions:"
        link_dict().add(
            file_name,
            file_line_number,
            "custom_text_in_diagram_tab",
            number_of_lines - 1,
            reference_to_default_state_actions_custom_text.text_id,
        )
        file_line_number += number_of_lines - 1

    state_action_process += "    -- State Actions:\n"
    state_action_process += "    case state is\n"
    file_line_number += 2

    for state_action in state_action_list:
        when_entry = _create_when_entry(state_action)
        state_action_process += hdl_generation_library.indent_text_by_the_given_number_of_tabs(2, when_entry)
        file_line_number += 1  # A when_entry starts always with "when ..."
        number_of_lines = when_entry.count("\n")
        link_dict().add(file_name, file_line_number, "custom_text_in_diagram_tab", number_of_lines - 1, state_action[2])
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
        link_dict().add(
            file_name,
            file_line_number,
            "custom_text_in_internals_tab",
            number_of_new_lines,
            main_window.internals_process_combinatorial_text,
        )
        file_line_number += number_of_new_lines

    state_action_process += hdl_generation_library.indent_text_by_the_given_number_of_tabs(1, default_state_actions)
    number_of_lines = default_state_actions.count("\n")
    if number_of_lines != 0:
        item_ids = main_window.canvas.find_withtag("state_actions_default")
        reference_to_default_state_actions_custom_text = state_actions_default.StateActionsDefault.dictionary[
            item_ids[0]
        ]
        file_line_number += 1  # default_state_actions starts always with "-- Default State Actions:"
        link_dict().add(
            file_name,
            file_line_number,
            "custom_text_in_diagram_tab",
            number_of_lines - 1,
            reference_to_default_state_actions_custom_text.text_id,
        )
        file_line_number += number_of_lines - 1

    state_action_process += "    // State Actions:\n"
    state_action_process += "    case (state)\n"
    file_line_number += 2

    for state_action in state_action_list:
        when_entry = _create_when_entry(state_action)
        number_of_lines = when_entry.count("\n")
        state_action_process += hdl_generation_library.indent_text_by_the_given_number_of_tabs(2, when_entry)
        if number_of_lines == 2 and when_entry.endswith("    ;\n"):  # Empty state action
            file_line_number += 2
        else:
            file_line_number += 1  # A when_entry starts always with "<State-Name: ..."
            link_dict().add(
                file_name,
                file_line_number,
                "custom_text_in_diagram_tab",
                number_of_lines - 2,  # a when entry always ends with "end"
                state_action[2],
            )
            file_line_number += number_of_lines - 1

    state_action_process += "        default:\n"
    state_action_process += "            ;\n"
    state_action_process += "    endcase\n"
    state_action_process += "end\n"
    file_line_number += 4
    return state_action_process, file_line_number


def _create_a_list_with_all_possible_sensitivity_entries() -> list:
    all_port_declarations = main_window.interface_ports_text.get("1.0", tk.END).lower()
    readable_ports_list = get_all_readable_ports(all_port_declarations, check=True)
    all_signal_declarations = main_window.internals_architecture_text.get("1.0", tk.END).lower()
    signals_list = _get_all_signals(all_signal_declarations)
    signals_list.extend(readable_ports_list)
    return signals_list


def _create_state_action_list(state_tag_list_sorted):
    state_action_list = []
    for state_tag in state_tag_list_sorted:
        state_action = "null;\n"
        state_action_reference = None
        for tag_of_state in main_window.canvas.gettags(state_tag):
            if tag_of_state.startswith("connection") and tag_of_state.endswith(
                "_end"
            ):  # This is a tag which exists only at states.
                connection_name = tag_of_state[:-4]
                state_action_id = main_window.canvas.find_withtag(connection_name + "_start")
                if state_action_id != ():
                    ref = state_action_handling.MyText.mytext_dict[state_action_id[0]]
                    state_action = ref.text_id.get("1.0", tk.END)
                    state_action_reference = ref.text_id
                    break
        state_name = main_window.canvas.itemcget(state_tag + "_name", "text")
        state_action_list.append([state_name, state_action, state_action_reference])
    return state_action_list


def _create_sensitivity_list(state_action_list, default_state_actions, all_possible_sensitivity_entries) -> str:
    sensitivity_list = "("
    default_state_actions_separated = hdl_generation_library.convert_hdl_lines_into_a_searchable_string(
        default_state_actions
    )
    default_state_actions_separated = _remove_left_hand_sides(default_state_actions_separated)
    for entry in all_possible_sensitivity_entries:
        if " " + entry + " " in default_state_actions_separated:
            sensitivity_list += entry + ", "
    for list_entry in state_action_list:
        state_action_separated = hdl_generation_library.convert_hdl_lines_into_a_searchable_string(list_entry[1])
        state_action_separated = _remove_left_hand_sides(state_action_separated)
        for entry in all_possible_sensitivity_entries:
            if " " + entry + " " in state_action_separated and entry + ", " not in sensitivity_list:
                sensitivity_list += entry + ", "
    sensitivity_list += "state)"
    return sensitivity_list


def _remove_left_hand_sides(state_action):
    # Insert ";" for the search pattern later:
    state_action = ";" + state_action
    state_action = re.sub(" begin ", " ; ", state_action, flags=re.I)
    state_action = re.sub(" then ", " ; ", state_action, flags=re.I)
    state_action = re.sub(" else ", " ; ", state_action, flags=re.I)
    # Replace the left sides:
    state_action = re.sub(r";\s*[^\s]+\s*<=", "; <=", state_action)
    return state_action


def _get_default_state_actions() -> str:
    item_ids = main_window.canvas.find_withtag("state_actions_default")
    if item_ids == ():
        return ""
    else:
        ref = state_actions_default.StateActionsDefault.dictionary[item_ids[0]]
        comment = "--" if main_window.language.get() == "VHDL" else "//"
        return comment + " Default State Actions:\n" + ref.text_id.get("1.0", tk.END)


def _create_when_entry(state_action):
    if main_window.language.get() == "VHDL":
        when_entry = "when " + state_action[0] + "=>\n"
        when_entry += hdl_generation_library.indent_text_by_the_given_number_of_tabs(1, state_action[1])
    else:
        if state_action[1].startswith("null;"):
            when_entry = state_action[0] + ":\n"
            when_entry += "    ;\n"
        else:
            when_entry = state_action[0] + ": begin\n"
            when_entry += hdl_generation_library.indent_text_by_the_given_number_of_tabs(1, state_action[1])
            when_entry += "end\n"
    return when_entry


def get_all_readable_ports(all_port_declarations, check) -> list:
    port_declaration_list = _create_list_of_declarations(all_port_declarations)
    readable_port_list = []
    for declaration in port_declaration_list:
        if declaration != "" and not declaration.isspace():
            inputs = _get_all_readable_port_names(
                declaration, check
            )  # One declaration can contain a comma separated list of names!
            if inputs != "":
                readable_port_list.extend(inputs.split(","))
    return readable_port_list


def get_all_writable_ports(all_port_declarations) -> list:
    port_declaration_list = _create_list_of_declarations(all_port_declarations)
    writeable_port_list = []
    for declaration in port_declaration_list:
        if declaration != "" and not declaration.isspace():
            outputs = _get_all_writable_port_names(declaration)
            if outputs != "":
                writeable_port_list.extend(outputs.split(","))
    return writeable_port_list


def _create_list_of_declarations(all_declarations):
    all_declarations_without_comments = hdl_generation_library.remove_comments_and_returns(all_declarations)
    all_declarations_separated = hdl_generation_library.surround_character_by_blanks(
        ":", all_declarations_without_comments
    )  # only needed for VHDL
    split_char = ";" if main_window.language.get() == "VHDL" else ","
    return all_declarations_separated.split(split_char)


def get_all_port_types(all_port_declarations) -> list:
    port_declaration_list = _create_list_of_declarations(all_port_declarations)
    port_types_list = []
    for declaration in port_declaration_list:
        if (
            declaration != ""
            and not declaration.isspace()
            and (" in " in declaration or " out " in declaration or " inout " in declaration)
        ):
            port_type = re.sub(".* in |.* out |.* inout ", "", declaration, flags=re.I | re.DOTALL)
            port_type = re.sub("\\(.*", "", port_type, flags=re.I | re.DOTALL)
            port_type = re.sub(";", "", port_type)
            if port_type != "" and not port_type.isspace():
                port_type = re.sub("\\s", "", port_type)
                port_types_list.append(port_type)
    return port_types_list


def get_all_generic_names(all_generic_declarations) -> list:
    generic_declaration_list = _create_list_of_declarations(all_generic_declarations)
    generic_name_list = []
    for declaration in generic_declaration_list:
        if declaration != "" and not declaration.isspace():
            if main_window.language.get() == "VHDL":
                generic_name = re.sub(" : .*", "", declaration, flags=re.I | re.DOTALL)
                generic_name = re.sub(r"(^|\s+)constant ", "", generic_name, flags=re.I | re.DOTALL)
                generic_name = re.sub("\\s", "", generic_name)
            else:  # Verilog
                generic_name = re.sub("=.*", "", declaration, flags=re.I | re.DOTALL)
                generic_name = re.sub("\\s", "", generic_name)
            generic_name_list.append(generic_name)
    return generic_name_list


def _get_all_readable_port_names(declaration, check) -> str:
    port_names = ""
    if " in " in declaration and main_window.language.get() == "VHDL":
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
    elif " input " in declaration and main_window.language.get() != "VHDL":
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
    if " out " in declaration and main_window.language.get() == "VHDL":
        if ":" in declaration:
            port_names = re.sub(":.*", "", declaration)
    elif " output " in declaration and main_window.language.get() != "VHDL":
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
    if main_window.language.get() == "VHDL":
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
                else:
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
                else:
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
    signal_names = re.sub(":.*", "", declaration)
    signal_names_alone = re.sub(" signal ", "", signal_names, flags=re.I)
    signal_names_without_blanks = re.sub(" ", "", signal_names_alone)
    return signal_names_without_blanks
