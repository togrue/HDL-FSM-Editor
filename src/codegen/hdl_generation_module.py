"""
module for generating the logic inside a Verilog design.
"""

import math
import re

import codegen.hdl_generation_architecture_state_actions as hdl_generation_architecture_state_actions
import codegen.hdl_generation_architecture_state_sequence as hdl_generation_architecture_state_sequence
import codegen.hdl_generation_library as hdl_generation_library
import main_window
from link_dictionary import link_dict

from .exceptions import GenerationError


def create_module_logic(file_name: str, file_line_number: int, state_tag_list_sorted: list[str]) -> str:
    architecture = ""
    state_signal_type_definition = _create_signal_declaration_for_the_state_variable(state_tag_list_sorted)
    architecture += hdl_generation_library.indent_text_by_the_given_number_of_tabs(1, state_signal_type_definition)
    file_line_number += state_signal_type_definition.count("\n")

    signal_declarations = hdl_generation_library.get_text_from_text_widget(main_window.internals_architecture_text)
    architecture += hdl_generation_library.indent_text_by_the_given_number_of_tabs(1, signal_declarations)
    number_of_new_lines = signal_declarations.count("\n")
    link_dict().add(
        file_name,
        file_line_number,
        "custom_text_in_internals_tab",
        number_of_new_lines,
        main_window.internals_architecture_text,
    )
    file_line_number += number_of_new_lines

    [reset_condition, reset_action, reference_to_reset_condition_custom_text, reference_to_reset_action_custom_text] = (
        hdl_generation_library.create_reset_condition_and_reset_action()
    )
    if reset_condition is None:
        raise GenerationError("Error", "No reset condition found. A reset condition must be set!")

    architecture += (
        "    always @(posedge "
        + main_window.clock_signal_name.get()
        + " or "
        + _get_reset_edge(reset_condition)
        + " "
        + main_window.reset_signal_name.get()
        + ") begin: p_states\n"
    )
    link_dict().add(file_name, file_line_number, "Control-Tab", 1, "reset_and_clock_signal_name")
    file_line_number += 1

    variable_declarations = hdl_generation_library.get_text_from_text_widget(main_window.internals_process_clocked_text)
    if variable_declarations != "":
        architecture += hdl_generation_library.indent_text_by_the_given_number_of_tabs(2, variable_declarations)
        number_of_new_lines = variable_declarations.count("\n")
        link_dict().add(
            file_name,
            file_line_number,
            "custom_text_in_internals_tab",
            number_of_new_lines,
            main_window.internals_process_clocked_text,
        )
        file_line_number += number_of_new_lines

    if reset_condition.count("\n") == 0:
        architecture += "        if (" + reset_condition + ") begin\n"
    else:
        reset_condition_list = reset_condition.split("\n")
        for index, line in enumerate(reset_condition_list):
            if index == 0:
                architecture += "        if (" + line + "\n"
            else:
                architecture += "            " + line + "\n"
        architecture += "        ) begin\n"
    number_of_new_lines = reset_condition.count("\n") + 1  # No return after the last line of the condition
    link_dict().add(
        file_name,
        file_line_number,
        "custom_text_in_diagram_tab",
        number_of_new_lines,
        reference_to_reset_condition_custom_text,
    )
    file_line_number += number_of_new_lines

    architecture += hdl_generation_library.indent_text_by_the_given_number_of_tabs(3, reset_action)
    file_line_number += 1  # There is always a "state <=  ..." assignment which must be skipped
    number_of_new_lines = reset_action.count("\n") - 1
    link_dict().add(
        file_name,
        file_line_number,
        "custom_text_in_diagram_tab",
        number_of_new_lines,
        reference_to_reset_action_custom_text,
    )
    file_line_number += number_of_new_lines

    architecture += "        end\n"
    architecture += "        else begin\n"
    file_line_number += 2

    _res = hdl_generation_library.create_global_actions_before()
    if _res:
        global_actions_before_reference, global_actions_before = _res
        global_actions_before = "// Global Actions before:\n" + global_actions_before
        file_line_number += 1
        architecture += hdl_generation_library.indent_text_by_the_given_number_of_tabs(3, global_actions_before)
        number_of_new_lines = global_actions_before.count("\n") - 1
        link_dict().add(
            file_name,
            file_line_number,
            "custom_text_in_diagram_tab",
            number_of_new_lines,
            global_actions_before_reference,
        )
        file_line_number += number_of_new_lines

    architecture += "            // State Machine:\n"
    architecture += "            case (state)\n"
    file_line_number += 2

    transition_specifications = hdl_generation_library.extract_transition_specifications_from_the_graph(
        state_tag_list_sorted
    )
    state_sequence, file_line_number = hdl_generation_architecture_state_sequence.create_verilog_for_the_state_sequence(
        transition_specifications, file_name, file_line_number
    )
    architecture += hdl_generation_library.indent_text_by_the_given_number_of_tabs(4, state_sequence)
    architecture += "                default:\n"
    architecture += "                    ;\n"
    architecture += "            endcase\n"
    file_line_number += 3

    _res = hdl_generation_library.create_global_actions_after()
    if _res:
        global_actions_after_reference, global_actions_after = _res
        global_actions_after = "// Global Actions after:\n" + global_actions_after
        file_line_number += 1
        architecture += hdl_generation_library.indent_text_by_the_given_number_of_tabs(3, global_actions_after)
        number_of_new_lines = global_actions_after.count("\n") - 1
        link_dict().add(
            file_name,
            file_line_number,
            "custom_text_in_diagram_tab",
            number_of_new_lines,
            global_actions_after_reference,
        )
        file_line_number += number_of_new_lines

    architecture += "        end\n"
    architecture += "    end\n"
    file_line_number += 2

    state_actions_process, file_line_number = hdl_generation_architecture_state_actions.create_state_action_process(
        file_name, file_line_number, state_tag_list_sorted
    )
    architecture += hdl_generation_library.indent_text_by_the_given_number_of_tabs(1, state_actions_process)

    _res = hdl_generation_library.create_concurrent_actions()
    if _res:
        concurrent_actions_reference, concurrent_actions = _res
        concurrent_actions = "// Global Actions combinatorial:\n" + concurrent_actions
        file_line_number += 1
        architecture += hdl_generation_library.indent_text_by_the_given_number_of_tabs(1, concurrent_actions)
        number_of_new_lines = concurrent_actions.count("\n") - 1
        link_dict().add(
            file_name,
            file_line_number,
            "custom_text_in_diagram_tab",
            number_of_new_lines,
            concurrent_actions_reference,
        )
        file_line_number += number_of_new_lines

    architecture += "endmodule\n"
    return architecture


