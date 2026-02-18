"""
Pure HDL text parsing helpers shared by UI and code generation.
"""

import re

from project_manager import project_manager

BLOCK_COMMENT_RE = re.compile(r"\/\*.*?\*\/", flags=re.DOTALL)


def remove_comments_and_returns(hdl_text) -> str:
    """Strip block and line comments, normalize to space-separated string for keyword search."""
    if project_manager.language.get() == "VHDL":
        hdl_text = remove_vhdl_block_comments(hdl_text)
    else:
        hdl_text = _remove_verilog_block_comments(hdl_text)
    lines_without_return = hdl_text.split("\n")
    text = ""
    for line in lines_without_return:
        if project_manager.language.get() != "VHDL":
            line_without_comment = re.sub("//.*$", "", line)
        else:
            line_without_comment = re.sub("--.*$", "", line)
        # Add " " at the beginning of the line. Then it is possible to search for keywords
        # surrounded by blanks also at the beginning of text:
        text += " " + line_without_comment
    text += " "  # Add " " at the end, so that keywords at the end are also surrounded by blanks.
    return text


def remove_functions(hdl_text):
    """Remove VHDL/Verilog function declarations from text for signal/constant parsing."""
    text = re.sub(
        r"(^|\s+)function\s+.*end(\s+function\s*;|function)", "", hdl_text
    )  # Regular expression for VHDL and Verilog function declaration
    return text


def remove_type_declarations(hdl_text):
    """Remove VHDL type declarations from text for signal/constant parsing."""
    text = re.sub(
        r"(^|\s+)type\s+\w+\s+is\s+.*;", "", hdl_text
    )  # Regular expression for VHDL and Verilog type declaration
    return text


def remove_vhdl_block_comments(list_string):
    """Replace /* ... */ block comments with spaces to preserve character positions."""
    # block comments are replaced by blanks, so all remaining text holds its position.
    while True:
        match_object = BLOCK_COMMENT_RE.search(list_string)
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
    """Remove comments and surround operators/punctuation with spaces for regex/keyword search."""
    without_comments = remove_comments_and_returns(text)
    separated = surround_character_by_blanks(";", without_comments)
    separated = surround_character_by_blanks("(", separated)
    separated = surround_character_by_blanks(")", separated)
    separated = surround_character_by_blanks(":", separated)
    separated = surround_character_by_blanks("!=", separated)
    separated = surround_character_by_blanks("!", separated)
    separated = surround_character_by_blanks("/", separated)
    separated = surround_character_by_blanks("=", separated)
    separated = surround_character_by_blanks(">", separated)
    separated = surround_character_by_blanks("<", separated)
    separated = surround_character_by_blanks(",", separated)
    separated = surround_character_by_blanks("'", separated)
    separated = surround_character_by_blanks("+", separated)
    separated = surround_character_by_blanks("-", separated)
    separated = surround_character_by_blanks("*", separated)
    separated = re.sub("<  =", "<=", separated)  # restore this operator (assignment or comparison)
    separated = re.sub(">  =", ">=", separated)  # restore this operator (comparison)
    separated = re.sub("=  >", "=>", separated)  # restore this operator (when selector in VHDL)
    separated = re.sub("=  =", "==", separated)  # restore this operator (comparison)
    separated = re.sub("/  =", "/=", separated)  # restore this operator (comparison)
    separated = re.sub(":  =", ":=", separated)  # restore this operator (assignment)
    separated = re.sub("!  =", "!=", separated)  # restore this operator (comparison)
    return separated


def surround_character_by_blanks(character, all_port_declarations_without_comments):
    """Replace each occurrence of character with ' character ' in the string."""
    # Add the escape character if necessary:
    search_character = "\\" + character if character in ("(", ")", "+", "*") else character
    return re.sub(search_character, " " + character + " ", all_port_declarations_without_comments)


def get_all_declared_signal_and_variable_names(all_signal_declarations) -> list:
    """Parse semicolon-separated declarations and return list of signal/variable names."""
    signal_declaration_list = all_signal_declarations.split(";")
    signal_list = []
    for declaration in signal_declaration_list:
        if declaration != "" and not declaration.isspace():
            declaration = (
                " " + declaration + " "
            )  # Splitting may have produced declarations without blanks but they are needed for keyword search.
            signals = _get_all_signal_names(declaration)
            if signals != "":
                signal_list.extend(signals.split(","))
    return signal_list


def get_all_declared_constant_names(all_signal_declarations) -> list:
    """Parse semicolon-separated declarations and return list of constant names."""
    signal_declaration_list = all_signal_declarations.split(";")
    constant_list = []
    for declaration in signal_declaration_list:
        if declaration != "" and not declaration.isspace():
            constants = _get_all_constant_names(declaration)
            if constants != "":
                constant_list.extend(constants.split(","))
    return constant_list


def _get_all_signal_names(declaration):
    signal_names = ""
    if " signal " in declaration and project_manager.language.get() == "VHDL":
        if ":" in declaration:
            signal_names = re.sub(":.*", "", declaration)
            signal_names = re.sub(" signal ", "", signal_names)
    elif " variable " in declaration and project_manager.language.get() == "VHDL":
        if ":" in declaration:
            signal_names = re.sub(":.*", "", declaration)
            signal_names = re.sub(" variable ", "", signal_names)
    elif project_manager.language.get() != "VHDL":
        declaration = re.sub(" integer ", " ", declaration, flags=re.I)
        declaration = re.sub(" logic ", " ", declaration, flags=re.I)
        declaration = re.sub(" reg ", " ", declaration, flags=re.I)
        signal_names = re.sub(" \\[.*?\\] ", " ", declaration)
    signal_names_without_blanks = re.sub(" ", "", signal_names)
    return signal_names_without_blanks


def _get_all_constant_names(declaration):
    constant_names = ""
    if " constant " in declaration and project_manager.language.get() == "VHDL" and ":" in declaration:
        constant_names = re.sub(":.*", "", declaration)
        constant_names = re.sub(" constant ", "", constant_names)
    if " localparam " in declaration and project_manager.language.get() != "VHDL":
        declaration = re.sub(" localparam ", " ", declaration, flags=re.I)
        constant_names = re.sub(" \\[.*?\\] ", " ", declaration)
    constant_names_without_blanks = re.sub(" ", "", constant_names)
    return constant_names_without_blanks
