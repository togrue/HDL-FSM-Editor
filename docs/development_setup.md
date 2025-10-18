# Development Setup

This guide will help you set up a complete development environment for HDL-FSM-Editor.

## Prerequisites

- **Python 3.9+** - Required for the application
- **Git** - For version control
- **VSCode** (recommended) - Primary development IDE

## Quick Setup

### 1. Install uv

Install [uv from astral.sh](https://docs.astral.sh/uv/getting-started/installation/) - a fast Python package manager.


### 2. Clone and Setup Environment

```bash
git clone <repository-url>
cd HDL-FSM-Editor
uv sync --dev
```

This command will:
- Create a virtual environment (`.venv`)
- Install all dependencies and development tools

### 3. Verify Installation

```bash
uv run python src/main.py --help
```

## VSCode Configuration

### Required Extensions

Install these VSCode extensions (they're auto-recommended when you open the project):

- **Python** (`ms-python.python`) - Official Python support
- **Ruff** (`charliermarsh.ruff`) - Fast linter and formatter

### Select Python Interpreter

**Critical:** Select the virtual environment created by uv:

1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
2. Type "Python: Select Interpreter"
3. Choose the `.venv` interpreter (should show `Python 3.x.x ('.venv': venv)`)

### Pre-configured Settings

The project includes VSCode settings that automatically:
- Enable Ruff for linting and formatting
- Format code on save
- Run tests with pytest
- Configure debugging profiles

## Development Tools

The project uses these development tools (installed automatically):

- **Ruff** - Fast Python linter and formatter
- **pytest** - Testing framework with parallel execution
- **mypy** - Static type checking
- **pylint** - Additional code analysis
- **pre-commit** - Git hooks for code quality

## Common Development Tasks

### Running the Application

```bash
# Run with example file
uv run python src/main.py examples/division_unsigned_control.hfe

# Run without arguments (opens empty editor)
uv run python src/main.py
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run tests in parallel (faster)
uv run pytest -n auto

```

### Code Quality Checks

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type checking
uv run mypy src

# Additional linting
uv run pylint src
```

### Building an executable

```bash
# Show build options
uv run release_script.py --help

# Create development build
uv run release_script.py --dev

# Create release build (requires clean git state)
uv run release_script.py --release
```

## Troubleshooting

### Python Interpreter Issues

**Problem:** VSCode not using the correct Python interpreter
**Solution:**
1. Press `Ctrl+Shift+P`
2. Select "Python: Select Interpreter"
3. Choose the `.venv` interpreter

### uv Command Not Found

**Problem:** `uv` command not recognized
**Solution:**
- Install uv (see [Quick Setup](#1-install-uv))
- Restart your terminal
- On Windows, restart PowerShell/Command Prompt
- Verify installation: `uv --version`

### Import Errors

**Problem:** Module import errors in VSCode
**Solution:**
1. Ensure correct Python interpreter is selected
2. Reload VSCode window (`Ctrl+Shift+P` → "Developer: Reload Window")
3. Check that `.venv` directory exists in project root

### Test Failures

**Problem:** Tests failing unexpectedly
**Solution:**
```bash
# Run tests with verbose output
uv run pytest -v

# Run single test for debugging
uv run pytest tests/test_specific.py::test_function -v
```

## Project Structure

```
HDL-FSM-Editor/
├── src/                   # Source code
├── tests/                 # Test files
├── examples/              # Example FSM files
├── docs/                  # Documentation
├── .vscode/               # VSCode configuration
├── pyproject.toml         # Project configuration
└── release_script.py      # Build script
```

## Getting Help

- Check the [main README](README.md) for general information
- Look at example files in `examples/` directory
- More state-machines can be found in the `tests/test_input` directory or on the [HDL-FSM-Editor website](http://www.hdl-fsm-editor.de/) (See 'Designs')
- Run `uv run python src/main.py --help` for command-line options