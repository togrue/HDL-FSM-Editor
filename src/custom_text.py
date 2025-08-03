"""
This code was copied (and extended) from https://stackoverflow.com/questions/40617515/python-tkinter-text-modified-callback
"""

import os
import re
import subprocess
import tkinter as tk
from tkinter import messagebox

import canvas_editing
import codegen.hdl_generation_architecture_state_actions as hdl_generation_architecture_state_actions
import codegen.hdl_generation_library as hdl_generation_library
import config
import constants
import file_handling
import linting
import main_window


class CustomText(tk.Text):
    read_variables_of_all_windows = {}
    written_variables_of_all_windows = {}

    def __init__(self, *args, text_type, **kwargs) -> None:
        """A text widget that report on internal widget commands"""
        tk.Text.__init__(
            self, *args, **kwargs
        )  # does not help: pady=5, pagdy is used to make sure that the undserscore line "_" is always visible at most font sizes.
        self.text_type = text_type
        # create a proxy for the underlying widget
        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)
        self.bind("<Tab>", lambda event: self.replace_tabs_by_blanks())
        # Overwrites the default control-e = "move cursor to end of line":
        self.bind("<Control-e>", lambda event: self.edit_in_external_editor())
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
        self.signals_list = []
        self.constants_list = []
        self.readable_ports_list = []
        self.writable_ports_list = []
        self.generics_list = []
        self.port_types_list = []
        CustomText.read_variables_of_all_windows[self] = []
        CustomText.written_variables_of_all_windows[self] = []
        self.tag_config("message_red", foreground="red")
        self.tag_config("message_green", foreground="green")

    def _open(self) -> str:
        file_handling.open_file()
        # Prevent a second call of open_file() by bind_all binding (which is located in entry 4 of the bind-list):
        return "break"

    def _proxy(self, command, *args) -> None:
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
        file_name = "hdl-fsm-editor.tmp.vhd" if main_window.language.get() == "VHDL" else "hdl-fsm-editor.tmp.v"
        with open(file_name, "w") as fileobject:
            fileobject.write(self.get("1.0", tk.END + "- 1 chars"))
        try:
            edit_cmd = main_window.edit_cmd.get().split()
            edit_cmd.append(file_name)
            process = subprocess.Popen(edit_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            messagebox.showerror("Error", "Error when running " + main_window.edit_cmd.get() + " " + file_name)
            return
        while True:
            poll = process.poll()
            if poll is not None:
                break
        with open(file_name) as fileobject:
            new_text = fileobject.read()
        os.remove(file_name)
        self.delete("1.0", tk.END)
        self.insert("1.0", new_text)
        self.format()

    def format_after_idle(self) -> None:
        self.after_idle(self.format)

    def format(self) -> None:
        text = self.get("1.0", tk.END)
        self.__update_size_of_text_box(text)
        self.__update_entry_of_this_window_in_list_of_read_and_written_variables_of_all_windows()
        self.update_highlighting()

    def __update_size_of_text_box(self, text) -> None:
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
        self.update_highlight_tags(canvas_editing.fontsize, ["control", "datatype", "function"])
        linting.recreate_keyword_list_of_unused_signals()
        linting.update_highlight_tags_in_all_windows_for_not_read_not_written_and_comment()

    def update_highlight_tags(self, fontsize, keyword_type_list) -> None:
        for keyword_type in keyword_type_list:
            self.tag_delete(keyword_type)
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
                    font=("Courier", int(fontsize), "normal"),
                )  # int() is necessary, because fontsize can be a "real" number.
            else:
                self.tag_configure(keyword_type, foreground=config.KEYWORD_COLORS[keyword_type], font=("Courier", 10))

    def add_highlight_tag_for_single_keyword(self, keyword_type, keyword) -> None:
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

    def replace_strings_and_attributes_by_blanks(self, copy_of_text):
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

    def remove_surrounding_characters_from_the_match(self, match_object, keyword) -> tuple:
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
        all_port_declarations = main_window.interface_ports_text.get("1.0", tk.END).lower()
        self.readable_ports_list = hdl_generation_architecture_state_actions.get_all_readable_ports(
            all_port_declarations, check=False
        )
        self.writable_ports_list = hdl_generation_architecture_state_actions.get_all_writable_ports(
            all_port_declarations
        )
        self.port_types_list = hdl_generation_architecture_state_actions.get_all_port_types(all_port_declarations)

    def update_custom_text_class_generics_list(self) -> None:
        all_generic_declarations = main_window.interface_generics_text.get("1.0", tk.END).lower()
        self.generics_list = hdl_generation_architecture_state_actions.get_all_generic_names(all_generic_declarations)

    def __update_entry_of_this_window_in_list_of_read_and_written_variables_of_all_windows(self) -> None:
        CustomText.read_variables_of_all_windows[self] = []
        CustomText.written_variables_of_all_windows[self] = []
        text = self.get("1.0", tk.END + "- 1 chars")
        text = hdl_generation_library.convert_hdl_lines_into_a_searchable_string(text)
        text = self.__remove_keywords(text)
        if main_window.language.get() == "VHDL":
            text = re.sub(r"\..*?\s", " ", text)  # remove all record-element-names from their signal/variable names
        if self.text_type == "condition":
            text = self.__remove_condition_keywords(text)
            CustomText.read_variables_of_all_windows[self] = text.split()
        elif self.text_type == "action":
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

    def __remove_keywords(self, text):
        if main_window.language.get() == "VHDL":
            text = self.__remove_keywords_from_vhdl(text)
        else:
            text = self.__remove_keywords_from_verilog(text)
        return text

    def __remove_keywords_from_vhdl(self, text):
        for keyword in constants.VHDL_KEYWORDS_FOR_SIGNAL_HANDLING + (
            " process.*?begin ",  # Remove complete process headers, if some exist.
            " end\\s+?process\\s*?;",  # remove end of process, before ...
            " process .*?$",  # ... when not complete process headers exist, remove until a return is found.
            " end\\s+?case\\s*?;",
            " end\\s+?if\\s*?;",
            " end\\s*?;",
            " end\\s*",
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
            "'.'",  # something like the std_logic value '1' or '0'
            '\\s"[0-9,a-f,A-F]+"',  # something like " 1234AB"
            '[^\\s]"[0-9,a-f,A-F]+"',  # something like X"1234"
        ):
            text = re.sub(keyword, "  ", text, flags=re.I)  # Keep the blanks the keyword is surrounded by.
        for keyword in constants.VHDL_KEYWORDS["datatype"]:
            text = re.sub(" " + keyword + " ", "  ", text, flags=re.I)  # Keep the blanks the keyword is surrounded by.
        return text

    def __remove_keywords_from_verilog(self, text):
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

    def __remove_condition_keywords(self, text):
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

    def __add_read_variables_from_with_select_blocks_to_read_variables_of_all_windows(self, text):
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

    def __add_read_variables_from_conditions_to_read_variables_of_all_windows(self, text):
        if main_window.language.get() == "VHDL":
            condition_search_pattern = "^if\\s+[^;]*?\\s+then| if\\s+[^;]*?\\s+then|elsif\\s+[^;]*?\\s+then|^when\\s+[^;]*?\\s+else| when\\s+[^;]*?\\s+else"
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

    def __add_read_variables_from_case_constructs_to_read_variables_of_all_windows(self, text):
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

    def __add_read_variables_from_assignments_to_read_variables_of_all_windows(self, text):
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

    def __add_read_variables_from_always_statements_to_read_variables_of_all_windows(self, text):
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

    def highlight_item(self, hdl_item_type, object_identifier, number_of_line) -> None:
        self.tag_add("highlight", str(number_of_line) + ".0", str(number_of_line + 1) + ".0")
        # self.tag_config("highlight", background="#e9e9e9")
        self.tag_config("highlight", background="orange")
        self.see(str(number_of_line) + ".0")
        self.focus_set()
