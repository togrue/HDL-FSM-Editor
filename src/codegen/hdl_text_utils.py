"""
Pure HDL text parsing helpers shared by UI and code generation.
"""

import re

from project_manager import project_manager

from .exceptions import GenerationError

BLOCK_COMMENT_RE = re.compile(r"\/\*.*?\*\/", flags=re.DOTALL)


def remove_comments_and_returns(hdl_text, language=None) -> str:
    """Strip block and line comments, normalize to space-separated string for keyword search."""
    if language is None:
        language = project_manager.language.get()
    hdl_text = _remove_vhdl_block_comments(hdl_text) if language == "VHDL" else _remove_verilog_block_comments(hdl_text)
    lines_without_return = hdl_text.split("\n")
    text = ""
    for line in lines_without_return:
        line_without_comment = re.sub("//.*$", "", line) if language != "VHDL" else re.sub("--.*$", "", line)
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


def _remove_vhdl_block_comments(list_string):
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


def convert_hdl_lines_into_a_searchable_string(text, language=None):
    """Remove comments and surround operators/punctuation with spaces for regex/keyword search."""
    without_comments = remove_comments_and_returns(text, language)
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


def get_all_declared_signal_and_variable_names(all_signal_declarations, language=None) -> list:
    """Parse semicolon-separated declarations and return list of signal/variable names."""
    if language is None:
        language = project_manager.language.get()
    signal_declaration_list = all_signal_declarations.split(";")
    signal_list = []
    for declaration in signal_declaration_list:
        if declaration != "" and not declaration.isspace():
            declaration = (
                " " + declaration + " "
            )  # Splitting may have produced declarations without blanks but they are needed for keyword search.
            signals = _get_all_signal_names(declaration, language)
            if signals != "":
                signal_list.extend(signals.split(","))
    return signal_list


def get_all_declared_constant_names(all_signal_declarations, language=None) -> list:
    """Parse semicolon-separated declarations and return list of constant names."""
    if language is None:
        language = project_manager.language.get()
    signal_declaration_list = all_signal_declarations.split(";")
    constant_list = []
    for declaration in signal_declaration_list:
        if declaration != "" and not declaration.isspace():
            constants = _get_all_constant_names(declaration, language)
            if constants != "":
                constant_list.extend(constants.split(","))
    return constant_list


def _get_all_signal_names(declaration, language=None):
    if language is None:
        language = project_manager.language.get()
    signal_names = ""
    if " signal " in declaration and language == "VHDL":
        if ":" in declaration:
            signal_names = re.sub(":.*", "", declaration)
            signal_names = re.sub(" signal ", "", signal_names)
    elif " variable " in declaration and language == "VHDL":
        if ":" in declaration:
            signal_names = re.sub(":.*", "", declaration)
            signal_names = re.sub(" variable ", "", signal_names)
    elif language != "VHDL":
        declaration = re.sub(" integer ", " ", declaration, flags=re.I)
        declaration = re.sub(" logic ", " ", declaration, flags=re.I)
        declaration = re.sub(" reg ", " ", declaration, flags=re.I)
        signal_names = re.sub(" \\[.*?\\] ", " ", declaration)
    signal_names_without_blanks = re.sub(" ", "", signal_names)
    return signal_names_without_blanks


def _get_all_constant_names(declaration, language=None):
    if language is None:
        language = project_manager.language.get()
    constant_names = ""
    if " constant " in declaration and language == "VHDL" and ":" in declaration:
        constant_names = re.sub(":.*", "", declaration)
        constant_names = re.sub(" constant ", "", constant_names)
    if " localparam " in declaration and language != "VHDL":
        declaration = re.sub(" localparam ", " ", declaration, flags=re.I)
        constant_names = re.sub(" \\[.*?\\] ", " ", declaration)
    constant_names_without_blanks = re.sub(" ", "", constant_names)
    return constant_names_without_blanks


def get_all_readable_ports(all_port_declarations, check, language=None) -> list:
    """Returns a list with the names of all readable ports.
    If check is True, an error is raised if an illegal port declaration is found.
    """
    if language is None:
        language = project_manager.language.get()
    port_declaration_list = _create_list_of_declarations(all_port_declarations, language)
    readable_port_list = []
    for declaration in port_declaration_list:
        if declaration != "" and not declaration.isspace():
            inputs = _get_all_readable_port_names(
                declaration, check, language
            )  # One declaration can contain a comma separated list of names!
            if inputs != "":
                readable_port_list.extend(inputs.split(","))
    return readable_port_list


def get_all_writable_ports(all_port_declarations, language=None) -> list:
    """Returns a list with the names of all writable ports."""
    if language is None:
        language = project_manager.language.get()
    port_declaration_list = _create_list_of_declarations(all_port_declarations, language)
    writeable_port_list = []
    for declaration in port_declaration_list:
        if declaration != "" and not declaration.isspace():
            outputs = _get_all_writable_port_names(declaration, language)
            if outputs != "":
                writeable_port_list.extend(outputs.split(","))
    return writeable_port_list


def get_all_port_types(all_port_declarations, language=None) -> list:
    """Returns a list with the type-names of all ports."""
    if language is None:
        language = project_manager.language.get()
    port_declaration_list = _create_list_of_declarations(all_port_declarations, language)
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


def get_all_generic_names(all_generic_declarations, language=None) -> list:
    """Returns a list with the names of all generics."""
    if language is None:
        language = project_manager.language.get()
    generic_declaration_list = _create_list_of_declarations(all_generic_declarations, language)
    generic_name_list = []
    for declaration in generic_declaration_list:
        if declaration != "" and not declaration.isspace():
            if language == "VHDL":
                generic_name = re.sub(" : .*", "", declaration, flags=re.I | re.DOTALL)
                generic_name = re.sub(r"(^|\s+)constant ", "", generic_name, flags=re.I | re.DOTALL)
                generic_name = re.sub("\\s", "", generic_name)
            else:  # Verilog
                generic_name = re.sub("=.*", "", declaration, flags=re.I | re.DOTALL)
                generic_name = re.sub("\\s", "", generic_name)
            generic_name_list.append(generic_name)
    return generic_name_list


def _create_list_of_declarations(all_declarations, language=None):
    if language is None:
        language = project_manager.language.get()
    all_declarations_without_comments = remove_comments_and_returns(all_declarations, language)
    all_declarations_separated = surround_character_by_blanks(
        ":", all_declarations_without_comments
    )  # only needed for VHDL
    split_char = ";" if language == "VHDL" else ","
    return all_declarations_separated.split(split_char)


def _get_all_readable_port_names(declaration, check, language=None) -> str:
    if language is None:
        language = project_manager.language.get()
    port_names = ""
    if " in " in declaration and language == "VHDL":
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
    elif " input " in declaration and language != "VHDL":
        declaration = re.sub(" input ", " ", declaration, flags=re.I)
        declaration = re.sub(" reg ", " ", declaration, flags=re.I)
        declaration = re.sub(" logic ", " ", declaration, flags=re.I)
        port_names = re.sub(" \\[.*?\\] ", " ", declaration)
    else:
        return ""
    port_names_without_blanks = re.sub(" ", "", port_names)
    return port_names_without_blanks


def _get_all_writable_port_names(declaration, language=None) -> str:
    if language is None:
        language = project_manager.language.get()
    port_names = ""
    if " out " in declaration and language == "VHDL":
        if ":" in declaration:
            port_names = re.sub(":.*", "", declaration)
    elif " output " in declaration and language != "VHDL":
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
