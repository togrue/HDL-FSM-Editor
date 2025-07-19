# HDL-FSM-Editor Test Suite

This directory contains automated tests for HDL-FSM-Editor.

## Structure

- `test_golden_file_generation.py`: Golden file tests (generates HDL from .hfe and checks output)
- `conftest.py`: Pytest config and fixtures
- `test_output/`: Output directory for generated files

## Running Tests

- Run all tests:
  `pytest`

- Run only golden file tests:
  `pytest -m golden_file`

- Run only batch mode tests:
  `pytest -m batch_mode`

- Verbose output:
  `pytest -v`

- Run a specific test:
  `pytest tests/test_golden_file_generation.py`

## Test Types

- **Golden File Tests:**
  Generate HDL from `.hfe` files in `examples/` and compare with expected output (ignoring timestamps).

- **Batch Mode Tests:**
  Check batch mode operation, reproducible output (no timestamps), and correct headers.

## Adding Tests

1. Add new test files with `test_` prefix.
2. Use pytest markers (`@pytest.mark.golden_file`, `@pytest.mark.batch_mode`).
3. Place new `.hfe` files in `examples/`.
4. Add matching golden HDL files in `examples/` (no timestamps).

## Output

Generated files are placed in `tests/test_output/` to keep the repo clean.