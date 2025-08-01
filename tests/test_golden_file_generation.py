"""
Golden file tests for HDL-FSM-Editor.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

# This provides additional parameters for the test.
# Files have to be specified here only if they are non-standard.
# - Which stdout is expected. (to match against warnings / generation errors).
# - If the generation is expected to succeed.
TEST_CONFIGURATION = {
    "fifo_test_error.hfe": {
        "generation_should_succeed": False,
        "validation_patterns": [
            "A transition starting at state S1\nwith no condition hides a transition with lower priority.",
        ],
    },
}


def read_hfe_metadata(hfe_file: Path) -> dict[str, Any]:
    """Read language and module name from HFE file."""
    with open(hfe_file, encoding="utf-8") as f:
        data = json.load(f)
    return {
        "language": data.get("language", "VHDL"),
        "module_name": data.get("modulename", ""),
        "number_of_files": data.get("number_of_files", 1),
    }


def get_output_file_names(hfe_file: Path, output_dir: Path) -> list[Path]:
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


def run_hdl_generation(hfe_file: Path, output_dir: Path) -> subprocess.CompletedProcess:
    """Run HDL-FSM-Editor to generate HDL from .hfe file."""
    # Note: we have to ensure that the tests don't overwrite files of other tests.
    # This is currently not checked. So ensure that all modules have a unique module name!
    output_dir.mkdir(parents=True, exist_ok=True)
    original_cwd = os.getcwd()
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


def collect_hfe_test_cases() -> list[tuple[str, Path]]:
    """Collect all HFE files and create test cases."""
    examples_dir = Path(__file__).parent / "test_input"
    hfe_files = list(examples_dir.glob("*.hfe"))
    if not hfe_files:
        pytest.skip("No .hfe files found in examples directory")

    return [(hfe_file.stem, hfe_file) for hfe_file in hfe_files]


@pytest.mark.golden_file
@pytest.mark.parametrize("test_id, hfe_file", collect_hfe_test_cases())
def test_golden_file_generation(test_id: str, hfe_file: Path, test_output_dir: Path):
    """Test HDL generation for individual HFE files.

    Handles both successful generation and expected validation failures.
    """
    print(f"\nTesting {hfe_file.name}")

    # Get test configuration
    config = TEST_CONFIGURATION.get(hfe_file.name)
    should_succeed = config is None or config.get("generation_should_succeed", True)
    validation_patterns = config.get("validation_patterns", []) if config else []

    print(f"  Expected success: {should_succeed}")
    if validation_patterns:
        print(f"  Expected validation patterns: {validation_patterns}")

    # Get expected output files
    metadata = read_hfe_metadata(hfe_file)
    output_files = get_output_file_names(hfe_file, test_output_dir)

    print(f"  Language: {metadata['language']}")
    print(f"  Module: {metadata['module_name']}")
    print(f"  Output files: {[f.name for f in output_files]}")

    # Record modification times before generation
    before_times = {
        output_file: output_file.stat().st_mtime if output_file.exists() else 0 for output_file in output_files
    }

    # Generate HDL
    result = run_hdl_generation(hfe_file, test_output_dir)

    # Check output patterns regardless of success/failure
    if validation_patterns:
        output_text = result.stdout + result.stderr
        for pattern in validation_patterns:
            match = re.search(re.escape(pattern), output_text, re.IGNORECASE)
            assert match is not None, f"Expected validation pattern '{pattern}' not found in output:\n{output_text}"
            print(f"  ✓ Found validation pattern (regex): {pattern}")

    if should_succeed:
        # Test successful generation
        assert result.returncode == 0, f"Generation failed: {result.stderr}"

        # Check each output file was created and modified
        for output_file in output_files:
            assert output_file.exists(), f"Output file not generated: {output_file}"

            after_time = output_file.stat().st_mtime
            was_modified = after_time > before_times[output_file]

            print(f"  {output_file.name}: modified = {was_modified}")
            assert was_modified, f"File {output_file.name} was not modified during generation"

    else:
        # Test expected validation failure
        assert result.returncode != 0, "Expected validation failure but generation succeeded"

        # Verify no output files were modified
        for output_file in output_files:
            if output_file.exists():
                after_time = output_file.stat().st_mtime
                was_modified = after_time > before_times[output_file]

                if was_modified:
                    print(f"  ⚠️  Warning: {output_file.name} was modified despite validation failure")


if __name__ == "__main__":
    pytest.main([__file__])
