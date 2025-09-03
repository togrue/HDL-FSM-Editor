"""
The code was copied and extended from https://stackoverflow.com/questions/40617515/python-tkinter-text-modified-callback
"""

import os
import re
import subprocess
import tkinter as tk
from re import Match
from tkinter import messagebox
from typing import Any, Optional

import canvas_editing
import codegen.hdl_generation_architecture_state_actions as hdl_generation_architecture_state_actions
import codegen.hdl_generation_library as hdl_generation_library
import config
import constants
import file_handling
import global_actions_combinatorial
import linting


class CustomText(tk.Text):
    """
    This code was copied and extended from:
    https://stackoverflow.com/questions/40617515/python-tkinter-text-modified-callback
    """

    read_variables_of_all_windows: dict["CustomText", list[str]] = {}
    written_variables_of_all_windows: dict["CustomText", list[str]] = {}

    def __init__(self, *args: Any, text_type: str, **kwargs: Any) -> None:
        """A text widget that report on internal widget commands"""
        tk.Text.__init__(self, *args, **kwargs)
        self.text_type = text_type
        # create a proxy for the underlying widget
        self._orig = str(self) + "_orig"
        self.tk.call("rename", str(self), self._orig)
        self.tk.createcommand(str(self), self._proxy)
        self.bind("<Tab>", lambda event: self.replace_tabs_by_blanks())
        # Overwrites the default control-o = "insert a new line", needed for opening a new file:
        self.bind("<Control-o>", lambda event: self._open())
        # After pressing a key 2 things happen:
        # 1. The new character is inserted in the text.
        # 2. format() is started
        # But as inserting the character takes a while, format() will still find the old text,
        # so it must be delayed until the character was inserted:
        self.bind(
            "<Key>", lambda event: self.format_after_idle()
        )  # This binding will be overwritten for the CustomText objects in Interface/Internals tab.
        self.bind("<Button-1>", lambda event: self.tag_delete("highlight"))
        self.signals_list: list[
            str
        ] = []  # Will be updated at file-read, key-event, undo/redo if text_type is a declaration.
        self.constants_list: list[str] = []
        self.readable_ports_list: list[str] = []
        self.writable_ports_list: list[str] = []
        self.generics_list: list[str] = []
        self.port_types_list: list[str] = []
        CustomText.read_variables_of_all_windows[self] = []
        CustomText.written_variables_of_all_windows[self] = []
        self.tag_config("message_red", foreground="red")
        self.tag_config("message_green", foreground="green")

    def _open(self) -> str:
        file_handling.open_file()
        # Prevent a second call of open_file() by bind_all binding (which is located in entry 4 of the bind-list):
        return "break"

    def _proxy(self, command: str, *args: Any) -> Any:
        cmd = (self._orig, command) + args
        try:
            result = self.tk.call(cmd)
            if command in ("insert", "delete", "replace"):
                self.event_generate("<<TextModified>>")
            return result
        except Exception:
            return None

    def replace_tabs_by_blanks(self) -> str:
        self.insert(tk.INSERT, "    ")  # replace the Tab by 4 blanks.
        self.format_after_idle()
        return "break"  # This prevents the "Tab" to be inserted in the text.

    def edit_in_external_editor(self) -> None:
        import main_window

        file_name = "hdl-fsm-editor.tmp.vhd" if main_window.language.get() == "VHDL" else "hdl-fsm-editor.tmp.v"
        with open(file_name, "w", encoding="utf-8") as fileobject:
            fileobject.write(self.get("1.0", tk.END + "- 1 chars"))
        try:
            edit_cmd = main_window.edit_cmd.get().split()
            edit_cmd.append(file_name)
            with subprocess.Popen(edit_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
                while True:
                    poll = process.poll()
                    if poll is not None:
                        break
        except FileNotFoundError:
            messagebox.showerror("Error", "Error when running " + main_window.edit_cmd.get() + " " + file_name)
            return
        with open(file_name, encoding="utf-8") as fileobject:
            new_text = fileobject.read()
        os.remove(file_name)
        self.delete("1.0", tk.END)
        self.insert("1.0", new_text)
        self.format()

    def format_after_idle(self) -> None:
        if self.text_type != "log":
            self.after_idle(self.format)

    def format(self) -> None:
        text = self.get("1.0", tk.END)
        self.__update_size_of_text_box(text)
        self.__update_entry_of_this_window_in_list_of_read_and_written_variables_of_all_windows()
        self.update_highlighting()

    def __update_size_of_text_box(self, text: str) -> None:
        import main_window

        nr_of_lines = 0
        nr_of_characters_in_line = 0
        max_line_length = 0

        if self not in [
            main_window.interface_generics_text,
            main_window.interface_package_text,
            main_window.interface_ports_text,
            main_window.internals_architecture_text,
            main_window.internals_process_clocked_text,
            main_window.internals_process_combinatorial_text,
            main_window.internals_package_text,
        ]:
            for c in text:
                if c != "\n":
                    nr_of_characters_in_line += 1
                    max_line_length = max(nr_of_characters_in_line, max_line_length)
                else:
                    nr_of_lines += 1
                    nr_of_characters_in_line = 0
            self.config(width=max_line_length)
            self.config(height=nr_of_lines)

    def update_highlighting(self) -> None:
        self.update_highlight_tags(int(canvas_editing.fontsize), ["control", "datatype", "function"])
        linting.recreate_keyword_list_of_unused_signals()
        linting.update_highlight_tags_in_all_windows_for_not_read_not_written_and_comment()

    def update_highlight_tags(self, fontsize: int, keyword_type_list: list[str]) -> None:
        for keyword_type in keyword_type_list:
            self.tag_delete(keyword_type)
            import main_window

            for keyword in main_window.keywords[keyword_type]:
                if self.text_type == "comment":  # State comment text
                    if keyword == "comment":  # keywords "not_read", "not_written" are ignored.
                        self.add_highlight_tag_for_single_keyword(keyword_type, keyword)
                else:
                    self.add_highlight_tag_for_single_keyword(keyword_type, keyword)
            if self.text_type in ("condition", "action", "comment"):
                self.tag_configure(
                    keyword_type,
                    foreground=config.KEYWORD_COLORS[keyword_type],
                    font=("Courier", fontsize, "normal"),
                )
            else:
                self.tag_configure(keyword_type, foreground=config.KEYWORD_COLORS[keyword_type], font=("Courier", 10))

    def add_highlight_tag_for_single_keyword(self, keyword_type: str, keyword: str) -> None:
        copy_of_text = self.get("1.0", tk.END + "- 1 chars")
        if copy_of_text == "":
            return
        copy_of_text = self.replace_strings_and_attributes_by_blanks(copy_of_text)
        while True:
            if keyword_type == "comment":
                match_object = re.search(keyword, copy_of_text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
                if not match_object:
                    break
                if match_object.start() == match_object.end():
                    break
                replace_string = " " * (match_object.end() - match_object.start())
                copy_of_text = (
                    copy_of_text[: match_object.start()] + replace_string + copy_of_text[match_object.end() :]
                )
                self.tag_add(
                    "comment",
                    "1.0 + " + str(match_object.start()) + " chars",
                    "1.0 + " + str(match_object.end()) + " chars",
                )
            else:
                # The keyword might be some strange character, when the user stumbles of the keyboard.
                # Normally this does not cause any problems, because no match_object will be created.
                # If a match object is created, it is important that the match is removed from the text.
                # For example for the keyword '.' the match is not removed.
                # So a check was inserted which checks if the text has been modified here.
                search_string = (
                    "([^a-zA-Z0-9_]|^)" + keyword + "([^a-zA-Z0-9_]|$)"
                )  # Prevent a hit, when the keyword is part of another word.
                try:
                    match_object = re.search(search_string, copy_of_text, flags=re.IGNORECASE)
                except re.error:
                    # Happens i.e. if search_string contains "**".
                    match_object = None
                if not match_object:
                    break
                match_start, match_end = self.remove_surrounding_characters_from_the_match(match_object, keyword)
                old_text = copy_of_text
                copy_of_text = copy_of_text[:match_start] + " " * len(keyword) + copy_of_text[match_end:]
                if copy_of_text == old_text:
                    break
                self.tag_add(keyword_type, "1.0 + " + str(match_start) + " chars", "1.0 + " + str(match_end) + " chars")

    def replace_strings_and_attributes_by_blanks(self, copy_of_text: str) -> str:
        for search_string in ["'image", "'length", '".*?"', "'.*?'"]:
            while True:
                match_object = re.search(search_string, copy_of_text, flags=re.IGNORECASE)
                if match_object:
                    if match_object.start() == match_object.end():
                        break
                    replace_string = " " * (match_object.end() - match_object.start())
                    copy_of_text = (
                        copy_of_text[: match_object.start()] + replace_string + copy_of_text[match_object.end() :]
                    )
                else:
                    break
        return copy_of_text

    def remove_surrounding_characters_from_the_match(self, match_object: Match[str], keyword: str) -> tuple[int, int]:
        if match_object.end() - match_object.start() == len(keyword) + 2:
            return match_object.start() + 1, match_object.end() - 1
        if match_object.end() - match_object.start() == len(keyword) + 1:
            if match_object.group().endswith(keyword):
                return match_object.start() + 1, match_object.end()
            return match_object.start(), match_object.end() - 1
        return match_object.start(), match_object.end()

    def undo(self) -> None:
        # self.edit_undo() # causes a second "undo", as Ctrl-z automatically starts edit_undo()
        self.after_idle(self.update_declaration_lists)
        self.format_after_idle()

    def redo(self) -> None:
        self.edit_redo()
        self.after_idle(self.update_declaration_lists)
        self.format_after_idle()

    def update_declaration_lists(self) -> None:
        import main_window

        if self == main_window.internals_architecture_text:
            self.update_custom_text_class_signals_list()
        elif self == main_window.interface_ports_text:
            self.update_custom_text_class_ports_list()

    def update_custom_text_class_signals_list(self) -> None:
        all_signal_declarations = self.get("1.0", tk.END).lower()
        self.signals_list = hdl_generation_library.get_all_declared_signal_names(all_signal_declarations)
        self.constants_list = hdl_generation_library.get_all_declared_constant_names(all_signal_declarations)
        self.__update_entry_of_this_window_in_list_of_read_and_written_variables_of_all_windows()
        self.update_highlighting()

    def update_custom_text_class_ports_list(self) -> None:
        import main_window

        all_port_declarations = main_window.interface_ports_text.get("1.0", tk.END).lower()
        self.readable_ports_list = hdl_generation_architecture_state_actions.get_all_readable_ports(
            all_port_declarations, check=False
        )
        self.writable_ports_list = hdl_generation_architecture_state_actions.get_all_writable_ports(
            all_port_declarations
        )
        self.port_types_list = hdl_generation_architecture_state_actions.get_all_port_types(all_port_declarations)

    def update_custom_text_class_generics_list(self) -> None:
        import main_window

        all_generic_declarations = main_window.interface_generics_text.get("1.0", tk.END).lower()
        self.generics_list = hdl_generation_architecture_state_actions.get_all_generic_names(all_generic_declarations)

    def __update_entry_of_this_window_in_list_of_read_and_written_variables_of_all_windows(self) -> None:
        import main_window

        CustomText.read_variables_of_all_windows[self] = []
        CustomText.written_variables_of_all_windows[self] = []
        text = self.get("1.0", tk.END + "- 1 chars")
        text = hdl_generation_library.convert_hdl_lines_into_a_searchable_string(text)
        if main_window.language.get() == "VHDL":
            text = self._remove_loop_indices(text)
        if main_window.language.get() == "VHDL" and self._text_is_global_actions_combinatorial():
            text = self._add_uncomplete_vhdl_variables_to_read_or_written_variables_of_all_windows(text)
        text = self.__remove_keywords(text)
        if main_window.language.get() == "VHDL":
            text = re.sub(r"\..*?\s", " ", text)  # remove all record-element-names from their signal/variable names
        if self.text_type == "condition":
            text = self.__remove_condition_keywords(text)
            CustomText.read_variables_of_all_windows[self] = text.split()
        elif self.text_type == "action":
            text = self.__add_read_variables_from_procedure_calls_to_read_variables_of_all_windows(text)
            text = self.__add_read_variables_from_with_select_blocks_to_read_variables_of_all_windows(text)
            text = self.__add_read_variables_from_conditions_to_read_variables_of_all_windows(text)
            text = self.__add_read_variables_from_case_constructs_to_read_variables_of_all_windows(text)
            text = self.__add_read_variables_from_assignments_to_read_variables_of_all_windows(text)
            text = self.__add_read_variables_from_always_statements_to_read_variables_of_all_windows(text)
            # Remove duplicates:
            CustomText.read_variables_of_all_windows[self] = list(set(CustomText.read_variables_of_all_windows[self]))
            text = re.sub(
                # remove remaining "when" of a "case"-statement (left hand side):
                " when | when$|^when |^when$",
                "",
                text,
                flags=re.I,
            )
            text = re.sub(
                # remove remaining "else" of an if-clause (left hand side):
                " else | else$|^else |^else$",
                "",
                text,
                flags=re.I,
            )
            # Store the remaining variable names and remove duplicates from the list:
            # print("written-variables = ", list(set(text.split())))
            CustomText.written_variables_of_all_windows[self] = list(set(text.split()))
            # When the ";" is missing, then the right hand side with "<=" could not be found and erased.
            # So remove "<=" and ":=" from these lists:
            if "<=" in CustomText.read_variables_of_all_windows[self]:
                CustomText.read_variables_of_all_windows[self].remove("<=")
            if ":=" in CustomText.read_variables_of_all_windows[self]:
                CustomText.read_variables_of_all_windows[self].remove(":=")
            if "<=" in CustomText.written_variables_of_all_windows[self]:
                CustomText.written_variables_of_all_windows[self].remove("<=")
            if ":=" in CustomText.written_variables_of_all_windows[self]:
                CustomText.written_variables_of_all_windows[self].remove(":=")

    def _text_is_global_actions_combinatorial(self) -> bool:
        import main_window

        list_of_canvas_id = main_window.canvas.find_withtag("global_actions_combinatorial1")
        if list_of_canvas_id:
            canvas_id = list_of_canvas_id[0]
            if global_actions_combinatorial.GlobalActionsCombinatorial.dictionary[canvas_id].text_id == self:
                return True
        return False

    def _remove_loop_indices(self, text: str) -> str:
        # Suchen nach "for   in"
        search_for_loop_indizes = r"\sfor\s+(.+?)\s+in\s"
        while True:
            match = re.search(search_for_loop_indizes, text, flags=re.IGNORECASE)
            if match:
                if match.start() == match.end():
                    break
                # print("match found =", match.group(0) + "|")
                # print("index found =", match.group(1) + "|")
                text = text[: match.start()] + text[match.end() :]
                search_for_index = " " + match.group(1) + " "
                text = re.sub(search_for_index, " ", text)
            else:
                break
        return text

    def _add_uncomplete_vhdl_variables_to_read_or_written_variables_of_all_windows(self, text: str) -> str:
        text_before_process_list, process_list, remaining_text = self._split(text)
        for p_number, process in enumerate(process_list):
            process, all_variable_names = self._remove_variable_declarations(process)
            process, written_variables = self._remove_written_variables(process, all_variable_names)
            process, read_variables = self._remove_read_variables(process, all_variable_names)
            process_list[p_number] = process
            self._check_variables(all_variable_names, written_variables, read_variables)
        new_text = ""
        for i, text_before in enumerate(text_before_process_list):
            new_text += text_before + process_list[i]
        return new_text + remaining_text

    def _split(self, text: str) -> tuple[list[str], list[str], str]:
        process_list = []
        search_for_processes = r"process(\s|\().*?\sbegin\s.*?\send\s+process(\s*;|\s.*?;)"
        text_before_process_list = []
        while True:
            match = re.search(search_for_processes, text, flags=re.IGNORECASE)
            if match:
                if match.start() == match.end():
                    break
                text_before_process_list.append(text[: match.start()])
                process_list.append(text[match.start() : match.end()])
                text = text[match.end() :]  # remove before-match and match from text
            else:
                break
        return text_before_process_list, process_list, text

    def _remove_variable_declarations(self, process: str) -> tuple[str, list[str]]:
        all_variable_names = []
        search_for_variable_declaration = r"\svariable\s+(.*?):.*?;"
        while True:
            match = re.search(search_for_variable_declaration, process, flags=re.IGNORECASE)
            if match:
                if match.start() == match.end():
                    break
                all_variable_names.append(match.group(1).strip())
                process = process[: match.start()] + " " + process[match.end() :]  # remove declaration from process
            else:
                break
        return process, all_variable_names

    def _remove_written_variables(self, process: str, all_variable_names: list[str]) -> tuple[str, list[str]]:
        written_variables = []
        for variable_name in all_variable_names:
            search_for_assignment_to_variable = rf"\s{variable_name}\s*:="
            while True:
                match = re.search(search_for_assignment_to_variable, process, flags=re.IGNORECASE)
                if match:
                    if match.start() == match.end():
                        break
                    process = (
                        process[: match.start()] + " " + process[match.end() - 2 :]
                    )  # remove assigned variable-name from process (without ":=")
                    written_variables.append(variable_name)
                else:
                    break
        written_variables = list(set(written_variables))  # remove duplicates
        return process, written_variables

    def _remove_read_variables(self, process: str, all_variable_names: list[str]) -> tuple[str, list[str]]:
        read_variables = []
        for variable_name in all_variable_names:
            search_for_reading_of_variable = rf"\s{variable_name}\s*"
            while True:
                match = re.search(search_for_reading_of_variable, process, flags=re.IGNORECASE)
                if match:
                    if match.start() == match.end():
                        break
                    process = (
                        process[: match.start()] + " " + process[match.end() :]
                    )  # remove assigned variable-name from process
                    read_variables.append(variable_name)
                else:
                    break
        read_variables = list(set(read_variables))  # remove duplicates
        return process, read_variables

    def _check_variables(self, all_variable_names: list[str], written_variables: list[str], read_variables: list[str]) -> None:
        for variable_name in all_variable_names:
            if variable_name not in written_variables + read_variables or variable_name not in written_variables:
                CustomText.read_variables_of_all_windows[self] += [variable_name]  # will be colored red
            else:
                CustomText.written_variables_of_all_windows[self] += [variable_name]  # will be colored yellow
        for read_or_written_variable in written_variables + read_variables:
            if read_or_written_variable not in all_variable_names:
                CustomText.read_variables_of_all_windows[self] += [read_or_written_variable]  # will be colored red

    def __remove_keywords(self, text: str) -> str:
        import main_window

        if main_window.language.get() == "VHDL":
            text = self.__remove_keywords_from_vhdl(text)
        else:
            text = self.__remove_keywords_from_verilog(text)
        return text

    def __remove_keywords_from_vhdl(self, text: str) -> str:
        for keyword in constants.VHDL_KEYWORDS_FOR_SIGNAL_HANDLING + (
            " process[^;]*?begin ",  # Remove complete process headers, if some exist.
            " end\\s+?process\\s*?;",  # remove end of process, before ...
            " process .*?$",  # ... when not complete process headers exist, remove until a return is found.
            " end\\s+?case\\s*?;",
            " end\\s+?if\\s*?;",
            " end\\s*?;",
            " end\\s+",
            "\\(",
            "\\)",
            "\\+",
            "\\*",
            "true",
            "false",
            "-",
            "/",
            "%",
            "&",
            "=>",  # something like "others =>"
            " [0-9]+ ",  # something like " 123 "
            "' . '",  # something like the std_logic value ' 1 ' or ' 0 '
            '[^\\s]"[0-9,a-f,A-F]+"',  # something like X"1234"
            "'.*?'",  # Remove strings from report-commands (they might contain ';')
            '".*?"',  # Remove strings from report-commands (they might contain ';')
        ):
            text = re.sub(keyword, "  ", text, flags=re.I)  # Keep the blanks the keyword is surrounded by.
        for keyword in constants.VHDL_KEYWORDS["datatype"]:
            text = re.sub(" " + keyword + " ", "  ", text, flags=re.I)  # Keep the blanks the keyword is surrounded by.
        return text

    def __remove_keywords_from_verilog(self, text: str) -> str:
        for keyword in constants.VERILOG_KEYWORDS_FOR_SIGNAL_HANDLING + (
            " end ",
            " endcase\\s*?;",
            "\\(",
            "\\)",
            "{",
            "}",
            "\\+",
            "-",
            "/",
            "%",
            " [0-9]+ ",  # something like 123
            " [0-9]+'[^0-9][0-9]+ ",  # something like 3'b000
        ):
            text = re.sub(keyword, "  ", text, flags=re.I)  # Keep the blanks the keyword is surrounded by.
        return text

    def __remove_condition_keywords(self, text: str) -> str:
        import main_window

        if main_window.language.get() == "VHDL":
            for keyword in (" = ", " /= ", " < ", " <= ", " > ", " >= "):
                text = re.sub(keyword, "  ", text, flags=re.I)  # Keep the blanks the keyword is surrounded by.
        else:
            for keyword in (
                " === ",
                " == ",
                " != ",
                " < ",
                " <= ",
                " > ",
                " >= ",
                " = ",  # This is an uncomplete comparison, which shall not be identified as signal by highlighting.
                " ! ",  # This is an uncomplete comparison, which shall not be identified as signal by highlighting.
            ):
                text = re.sub(keyword, "  ", text, flags=re.I)  # Keep the blanks the keyword is surrounded by.
        return text

    def __add_read_variables_from_procedure_calls_to_read_variables_of_all_windows(self, text: str) -> str:
        import main_window

        if main_window.language.get() == "VHDL":
            all_procedure_calls = []
            search_for_not_assignments = "^[^=]*?;"
            while True:
                match = re.search(search_for_not_assignments, text, flags=re.IGNORECASE)
                if match:
                    if match.start() == match.end():
                        break
                    all_procedure_calls.append(match.group(0)[:-1])  # append without semicolon
                    text = text[: match.start()] + text[match.end() :]  # remove match from text
                else:
                    break
            for procedure_call in all_procedure_calls:
                procedure_parameters = self._remove_procedure_name(procedure_call)
                procedure_parameter_list = procedure_parameters.split(",")
                for procedure_parameter in procedure_parameter_list:
                    procedure_parameter = procedure_parameter.strip()
                    if (
                        procedure_parameter != ""
                        and procedure_parameter not in ["x", "X"]
                        and not procedure_parameter.isdigit()
                    ):
                        # As the procedure definition may not be part of this VHDL file,
                        # it can not for sure be determined, which parameter is read and which parameter is written.
                        if procedure_parameter in main_window.interface_ports_text.readable_ports_list:
                            # If a parameter is an input port, then it is read.
                            CustomText.read_variables_of_all_windows[self] += [procedure_parameter]
                        elif procedure_parameter in main_window.interface_ports_text.writable_ports_list:
                            # If a parameter is an output port, then it is written and
                            # must be added to the variable text with a pseudo assignment:
                            text += procedure_parameter + " <= ;"
                        else:
                            # If a parameter is neither an input nor an output, then the parameter is probably a signal.
                            # But it is not clear if it is written or read and
                            # to avoid false alarms it is added to both lists:
                            CustomText.read_variables_of_all_windows[self] += [procedure_parameter]
                            text += procedure_parameter + " <= ;"
        return text

    def _remove_procedure_name(self, procedure_call: str) -> str:
        return re.sub(r"^.*?\s", "", procedure_call.lstrip())

    def __add_read_variables_from_with_select_blocks_to_read_variables_of_all_windows(self, text: str) -> str:
        import main_window

        if main_window.language.get() == "VHDL":
            with_select_search_pattern = "with\\s+.*?\\s+select"
            all_with_selects = []
            while True:  # Collect all with_selects and remove them from text.
                match = re.search(with_select_search_pattern, text, flags=re.IGNORECASE)
                if match:
                    if match.start() == match.end():
                        break
                    all_with_selects.append(match.group(0))
                    text = text[: match.start()] + text[match.end() :]  # remove match from text
                else:
                    break
            for with_select in all_with_selects:
                with_select = re.sub("^with ", " ", with_select, flags=re.I)
                with_select = re.sub(" select$", " ", with_select, flags=re.I)
                CustomText.read_variables_of_all_windows[self] += (
                    with_select.split()
                )  # split() removes only blanks here.
        return text

    def __add_read_variables_from_conditions_to_read_variables_of_all_windows(self, text: str) -> str:
        import main_window

        if main_window.language.get() == "VHDL":
            condition_search_pattern = (
                "^if\\s+[^;]*?\\s+then| if\\s+[^;]*?\\s+then|elsif\\s+[^;]*?\\s+then|"
                + "^when\\s+[^;]*?\\s+else| when\\s+[^;]*?\\s+else"
            )
        else:
            condition_search_pattern = "^if\\s+[^;]*?\\s+begin| if\\s+[^;]*?\\s+begin"  # Verilog
        all_conditions = []
        while True:  # Collect all conditions and remove them from text.
            # print("text for search =", text)
            match = re.search(condition_search_pattern, text, flags=re.IGNORECASE)
            if match:
                if match.start() == match.end():
                    break
                # print("match.group(0)", match.group(0))
                all_conditions.append(match.group(0))
                text = text[: match.start()] + text[match.end() :]  # remove match from text
                # print(text)
            else:
                break
        for condition in all_conditions:
            if main_window.language.get() == "VHDL":
                condition = re.sub("^if| if", " ", condition, flags=re.I)
                condition = re.sub("^elsif| elsif", " ", condition, flags=re.I)
                condition = re.sub(" then$", " ", condition, flags=re.I)
                condition = re.sub("^when| when", " ", condition, flags=re.I)
                condition = re.sub(" else$", " ", condition, flags=re.I)
                for keyword in (" = ", " /= ", " < ", " <= ", " > ", " >= "):
                    condition = re.sub(keyword, "  ", condition)  # Keep the blanks the keyword is surrounded by.
            else:
                condition = re.sub("^if| if ", " ", condition, flags=re.I)
                condition = re.sub(" begin$", " ", condition, flags=re.I)
                for keyword in (
                    " === ",
                    " == ",
                    " != ",
                    " < ",
                    " <= ",
                    " > ",
                    " >= ",
                    " = ",  # This is an uncomplete comparison, which shall not be identified as signal by highlighting.
                    " ! ",
                ):  # This is an uncomplete comparison, which shall not be identified as signal by highlighting.
                    condition = re.sub(keyword, "  ", condition)  # Keep the blanks the keyword is surrounded by.
            CustomText.read_variables_of_all_windows[self] += condition.split()
        return text

    def __add_read_variables_from_case_constructs_to_read_variables_of_all_windows(self, text: str) -> str:
        import main_window

        if main_window.language.get() == "VHDL":
            case_search_pattern = "^case\\s+.+?\\s+is| case\\s+.+?\\s+is"
        else:
            case_search_pattern = "^case\\s*?\\(.*?\\)| case\\s*?\\(.*?\\)"  # Verilog
        all_cases = []
        while True:  # Collect all case-statements and remove them from text.
            match = re.search(case_search_pattern, text, flags=re.IGNORECASE)
            if match:
                if match.start() == match.end():
                    break
                all_cases.append(match.group(0))
                text = text[: match.start()] + text[match.end() :]  # remove match from text
            else:
                break
        for case in all_cases:
            if main_window.language.get() == "VHDL":
                case = re.sub("^case | case ", "", case, flags=re.I)
                case = re.sub(" is$", "", case, flags=re.I)
            else:
                case = re.sub("^case\\s*?\\(| case\\s*?\\(", "", case, flags=re.I)
                case = re.sub("\\)", "", case, flags=re.I)
                case = re.sub(",", " ", case, flags=re.I)
            CustomText.read_variables_of_all_windows[self] += case.split()
        return text

    def __add_read_variables_from_assignments_to_read_variables_of_all_windows(self, text: str) -> str:
        right_hand_side_search_pattern = "=.*?;"
        while True:  # Collect all right hand sides and remove them from text.
            match = re.search(right_hand_side_search_pattern, text, flags=re.IGNORECASE)
            if match:
                # remove not only the match but also complete ":=" or "<=":
                if match.start() - 1 == match.end():
                    break
                text = text[: match.start() - 1] + text[match.end() :]
                hit = match.group(0)[+1:-1]
                hit = re.sub(",", "", hit)  # Remove "," of a "with .. select" statement.
                # remove remaining "when" of a "with .. select"-statement (right hand side):
                hit = re.sub(" when | when$|^when |^when$", "", hit, flags=re.I)
                # remove remaining "else" of an "when .. else"-clause (right hand side).
                hit = re.sub(" else | else$|^else |^else$", "", hit, flags=re.I)
                hit = re.sub(" ' ", "", hit, flags=re.I)  # remove remaining "ticks" of VHDL attributes
                CustomText.read_variables_of_all_windows[self] += list(set(hit.split()))  # remove duplicates from list
            else:
                break
        return text

    def __add_read_variables_from_always_statements_to_read_variables_of_all_windows(self, text: str) -> str:
        while True:
            match = re.search(r"always\s*@.*?begin", text, flags=re.IGNORECASE)
            if match:
                if match.start() == match.end():
                    break
                text = text[: match.start()] + text[match.end() :]
                hit = match.group(0)
                hit = re.sub(r"always\s*@", "", hit, flags=re.IGNORECASE)
                hit = re.sub(r"begin", "", hit, flags=re.IGNORECASE)
                hit = re.sub(r"\(", "", hit, flags=re.IGNORECASE)
                hit = re.sub(r"\)", "", hit, flags=re.IGNORECASE)
                hit = re.sub(r" or ", "", hit, flags=re.IGNORECASE)
                hit = re.sub(r" and ", "", hit, flags=re.IGNORECASE)
                hit = re.sub(r"posedge ", "", hit, flags=re.IGNORECASE)
                hit = re.sub(r"negedge ", "", hit, flags=re.IGNORECASE)
                hit = re.sub(r"\*", "", hit, flags=re.IGNORECASE)
                CustomText.read_variables_of_all_windows[self] += hit.split()
            else:
                break
        return text

    def highlight_item(self, _hdl_item_type: str, _object_identifier: str, number_of_line: int) -> None:
        self.tag_add("highlight", str(number_of_line) + ".0", str(number_of_line + 1) + ".0")
        # self.tag_config("highlight", background="#e9e9e9")
        self.tag_config("highlight", background="orange")
        self.see(str(number_of_line) + ".0")
        self.focus_set()


class ConditionCustomText(CustomText):
    """Wrapper for CustomText that provides a condition_text attribute."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.condition_text: Optional[str] = None


class ActionCustomText(CustomText):
    """Wrapper for CustomText that provides an action_text attribute."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.action_text: Optional[str] = None


class TextAfterCustomText(CustomText):
    """Wrapper for CustomText that provides a text_after_content attribute."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.text_after_content: Optional[str] = None


class TextBeforeCustomText(CustomText):
    """Wrapper for CustomText that provides a text_before_content attribute."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.text_before_content: Optional[str] = None
