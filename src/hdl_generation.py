"""
Methods needed for HDL generation
"""

import os
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox

import file_handling
import hdl_generation_architecture
import hdl_generation_library
import hdl_generation_module
import link_dictionary
import list_separation_check
import main_window
import tag_plausibility

last_line_number_of_file1 = 0


def run_hdl_generation(write_to_file):
    if design_is_not_ready_for_hdl_generation():
        return
    if not tag_plausibility.TagPlausibility().get_tag_status_is_okay():
        messagebox.showerror("Error", "The database is corrupt.\nHDL is not generated.\nSee details at STDOUT.")
        return
    if main_window.root.title().endswith("*"):
        file_handling.save()
    if main_window.language.get() == "VHDL":
        header = "-- Created by HDL-FSM-Editor at " + datetime.today().ctime() + "\n"
    else:
        header = "// Created by HDL-FSM-Editor at " + datetime.today().ctime() + "\n"
    create_hdl(header, write_to_file)


def design_is_not_ready_for_hdl_generation():
    name = main_window.module_name.get()
    if name.isspace() or name == "":
        messagebox.showerror(
            "Error in HDL-FSM-Editor", "No module-name is specified,\nso no HDL-generation is possible."
        )
        return True
    path_string = main_window.generate_path_value.get()
    if path_string.isspace() or path_string == "":
        messagebox.showerror(
            "Error in HDL-FSM-Editor",
            "No path for the generation of the HDL-files is specified,\nso no HDL-generation is possible.",
        )
        return True
    else:
        path = Path(path_string)
        if not path.exists():
            messagebox.showerror(
                "Error in HDL-FSM-Editor",
                "HDL-generation for module "
                + name
                + " is not possible, because the specified path\n"
                + path_string
                + '\nfor the generation of the HDL-files does not exist.\nSee "Path for generated HDL" in the Control-Tab.',
            )
            return True
    reset = main_window.reset_signal_name.get()
    if reset.isspace() or reset == "":
        messagebox.showerror(
            "Error in HDL-FSM-Editor", "No reset signal name is specified,\nso no HDL-generation is possible."
        )
        return True
    clock = main_window.clock_signal_name.get()
    if clock.isspace() or clock == "":
        messagebox.showerror(
            "Error in HDL-FSM-Editor", "No clock signal name is specified,\nso no HDL-generation is possible."
        )
        return True
    return False


def create_hdl(header, write_to_file):
    file_name, file_name_architecture = get_file_names()
    link_dictionary.LinkDictionary.link_dict_reference.clear_link_dict(file_name)
    link_dictionary.LinkDictionary.link_dict_reference.clear_link_dict(file_name_architecture)
    file_line_number = 3  # Line 1 = Filename, Line 2 = Header
    if main_window.language.get() == "VHDL":
        entity, file_line_number = create_entity(file_name, file_line_number)
        if file_name_architecture == "":  # All VHDL is written in 1 file.
            file_to_use = file_name
            file_line_number_to_use = file_line_number
        else:
            file_to_use = file_name_architecture
            file_line_number_to_use = 3
        architecture = hdl_generation_architecture.create_architecture(file_to_use, file_line_number_to_use)
    else:
        entity, file_line_number = create_module_ports(file_name, file_line_number)
        architecture = hdl_generation_module.create_module_logic(file_name, file_line_number)
    if architecture is None:
        return  # No further actions required, because when writing to a file, always an architecture must exist.
    # write_hdl_file must be called even if hdl is not needed, as write_hdl_file sets last_line_number_of_file1, which is read by Linking.
    hdl = write_hdl_file(write_to_file, header, entity, architecture, file_name, file_name_architecture)
    if write_to_file is True:
        copy_hdl_into_generated_hdl_tab(hdl, file_name)


