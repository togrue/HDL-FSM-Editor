"""
"""
import os
import re
import shlex
import subprocess
import tkinter as tk
from datetime import datetime
from os.path import exists
from tkinter import messagebox

import main_window


def compile_hdl():
    show_compile_messages_tab()
    if main_window.working_directory_value.get()!="" and not main_window.working_directory_value.get().isspace():
        try:
            os.chdir(main_window.working_directory_value.get())
        except FileNotFoundError:
            messagebox.showerror("Error", "The working directory\n" + main_window.working_directory_value.get() + "\ndoes not exist.")
            return
    main_window.log_frame_text.config(state=tk.NORMAL)
    main_window.log_frame_text.insert(tk.END,
                 "\n++++++++++++++++++++++++++++++++++++++ " + datetime.today().ctime() +" +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n")
    main_window.log_frame_text.config(state=tk.DISABLED)
    start_time = datetime.now()
    commands = get_command_list()
    #print("compile_handling: commands =", commands)
    for command in commands:
        success = execute(command)
        if not success:
            break
    end_time = datetime.now()
    main_window.log_frame_text.config(state=tk.NORMAL)
    insert_line_in_log("Finished user commands from Control-Tab after " + str(end_time - start_time) + ".\n")
    main_window.log_frame_text.config(state=tk.DISABLED)

def execute(command):
    command_array = shlex.split(command) # Does not split quoted sub-strings with blanks.
    command_array_new = replace_variables(command_array)
    if command_array_new is None:
        return False
    for command_part in command_array_new:
        insert_line_in_log(command_part+" ")
    insert_line_in_log("\n")
    try:
        process = subprocess.Popen(command_array_new,
                                    text=True, # Decoding is done by Popen.
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT)
        for line in process.stdout: # Terminates when process.stdout is closed.
            if line!="\n": # VHDL report-statements cause empty lines which mess up the protocol.
                insert_line_in_log(line)
    except FileNotFoundError:
        command_string = ""
        for word in command_array_new:
            command_string += word + " "
        messagebox.showerror("Error in HDL-FSM-Editor", "FileNotFoundError caused by compile command:\n" + command_string)
        return False
    return True

def show_compile_messages_tab():
    notebook_ids = main_window.notebook.tabs()
    for notebook_id in notebook_ids:
        if main_window.notebook.tab(notebook_id, option="text")=="Compile Messages":
            main_window.notebook.select(notebook_id)

def get_command_list():
    command_string_tmp = main_window.compile_cmd.get()
    command_string = command_string_tmp.replace(";", " ; ")
    return command_string.split(";")

def replace_variables(command_array):
    command_array_new = []
    for entry in command_array:
        if entry=="$file":
            if main_window.select_file_number_text.get()==2:
                messagebox.showerror("Error", 'The compile command uses $file, but the "2 files mode" is selected, so only $file1 and $file2 are allowed.')
                return
            language = main_window.language.get()
            if language=="VHDL":
                extension = ".vhd"
            elif language=="Verilog":
                extension = ".v"
            else:
                extension = ".sv"
            file_name = main_window.generate_path_value.get() + "/" + main_window.module_name.get() + extension
            if not exists(file_name):
                messagebox.showerror("Error", "Compile is not possible, HDL file " + file_name + " does not exist.")
                return
            command_array_new.append(file_name)
        elif entry=="$file1":
            if main_window.select_file_number_text.get()==1:
                messagebox.showerror("Error", 'The compile command uses $file1, but the "1 files mode" is selected, so only $file is allowed).')
                return
            file_name1 = main_window.generate_path_value.get() + "/" + main_window.module_name.get() + "_e.vhd"
            if not exists(file_name1):
                messagebox.showerror("Error", "Compile is not possible, as HDL file" + file_name1 + " does not exist.")
                return
            command_array_new.append(file_name1)
        elif entry=="$file2":
            if main_window.select_file_number_text.get()==1:
                messagebox.showerror("Error", 'The compile command uses $file2, but the "1 files mode" is selected, so only $file is allowed).')
                return
            file_name2 = main_window.generate_path_value.get() + "/" + main_window.module_name.get() + "_fsm.vhd"
            if not exists(file_name2):
                messagebox.showerror("Error", "Compile is not possible, as HDL file" + file_name2 + " does not exist.")
                return
            command_array_new.append(file_name2)
        elif entry=="$name":
            command_array_new.append(main_window.module_name.get())
        else:
            command_array_new.append(entry)
    return command_array_new

def copy_into_compile_messages_tab(stdout, stderr, command_array_new):
    main_window.log_frame_text.config(state=tk.NORMAL)
    for part in command_array_new:
        main_window.log_frame_text.insert(tk.END, part + " ")
    main_window.log_frame_text.insert(tk.END, "\n")
    main_window.log_frame_text.insert(tk.END, "STDERR:\n")
    main_window.log_frame_text.insert(tk.END, stderr)
    main_window.log_frame_text.insert(tk.END, "STDOUT:\n")
    main_window.log_frame_text.insert(tk.END, stdout)
    main_window.log_frame_text.insert(tk.END, "=========================================================================\n")
    main_window.log_frame_text.config(state=tk.DISABLED)
    main_window.log_frame_text.see(tk.END)

def insert_line_in_log(text):
    if main_window.language.get()=="VHDL":
        regex_message_find = main_window.regex_message_find_for_vhdl
    else:
        regex_message_find = main_window.regex_message_find_for_verilog
    text_low = text.lower()
    match_object_of_message = re.match(regex_message_find, text)
    main_window.log_frame_text.config(state=tk.NORMAL)
    if match_object_of_message is not None or "error" in text_low  or "warning" in text_low:
        if main_window.language.get()=="VHDL" and "report note" in text_low:
            main_window.log_frame_text.insert(tk.END, text, ("message_green"))
        else:
            main_window.log_frame_text.insert(tk.END, text, ("message_red"))
    else:
        main_window.log_frame_text.insert(tk.END, text)
    main_window.log_frame_text.config(state=tk.DISABLED)
    main_window.log_frame_text.see(tk.END)
