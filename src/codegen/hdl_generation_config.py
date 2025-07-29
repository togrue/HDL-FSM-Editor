"""
Configuration class for HDL generation settings
"""

from pathlib import Path
from typing import Optional


class GenerationConfig:
    """Configuration for HDL code generation"""

    def __init__(self) -> None:
        # Core generation settings
        self.language: str = "VHDL"  # "VHDL", "Verilog", "SystemVerilog"
        self.module_name: str = ""
        self.generate_path: str = ""
        self.select_file_number: int = 1  # 1 or 2 files (VHDL only)
        self.include_timestamp: bool = False

        # Signal names
        self.clock_signal_name: str = ""
        self.reset_signal_name: str = ""

        # Code style
        self.indentation: str = "    "  # 4 spaces

        self.write_to_file: bool = False

    @classmethod
    def from_main_window(cls) -> "GenerationConfig":
        """Create a GenerationConfig instance from main_window settings"""
        import main_window

        config = cls()
        config.language = main_window.language.get()
        config.module_name = main_window.module_name.get()
        config.generate_path = main_window.generate_path_value.get()
        config.select_file_number = main_window.select_file_number_text.get()
        config.include_timestamp = main_window.include_timestamp_in_output.get()
        config.clock_signal_name = main_window.clock_signal_name.get()
        config.reset_signal_name = main_window.reset_signal_name.get()

        return config

    def get_comment_style(self) -> str:
        """Get the appropriate comment style for the current language"""
        if self.language == "VHDL":
            return "--"
        else:  # Verilog, SystemVerilog
            return "//"

    def get_file_extension(self) -> str:
        """Get the appropriate file extension for the current language"""
        if self.language == "VHDL":
            return ".vhd"
        elif self.language == "Verilog":
            return ".v"
        elif self.language == "SystemVerilog":
            return ".sv"
        else:
            raise ValueError(f"Unsupported language: {self.language}")

    def get_output_files(self) -> list[str]:
        """
        Get the list of output file paths based on language and file count settings.
        Returns a list of file paths that will be generated.
        """
        if not self.module_name or not self.generate_path:
            return []

        # For Verilog and SystemVerilog, always generate single files
        if self.language in ["Verilog", "SystemVerilog"]:
            extension = self.get_file_extension()
            return [f"{self.generate_path}/{self.module_name}{extension}"]

        # For VHDL, check file count setting
        if self.select_file_number == 1:
            # Single file
            return [f"{self.generate_path}/{self.module_name}.vhd"]
        else:
            # Two files: entity and architecture
            return [
                f"{self.generate_path}/{self.module_name}_e.vhd",
                f"{self.generate_path}/{self.module_name}_fsm.vhd",
            ]

    def get_primary_file(self) -> Optional[str]:
        """Get the primary output file path (first file in the list)"""
        files = self.get_output_files()
        return files[0] if files else None

    def get_architecture_file(self) -> Optional[str]:
        """Get the architecture file path (for VHDL two-file mode)"""
        files = self.get_output_files()
        return files[1] if len(files) > 1 else None

    def validate(self) -> list[str]:
        """
        Validate the configuration and return a list of error messages.
        Returns empty list if configuration is valid.
        """
        errors = []

        if not self.module_name or self.module_name.isspace():
            errors.append("No module name is specified")

        if not self.generate_path or self.generate_path.isspace():
            errors.append("No output path is specified")
        else:
            path = Path(self.generate_path)
            if not path.exists():
                errors.append(f"Output path does not exist: {self.generate_path}")

        if not self.reset_signal_name or self.reset_signal_name.isspace():
            errors.append("No reset signal name is specified")

        if not self.clock_signal_name or self.clock_signal_name.isspace():
            errors.append("No clock signal name is specified")

        if self.language not in ["VHDL", "Verilog", "SystemVerilog"]:
            errors.append(f"Unsupported language: {self.language}")

        if self.select_file_number not in [1, 2]:
            errors.append(f"Invalid file number setting: {self.select_file_number}")

        return errors

    def is_valid(self) -> bool:
        """Check if the configuration is valid"""
        return len(self.validate()) == 0
