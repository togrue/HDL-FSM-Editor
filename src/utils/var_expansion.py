"""
Variable expansion utilities for HDL-FSM-Editor.

This module provides functionality to expand bash-style variables in strings,
including environment variables and application-specific internal variables.
"""

import os
import re
from typing import Optional


def expand_variables(
    text: str,
    internal_vars: Optional[dict[str, str]] = None,
    error_on_missing: bool = False,
    use_environ: bool = True,
) -> str:
    """
    Expand bash-style variables in a string.

    Supports:
    - Environment variables: $VAR or ${VAR}
    - Internal variables: $file, $file1, $file2, $name, etc.
    - Default values: ${VAR:-default}

    Args:
        text: The input string containing variables to expand
        internal_vars: Dictionary of internal application variables
        error_on_missing: If True, raise KeyError for missing variables.
                         If False, leave unresolved variables as-is.
        use_environ: If True, include environment variables in expansion.
                    If False, only use internal_vars.

    Returns:
        String with variables expanded

    Raises:
        KeyError: If error_on_missing=True and a variable is not found
    """
    if internal_vars is None:
        internal_vars = {}

    # Combine environment variables with internal variables
    all_vars = {**os.environ, **internal_vars} if use_environ else internal_vars

    def replace_var(match: re.Match) -> str:
        """Replace a single variable match."""
        full_match: str = match.group(0)
        var_name: str = match.group(1)

        # Handle default value syntax: ${VAR:-default}
        if ":-" in var_name:
            var_name, default_value = var_name.split(":-", 1)
            if var_name in all_vars:
                return all_vars[var_name]
            else:
                return default_value

        # Regular variable expansion
        if var_name in all_vars:
            return all_vars[var_name]
        elif error_on_missing:
            raise KeyError(f"Variable '{var_name}' not found")
        else:
            # Leave unresolved variables as-is
            return full_match

    # Pattern to match $VAR or ${VAR} syntax
    # Supports: $var, ${var}, ${var:-default}
    pattern = r"\$\{([^}]+)\}|\$([a-zA-Z_][a-zA-Z0-9_]*)"

    return re.sub(pattern, replace_var, text)


def expand_variables_in_list(
    items: list[str],
    internal_vars: Optional[dict[str, str]] = None,
    error_on_missing: bool = False,
    use_environ: bool = True,
) -> list[str]:
    """
    Expand variables in each item of a list of strings.

    Args:
        items: List of strings to process
        internal_vars: Dictionary of internal application variables
        error_on_missing: If True, raise KeyError for missing variables
        use_environ: If True, include environment variables in expansion.
                    If False, only use internal_vars.

    Returns:
        List of strings with variables expanded

    Raises:
        KeyError: If error_on_missing=True and a variable is not found
    """
    return [expand_variables(item, internal_vars, error_on_missing, use_environ) for item in items]


def find_git_root(start_path: Optional[str] = None) -> Optional[str]:
    """
    Search upwards from start_path (or current working dir) for a .git directory or file.
    Returns the absolute path to the directory containing .git, or None if not found.
    """
    path = os.getcwd() if start_path is None else os.path.abspath(start_path)
    while True:
        git_path = os.path.join(path, ".git")
        if os.path.isdir(git_path) or os.path.isfile(git_path):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent
    return None


# TODO: introduce special variables
# like $git_root {which searches upwards for a .git directory or file}
# $hfe_dir {which is the directory of the FSM file}
# $cwd {which is the current working directory}
# $working_dir {which is the working directory}


# expansion tree:
# $module_name <- main_window.module_name.get()
# $hdl_ext <- .vhd if language is VHDL, .v if language is Verilog, .sv if language is SystemVerilog
# $gen_dir <- get_generate_dir()
# $file <- $gen_dir/$module_name$hdl_ext
# $file1 <- $gen_dir/${module_name}_e$hdl_ext
# $entity_file <- $file1
# $file2 <- $gen_dir/${module_name}_fsm$hdl_ext
# $architecture_file <- $file2
# $compile_cmd <- expand_variables(main_window.compile_cmd.get())
# $edit_file <-
# $edit_cmd <- expand_variables(main_window.edit_cmd.get())


def get_internal_variables() -> dict[str, str]:
    """
    Get the current internal variables from the main window.

    This function provides the same variables that _replace_variables uses,
    but returns them as a dictionary for use with expand_variables.

    Returns:
        Dictionary of internal variable names to their values
    """
    # Import here to avoid circular imports
    import main_window

    internal_vars = {}

    # Add module name
    internal_vars["name"] = main_window.module_name.get()

    # Add file variables based on current mode
    file_mode = main_window.select_file_number_text.get()
    language = main_window.language.get()

    # Determine file extension based on language
    if language == "VHDL":
        extension = ".vhd"
    elif language == "Verilog":
        extension = ".v"
    else:
        extension = ".sv"

    base_path = main_window.get_generation_dir()
    module_name = main_window.module_name.get()

    if file_mode == 1:
        # Single file mode
        internal_vars["file"] = f"{base_path}/{module_name}{extension}"
    else:
        # Two file mode
        internal_vars["file1"] = f"{base_path}/{module_name}_e{extension}"
        internal_vars["file2"] = f"{base_path}/{module_name}_fsm{extension}"

    return internal_vars
