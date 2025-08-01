# HDL-FSM-Editor
A tool for modeling FSMs by VHDL or Verilog.

Please visit [HDL-FSM-Editor](http://www.hdl-fsm-editor.de) for more information.

## Quick Start

Clone the repository and run:
```bash
python src/main.py
```

## Development

### Setup
Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and run:
```bash
uv sync --dev
```

To find out how to build a full executable of the application, run:
```bash
uv run release_script.py --help
```

### VSCode Setup
For the best development experience, install these VSCode extensions:
- **Python** - Official Python extension
- **Ruff** - Fast Python linter and formatter

**Ensure to select the virtual environment** (`.venv`) created by uv for the full development experience.
Press `Ctrl+Shift+P` and select `Python: Select Interpreter` to select the virtual environment.

