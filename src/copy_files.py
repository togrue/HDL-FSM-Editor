#!/usr/bin/env python3
"""
Script to copy all Python source files to the src/hdl_fsm_editor directory.
"""

import os
import shutil

# List of all Python files to copy (excluding the copy script itself)
python_files = [
    "canvas_editing.py",
    "canvas_modify_bindings.py",
    "color_changer.py",
    "compile_handling.py",
    "condition_action_handling.py",
    "connector_handling.py",
    "custom_text.py",
    "file_handling.py",
    "global_actions.py",
    "global_actions_combinatorial.py",
    "global_actions_handling.py",
    "grid_drawing.py",
    "hdl_generation.py",
    "hdl_generation_architecture.py",
    "hdl_generation_architecture_state_actions.py",
    "hdl_generation_architecture_state_sequence.py",
    "hdl_generation_library.py",
    "hdl_generation_module.py",
    "link_dictionary.py",
    "linting.py",
    "list_separation_check.py",
    "main_window.py",
    "move_handling.py",
    "move_handling_finish.py",
    "move_handling_initialization.py",
    "OptionMenu.py",
    "reset_entry_handling.py",
    "state_action_handling.py",
    "state_actions_default.py",
    "state_comment.py",
    "state_handling.py",
    "tag_plausibility.py",
    "transition_handling.py",
    "undo_handling.py",
    "update_hdl_tab.py",
    "vector_handling.py",
]

# Create src directory if it doesn't exist
src_dir = "src/hdl_fsm_editor"
os.makedirs(src_dir, exist_ok=True)

# Copy each file
for file in python_files:
    if os.path.exists(file):
        shutil.copy2(file, os.path.join(src_dir, file))
        print(f"Copied {file}")
    else:
        print(f"Warning: {file} not found")

print("All files copied successfully!")
