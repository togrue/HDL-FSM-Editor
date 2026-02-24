"""
Build GenerationConfig from UI (project_manager) or from design_data + project_manager (script mode).

Codegen only receives GenerationConfig instances; it does not build them.
"""

from codegen.hdl_generation_config import GenerationConfig
from design_data import DesignData
from project_manager import project_manager


def build_config_from_main_window() -> GenerationConfig:
    """Create a GenerationConfig from main window / project_manager settings (GUI)."""
    config = GenerationConfig()
    config.language = project_manager.language.get()
    config.module_name = project_manager.module_name.get()
    config.generate_path = project_manager.generate_path_value.get()
    config.select_file_number = project_manager.select_file_number_text.get()
    config.include_timestamp = project_manager.include_timestamp_in_output.get()
    config.clock_signal_name = project_manager.clock_signal_name.get()
    config.reset_signal_name = project_manager.reset_signal_name.get()
    return config


def build_config_for_script_mode(design_data: DesignData) -> GenerationConfig:
    """Create a GenerationConfig for script mode: design_data for module/language/signals, project_manager for paths."""
    config = GenerationConfig()
    config.language = design_data.language
    config.module_name = design_data.module_name
    config.reset_signal_name = design_data.reset_signal_name
    config.clock_signal_name = design_data.clock_signal_name
    config.generate_path = project_manager.generate_path_value.get()
    config.select_file_number = project_manager.select_file_number_text.get()
    config.include_timestamp = project_manager.include_timestamp_in_output.get()
    return config
