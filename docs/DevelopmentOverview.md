# HDL-FSM-Editor Architecture Guide

## Overview

The HDL-FSM-Editor is a graphical tool for designing Finite State Machines (FSMs) and generating Hardware Description Language (HDL) code in VHDL, Verilog, or SystemVerilog. The application uses a multi-tab interface built on tkinter, with a canvas-based diagram editor for visual FSM design and integrated code generation capabilities.

The application follows a traditional GUI architecture where the main window coordinates various specialized modules for different aspects of FSM design and HDL generation.

## Core Components

### Main Window (`src/main_window.py`)

The central hub that orchestrates all application components:

- **Global Variables**: Stores all UI widget references and application state
- **Tab Management**: Creates and manages the notebook interface with 6 tabs:
  - Control: Project settings and configuration
  - Interface: VHDL packages, generics/parameters, and ports
  - Internals: Internal declarations and variable definitions
  - Diagram: Visual FSM editor with canvas
  - Generated HDL: Displays generated code with hyperlinks
  - Compile Messages: Compilation output with error navigation

Key functions:
- `create_root()`: Initializes the main tkinter window
- `create_notebook()`: Sets up the tabbed interface
- `switch_language_mode()`: Adapts UI for VHDL vs Verilog/SystemVerilog

### Canvas Editing System (`src/canvas_editing.py`)

Manages the visual diagram editor:

- **Canvas Operations**: Zoom, pan, view controls, and grid management
- **Mouse Handling**: Tracks cursor position and coordinates
- **Visual Elements**: States (circles), transitions (lines), connectors, and text windows
- **Font Management**: Handles text rendering for state names and labels

Key functions:
- `store_mouse_position()`: Tracks mouse coordinates for editing operations
- `view_all()`: Fits entire diagram in view
- `zoom_plus()/zoom_minus()`: Zoom controls

### State Management (`src/state_handling.py`)

Handles FSM state creation and manipulation:

- **State Creation**: Creates circular state elements with labels
- **State Movement**: Drag-and-drop functionality for repositioning
- **State Properties**: Name editing and visual feedback
- **Menu System**: Right-click context menus for state operations

Key functions:
- `insert_state()`: Creates new state elements
- `move_to()`: Handles state repositioning
- `edit_state_name()`: In-place state name editing

### Transition System (`src/transition_handling.py`)

Manages connections between states:

- **Transition Creation**: Draws lines between states
- **Condition Handling**: Manages transition conditions and actions
- **Priority System**: Handles multiple transitions from same state
- **Visual Feedback**: Hover effects and selection highlighting

### Movement Handling (`src/move_handling_*.py`)

Complex multi-phase movement system:

- **Initialization** (`move_handling_initialization.py`): Detects clickable objects and creates move lists
- **Core Movement** (`move_handling.py`): Handles continuous dragging operations
- **Finalization** (`move_handling_finish.py`): Completes moves and updates connections

The system automatically includes connected transitions when moving states.

### Editing Modes (`src/canvas_modify_bindings.py`)

Manages different interaction modes:

- **Move Mode**: Default mode for selecting and moving elements
- **State Insertion**: Click to create new states
- **Transition Insertion**: Click to create transitions between states
- **Connector Insertion**: Add connection points
- **Action Windows**: Insert state action or global action windows

Mode switching is handled through button clicks and escape key.

### Code Generation (`src/codegen/`)

Multi-module HDL generation system:

- **Configuration** (`hdl_generation_config.py`): Settings for language, file count, paths
- **Library** (`hdl_generation_library.py`): Core data structures and utilities
- **Module Logic** (`hdl_generation_module.py`): Main generation orchestration
- **State Sequence** (`hdl_generation_architecture_state_sequence.py`): FSM state machine logic
- **State Actions** (`hdl_generation_architecture_state_actions.py`): Action generation

Supports:
- VHDL: Single file or separate entity/architecture files
- Verilog/SystemVerilog: Single module file
- Customizable signal names and compilation commands

### Linking System (`src/link_dictionary.py`)

Bidirectional navigation between HDL code and GUI elements:

- **Link Creation**: Maps HDL line numbers to GUI widgets during code generation
- **Navigation**: Click on HDL lines to jump to source GUI elements
- **Error Navigation**: Click on compilation errors to locate source
- **Tab Integration**: Works across all tabs (Interface, Internals, Diagram)

Key functions:
- `add()`: Creates links during HDL generation
- `jump_to_source()`: Navigates from HDL to GUI
- `jump_to_hdl()`: Navigates from GUI to HDL

### File Handling (`src/file_handling.py`)

Project persistence and management:

- **Save/Load**: JSON-based project file format
- **Canvas Serialization**: Saves all visual elements (states, transitions, text windows)
- **Text Content**: Preserves all text widget contents
- **Version Compatibility**: Supports loading older file formats

### Undo/Redo System (`src/undo_handling.py`)

Comprehensive change tracking:

- **Design Changes**: Tracks modifications to enable undo/redo
- **Window Title**: Updates title with asterisk for unsaved changes
- **State Management**: Coordinates with canvas editing operations

### Custom Text Widgets (`src/custom_text.py`)

Enhanced text editing with syntax highlighting:

- **Language Support**: VHDL, Verilog, SystemVerilog syntax highlighting
- **Undo/Redo**: Built-in undo/redo functionality
- **Validation**: Port/generic declaration validation
- **Integration**: Works with linking system for navigation

## Data Flow

1. **User Input**: Mouse clicks and keyboard input captured by canvas and text widgets
2. **Mode Handling**: `canvas_modify_bindings` determines current editing mode
3. **Element Creation**: Specialized handlers create states, transitions, or text windows
4. **State Updates**: Global variables in `main_window` track all application state
5. **Code Generation**: HDL generation reads GUI state and produces code
6. **Linking**: Link dictionary maps generated code lines to source GUI elements
7. **Persistence**: File handling saves/loads complete project state

## Key Design Patterns

- **Global State**: Application state stored in `main_window` module variables
- **Event-Driven**: tkinter event system drives all user interactions
- **Modular Architecture**: Separate modules for different concerns (states, transitions, codegen)
- **Bidirectional Linking**: Seamless navigation between visual design and generated code
- **Multi-Language Support**: Single codebase supports multiple HDL languages

## File Structure

```
src/
├── main_window.py          # Main application window and coordination
├── canvas_editing.py      # Canvas operations and visual controls
├── state_handling.py      # FSM state management
├── transition_handling.py # Transition creation and management
├── move_handling_*.py     # Multi-phase movement system
├── canvas_modify_bindings.py # Editing mode management
├── codegen/               # HDL generation modules
├── file_handling.py       # Project persistence
├── undo_handling.py       # Change tracking
├── link_dictionary.py     # HDL-GUI navigation
└── custom_text.py         # Enhanced text widgets
```

This architecture enables rapid FSM design with immediate HDL code generation and seamless navigation between visual design and generated code.
