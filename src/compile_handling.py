"""
This module implements all methods executes the compile command stored in the Control-tab.
"""

import os
import re
import shlex
import subprocess
import tkinter as tk
from datetime import datetime
from os.path import exists
from tkinter import messagebox
from typing import Optional

import main_window
from constants import GuiTab


def compile_hdl() -> None:
    main_window.show_tab(GuiTab.COMPILE_MSG)
    if main_window.working_directory_value.get() != "" and not main_window.working_directory_value.get().isspace():
        try:
            os.chdir(main_window.working_directory_value.get())
        except FileNotFoundError:
            messagebox.showerror(
                "Error", "The working directory\n" + main_window.working_directory_value.get() + "\ndoes not exist."
            )
            return
    main_window.log_frame_text.config(state=tk.NORMAL)
    main_window.log_frame_text.insert(
        tk.END,
        "\n++++++++++++++++++++++++++++++++++++++ "
        + datetime.today().ctime()
        + " +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n",
    )
    main_window.log_frame_text.config(state=tk.DISABLED)
    start_time = datetime.now()
    commands = _get_command_list()
    # print("compile_handling: commands =", commands)
    for command in commands:
        success = _execute(command)
        if not success:
            break
    end_time = datetime.now()
    main_window.log_frame_text.config(state=tk.NORMAL)
    _insert_line_in_log("Finished user commands from Control-Tab after " + str(end_time - start_time) + ".\n")
    main_window.log_frame_text.config(state=tk.DISABLED)


def _execute(command: str) -> bool:
    command_array = shlex.split(command)  # Does not split quoted sub-strings with blanks.
    command_array_new = _replace_variables(command_array)
    if command_array_new is None:
        return False
    for command_part in command_array_new:
        _insert_line_in_log(command_part + " ")
    _insert_line_in_log("\n")
    try:
        process = subprocess.Popen(
            command_array_new,
            text=True,  # Decoding is done by Popen.
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        assert process.stdout is not None

        for line in process.stdout:  # Terminates when process.stdout is closed.
            if line != "\n":  # VHDL report-statements cause empty lines which mess up the protocol.
                _insert_line_in_log(line)
    except FileNotFoundError:
        command_string = ""
        for word in command_array_new:
            command_string += word + " "
        messagebox.showerror(
            "Error in HDL-FSM-Editor", "FileNotFoundError caused by compile command:\n" + command_string
        )
        return False
    return True


def _get_command_list() -> list[str]:
    command_string_tmp = main_window.compile_cmd.get()
    command_string = command_string_tmp.replace(";", " ; ")
    return command_string.split(";")


def _replace_variables(command_array: list[str]) -> Optional[list[str]]:
    command_array_new = []
    for entry in command_array:
        if entry == "$file":
            if main_window.select_file_number_text.get() == 2:
                messagebox.showerror(
                    "Error",
                    'The compile command uses $file, but the "2 files mode" is selected,\
so only $file1 and $file2 are allowed.',
                )
                return None
            language = main_window.language.get()
            if language == "VHDL":
                extension = ".vhd"
            elif language == "Verilog":
                extension = ".v"
            else:
                extension = ".sv"
            file_name = main_window.generate_path_value.get() + "/" + main_window.module_name.get() + extension
            if not exists(file_name):
                messagebox.showerror("Error", "Compile is not possible, HDL file " + file_name + " does not exist.")
                return None
            command_array_new.append(file_name)
        elif entry == "$file1":
            if main_window.select_file_number_text.get() == 1:
                messagebox.showerror(
                    "Error",
                    'The compile command uses $file1, but the "1 files mode" is selected, so only $file is allowed).',
                )
                return None
            file_name1 = main_window.generate_path_value.get() + "/" + main_window.module_name.get() + "_e.vhd"
            if not exists(file_name1):
                messagebox.showerror("Error", "Compile is not possible, as HDL file" + file_name1 + " does not exist.")
                return None
            command_array_new.append(file_name1)
        elif entry == "$file2":
            if main_window.select_file_number_text.get() == 1:
                messagebox.showerror(
                    "Error",
                    'The compile command uses $file2, but the "1 files mode" is selected, so only $file is allowed).',
                )
                return None
            file_name2 = main_window.generate_path_value.get() + "/" + main_window.module_name.get() + "_fsm.vhd"
            if not exists(file_name2):
                messagebox.showerror("Error", "Compile is not possible, as HDL file" + file_name2 + " does not exist.")
                return None
            command_array_new.append(file_name2)
        elif entry == "$name":
            command_array_new.append(main_window.module_name.get())
        else:
            command_array_new.append(entry)
    return command_array_new


def _insert_line_in_log(line: str) -> None:
    if main_window.language.get() == "VHDL":
        # search for compiler-message with ":<line-number>:<column-number>:":
        regex_message_find = main_window.regex_message_find_for_vhdl
    else:
        regex_message_find = main_window.regex_message_find_for_verilog
    try:
        match_object_of_message = re.match(regex_message_find, line)
    except re.error as e:
        print("Error in HDL-FSM-Editor by regular expression", repr(e))
        return

    line_low = line.lower()
    main_window.log_frame_text.config(state=tk.NORMAL)
    if match_object_of_message is not None or " error " in line_low or " warning " in line_low:
        # Add line together with color-tag to the text:
        if main_window.language.get() == "VHDL" and "report note" in line_low:
            main_window.log_frame_text.insert(tk.END, line, ("message_green"))
        else:
            main_window.log_frame_text.insert(tk.END, line, ("message_red"))
    else:
        main_window.log_frame_text.insert(tk.END, line)
    main_window.log_frame_text.config(state=tk.DISABLED)
    main_window.log_frame_text.see(tk.END)