def copy_hdl_into_generated_hdl_tab(hdl, file_name):
    main_window.date_of_hdl_file_shown_in_hdl_tab = os.path.getmtime(file_name)
    main_window.hdl_frame_text.config(state=tk.NORMAL)
    main_window.hdl_frame_text.delete("1.0", tk.END)
    main_window.hdl_frame_text.insert("1.0", hdl)
    main_window.hdl_frame_text.update_highlight_tags(
        10, ["not_read", "not_written", "control", "datatype", "function", "comment"]
    )
    main_window.hdl_frame_text.config(state=tk.DISABLED)
    # Bring the notebook tab with the hdl into the foreground:
    # notebook_ids = main_window.notebook.tabs()
    # for id in notebook_ids:
    #     if main_window.notebook.tab(id, option="text")=="generated HDL":
    #         main_window.notebook.select(id)
    main_window.show_tab("generated HDL")


def create_entity(file_name, file_line_number):
    entity = ""

    package_statements = hdl_generation_library.get_text_from_text_widget(main_window.interface_package_text)
    entity += package_statements
    number_of_new_lines = package_statements.count("\n")
    link_dictionary.LinkDictionary.link_dict_reference.add(
        file_name,
        file_line_number,
        "custom_text_in_interface_tab",
        number_of_new_lines,
        main_window.interface_package_text,
        "",
    )
    file_line_number += number_of_new_lines

    entity += "\n"
    file_line_number += 1

    entity += "entity " + main_window.module_name.get() + " is\n"
    link_dictionary.LinkDictionary.link_dict_reference.add(
        file_name, file_line_number, "Control-Tab", 1, "module_name", ""
    )
    file_line_number += 1

    generic_declarations = hdl_generation_library.get_text_from_text_widget(main_window.interface_generics_text)
    generic_declarations = list_separation_check.ListSeparationCheck(generic_declarations, "VHDL").get_fixed_list()
    if generic_declarations != "":
        generic_declarations = (
            "    generic (\n"
            + hdl_generation_library.indent_text_by_the_given_number_of_tabs(2, generic_declarations)
            + "    );\n"
        )
        file_line_number += 1  # switch to first line with generic value.
        number_of_new_lines = generic_declarations.count("\n") - 2  # Subtract first and last line
        link_dictionary.LinkDictionary.link_dict_reference.add(
            file_name,
            file_line_number,
            "custom_text_in_interface_tab",
            number_of_new_lines,
            main_window.interface_generics_text,
            "",
        )
        file_line_number += number_of_new_lines + 1
    entity += generic_declarations

    port_declarations = hdl_generation_library.get_text_from_text_widget(main_window.interface_ports_text)
    port_declarations = list_separation_check.ListSeparationCheck(port_declarations, "VHDL").get_fixed_list()
    if port_declarations != "":
        port_declarations = (
            "    port (\n"
            + hdl_generation_library.indent_text_by_the_given_number_of_tabs(2, port_declarations)
            + "    );\n"
        )
        file_line_number += 1  # switch to first line with port.
        number_of_new_lines = port_declarations.count("\n") - 2  # Subtract first and last line
        link_dictionary.LinkDictionary.link_dict_reference.add(
            file_name,
            file_line_number,
            "custom_text_in_interface_tab",
            number_of_new_lines,
            main_window.interface_ports_text,
            "",
        )
        file_line_number += number_of_new_lines + 1
    entity += port_declarations

    entity += "end entity;\n"
    file_line_number += 1
    return entity, file_line_number


def create_module_ports(file_name, file_line_number):
    module = ""
    file_line_number = 3  # Line 1 = Filename, Line 2 = Header
    module += "module " + main_window.module_name.get() + "\n"
    link_dictionary.LinkDictionary.link_dict_reference.add(
        file_name, file_line_number, "Control-Tab", 1, "module_name", ""
    )
    file_line_number += 1

    parameters = hdl_generation_library.get_text_from_text_widget(main_window.interface_generics_text)
    parameters = list_separation_check.ListSeparationCheck(parameters, "Verilog").get_fixed_list()
    if parameters != "":
        parameters = (
            "    #(parameter\n"
            + hdl_generation_library.indent_text_by_the_given_number_of_tabs(1, parameters)
            + "    )\n"
        )
        file_line_number += 1  # switch to first line with parameters.
        number_of_new_lines = parameters.count("\n") - 2  # Subtract first and last line
        link_dictionary.LinkDictionary.link_dict_reference.add(
            file_name,
            file_line_number,
            "custom_text_in_interface_tab",
            number_of_new_lines,
            main_window.interface_generics_text,
            "",
        )
        file_line_number += number_of_new_lines + 1
        module += parameters

    ports = hdl_generation_library.get_text_from_text_widget(main_window.interface_ports_text)
    ports = list_separation_check.ListSeparationCheck(ports, "Verilog").get_fixed_list()
    if ports != "":
        ports = "    (\n" + hdl_generation_library.indent_text_by_the_given_number_of_tabs(2, ports) + "    );\n"
        number_of_new_lines = ports.count("\n") - 2  # Subtract first and last line
        file_line_number += 1  # switch to first line with port.
        link_dictionary.LinkDictionary.link_dict_reference.add(
            file_name,
            file_line_number,
            "custom_text_in_interface_tab",
            number_of_new_lines,
            main_window.interface_ports_text,
            "",
        )
        file_line_number += number_of_new_lines + 1
        module += ports
    return module, file_line_number