def _create_signal_declaration_for_the_state_variable(state_tag_list_sorted) -> str:
    list_of_all_state_names = [
        main_window.canvas.itemcget(state_tag + "_name", "text") for state_tag in state_tag_list_sorted
    ]
    number_of_states = len(list_of_all_state_names)
    if main_window.language.get() == "Verilog":
        bit_width_number_of_states = math.ceil(math.log(number_of_states, 2))
        high_index = bit_width_number_of_states - 1
        signal_declaration = "reg [" + str(high_index) + ":0] state;\n"
        signal_declaration += "localparam\n"
        state_name_declaration_list = []
        for index, state_name in enumerate(list_of_all_state_names):
            state_name_declaration_list.append("    " + state_name + " = " + str(index) + ",\n")
        state_name_declaration_list = _indent_identically("=", state_name_declaration_list)
        state_name_declarations = "".join(state_name_declaration_list)
        signal_declaration += state_name_declarations[:-2] + ";\n"  # Substitute the last "," by a ";".
    else:  # SystemVerilog
        name_list = ""
        for name in list_of_all_state_names:
            name_list += name + ", "
        signal_declaration = "typedef enum {" + name_list[:-2] + "} t_state;\nt_state state;\n"
    return signal_declaration


def _indent_identically(character, actual_list) -> list:
    actual_list = [
        re.sub("[ ]*" + character, character, decl, count=1) for decl in actual_list
    ]  # Blanks for the character will be adapted und must first be removed here.
    max_index = 0
    new_list = []
    for port_declaration in actual_list:
        index = port_declaration.find(character)
        if index > max_index:
            max_index = index
    for port_declaration in actual_list:
        index = port_declaration.find(character)
        fill = " " * (max_index - index + 1) + character
        new_list.append(re.sub(character, fill, port_declaration, count=1))
    return new_list


def _get_reset_edge(reset_condition) -> str:
    reset_condition_mod = hdl_generation_library.remove_comments_and_returns(reset_condition)
    reset_condition_mod = re.sub("\\s", "", reset_condition_mod)  # remove blanks
    if reset_condition_mod.endswith("1'b0"):
        return "negedge"
    elif reset_condition_mod.endswith("1'b1"):
        return "posedge"
    else:
        raise GenerationError(
            "Error", "The reset polarity could not be determined from the reset condition: " + reset_condition_mod
        )
