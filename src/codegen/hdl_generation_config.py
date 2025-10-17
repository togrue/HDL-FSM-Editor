"""
Configuration class for HDL generation settings
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class GenerationConfig:
    """Configuration for HDL code generation"""

    # Core generation settings
    language: str = "VHDL"  # "VHDL", "Verilog", "SystemVerilog"
    module_name: str = ""
    generate_path: Path = field(default_factory=Path)
    select_file_number: int = 1  # 1 or 2 files (VHDL only)
    include_timestamp: bool = False

    primary_file_path: Path = field(default_factory=Path)
    architecture_file_path: Optional[Path] = None

    # Signal names
    clock_signal_name: str = ""
    reset_signal_name: str = ""

    @classmethod
    def from_main_window(cls) -> "GenerationConfig":
        """Create a GenerationConfig instance from main_window settings"""
        import main_window

        return cls(
            language=main_window.language.get(),
            module_name=main_window.module_name.get(),
            generate_path=main_window.get_generation_dir(),
            select_file_number=main_window.select_file_number_text.get(),
            include_timestamp=main_window.include_timestamp_in_output.get(),
            primary_file_path=main_window.get_primary_file_path(),
            architecture_file_path=main_window.get_architecture_file_path(),
            clock_signal_name=main_window.clock_signal_name.get(),
            reset_signal_name=main_window.reset_signal_name.get(),
        )

    def validate(self) -> list[str]:
        """
        Validate the configuration and return a list of error messages.
        Returns empty list if configuration is valid.
        """
        errors = []

        if not self.module_name or self.module_name.isspace():
            errors.append("No module name is specified")

        if not self.generate_path:
            errors.append("No output path is specified")
        else:
            if not self.generate_path.exists():
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