def write_hdl_file(write_to_file, header, entity, architecture, path_name, path_name_architecture):
    global last_line_number_of_file1
    _, name_of_file = os.path.split(path_name)
    if main_window.select_file_number_text.get() == 1:
        if main_window.language.get() == "VHDL":
            comment_string = "--"
        elif main_window.language.get() == "Verilog":
            comment_string = "//"
        else:
            comment_string = "//"
        content = comment_string + " Filename: " + name_of_file + "\n"
        content += header
        content += entity
        content += architecture
        if write_to_file:
            fileobject = open(path_name, "w", encoding="utf-8")
            fileobject.write(content)
            fileobject.close()
        last_line_number_of_file1 = content.count("\n") + 1  # For example: 3 lines are separated by 2 returns.
        main_window.size_of_file1_line_number = len(str(last_line_number_of_file1)) + 2  # "+2" because of string ": "
        main_window.size_of_file2_line_number = 0
        content_with_numbers = add_line_numbers(content)
    else:
        content1 = "-- Filename: " + name_of_file + "\n"
        content1 += header
        content1 += entity
        if write_to_file:
            fileobject_entity = open(path_name, "w", encoding="utf-8")
            fileobject_entity.write(content1)
            fileobject_entity.close()
        last_line_number_of_file1 = content1.count("\n") + 1  # For example: 3 lines are separated by 2 returns.
        main_window.size_of_file1_line_number = len(str(last_line_number_of_file1)) + 2  # "+2" because of string ": "
        _, name_of_architecture_file = os.path.split(path_name_architecture)
        content2 = "-- Filename: " + name_of_architecture_file + "\n"
        content2 += header
        content2 += architecture
        if write_to_file:
            fileobject_architecture = open(path_name_architecture, "w", encoding="utf-8")
            fileobject_architecture.write(content2)
            fileobject_architecture.close()
        content_with_numbers1 = add_line_numbers(content1)
        content_with_numbers2 = add_line_numbers(content2)
        content_with_numbers = content_with_numbers1 + content_with_numbers2
        main_window.size_of_file2_line_number = (
            len(str(content_with_numbers.count("\n"))) + 2
        )  # "+2" because of string ": "
    return content_with_numbers


def get_file_names():
    if main_window.select_file_number_text.get() == 1:
        if main_window.language.get() == "VHDL":
            file_type = ".vhd"
        elif main_window.language.get() == "Verilog":
            file_type = ".v"
        else:
            file_type = ".sv"
        file_name = main_window.generate_path_value.get() + "/" + main_window.module_name.get() + file_type
        file_name_architecture = ""
    else:
        file_name = main_window.generate_path_value.get() + "/" + main_window.module_name.get() + "_e.vhd"
        file_name_architecture = (
            main_window.generate_path_value.get() + "/" + main_window.module_name.get() + "_fsm.vhd"
        )
    return file_name, file_name_architecture


def add_line_numbers(text):
    text_lines = text.split("\n")
    text_length_as_string = str(len(text_lines))
    number_of_needed_digits_as_string = str(len(text_length_as_string))
    content_with_numbers = ""
    for line_number, line in enumerate(text_lines, start=1):
        content_with_numbers += format(line_number, "0" + number_of_needed_digits_as_string + "d") + ": " + line + "\n"
    return content_with_numbers
