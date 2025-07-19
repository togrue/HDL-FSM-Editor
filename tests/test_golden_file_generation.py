"""
Golden file tests for HDL-FSM-Editor.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def read_hfe_metadata(hfe_file):
    """Read language and module name from HFE file."""
    with open(hfe_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {
        "language": data.get("language", "VHDL"),
        "module_name": data.get("modulename", ""),
        "number_of_files": data.get("number_of_files", 1),
    }


def get_output_file_names(hfe_file, output_dir):
    """Determine output file names based on HFE metadata."""
    metadata = read_hfe_metadata(hfe_file)
    module_name = metadata["module_name"]
    language = metadata["language"]
    number_of_files = metadata["number_of_files"]

    if language == "VHDL":
        if number_of_files == 1:
            return [output_dir / f"{module_name}.vhd"]
        else:
            return [output_dir / f"{module_name}_e.vhd", output_dir / f"{module_name}_fsm.vhd"]
    elif language == "Verilog":
        return [output_dir / f"{module_name}.v"]
    elif language == "SystemVerilog":
        return [output_dir / f"{module_name}.sv"]
    else:
        raise ValueError(f"Unsupported language: {language}")


def check_git_dirty(file_path):
    """Check if a file is marked as dirty by git."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain", str(file_path)], capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0 and result.stdout.strip() != ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def run_hdl_generation(hfe_file, output_dir):
    """Run HDL-FSM-Editor to generate HDL from .hfe file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    original_cwd = os.getcwd()
    # The FSMs have to specify "." as the output directory
    # Then they will end up in the test_output_dir; And can be compared.
    os.chdir(output_dir)

    try:
        cmd = [
            sys.executable,
            str(Path(__file__).parent.parent / "src" / "main.py"),
            str(hfe_file),
            "--generate-hdl",
            "--no-version-check",
            "--no-message",
        ]
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    finally:
        os.chdir(original_cwd)


@pytest.mark.golden_file
def test_golden_file_generation(examples_dir, test_output_dir):
    """Test HDL generation and check file status."""
    hfe_files = list(examples_dir.glob("*.hfe"))
    if not hfe_files:
        pytest.skip("No .hfe files found in examples directory")

    for hfe_file in hfe_files:
        print(f"\nTesting {hfe_file.name}")

        # Read HFE file and determine output files
        metadata = read_hfe_metadata(hfe_file)
        output_files = get_output_file_names(hfe_file, test_output_dir)

        print(f"  Language: {metadata['language']}")
        print(f"  Module: {metadata['module_name']}")
        print(f"  Output files: {[f.name for f in output_files]}")

        # Record modification times before generation
        before_times = {}
        for output_file in output_files:
            if output_file.exists():
                before_times[output_file] = output_file.stat().st_mtime
            else:
                before_times[output_file] = 0

        # Generate HDL
        result = run_hdl_generation(hfe_file, test_output_dir)
        assert result.returncode == 0, f"Generation failed: {result.stderr}"

        # Check each output file
        for output_file in output_files:
            assert output_file.exists(), f"Output file not generated: {output_file}"

            # Check git status
            is_dirty = check_git_dirty(output_file)
            print(f"  {output_file.name}: git dirty = {is_dirty}")
            assert not is_dirty, f"File {output_file.name} is dirty"

            # Check if file was modified by comparing timestamps
            after_time = output_file.stat().st_mtime
            before_time = before_times[output_file]
            was_modified = after_time > before_time

            print(f"  {output_file.name}: modified = {was_modified} (before: {before_time}, after: {after_time})")

            # Verify file was modified
            assert was_modified, f"File {output_file.name} was not modified during generation"


if __name__ == "__main__":
    pytest.main([__file__])
