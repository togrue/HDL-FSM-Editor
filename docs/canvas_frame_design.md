# CanvasFrame Design Document

## Overview
A selectable, movable base class for canvas elements that provides intuitive user interactions through a simplified state machine and unified selection management.

## Core User Experience

### Selection & Movement
- **Click to select**: Single-click selects frame (clears others)
- **Ctrl+Click to toggle**: Add/remove from multi-selection
- **Click-and-drag**: Immediate movement (no separate drag mode)
- **Click outside**: Clear all selections

### Visual Feedback
- **NORMAL**: Default appearance, no border
- **HOVERED**: Light blue border (1px) - indicates interactivity
- **SELECTED**: Dark blue border (2px) + light blue background - clear selection indicator

## Simplified State Machine

### States
1. **NORMAL** - Default inactive state
2. **HOVERED** - Mouse over frame (subtle highlight)
3. **SELECTED** - Frame is selected (clear visual indication)

### State Transitions
```
NORMAL
  ├─ Mouse Enter → HOVERED
  └─ Click → SELECTED

HOVERED
  ├─ Mouse Leave → NORMAL
  ├─ Click (no Ctrl) → SELECTED (clear others)
  └─ Click (Ctrl) → SELECTED (add to selection)

SELECTED
  ├─ Click Outside → NORMAL (clear selection)
  ├─ Click (Ctrl) → NORMAL (remove from selection)
  └─ Mouse Enter → SELECTED (stay selected)
```

## Key Design Decisions

### Why No MOVING State?
- **Simpler**: SELECTED frames can be dragged immediately
- **Intuitive**: No mode switching required
- **Consistent**: Same visual feedback during drag

### Why No FOCUSED State?
- **Redundant**: Text editing works within SELECTED state
- **Cleaner**: Fewer state transitions to manage
- **Standard**: Most applications don't separate selection and focus

### Immediate Drag Behavior
- **Natural**: Click and drag starts movement immediately
- **Efficient**: No separate drag initiation step
- **Familiar**: Matches common UI patterns

## Implementation

### Core Methods
```python
class CanvasFrame(ttk.Frame):
    # Global state
    _selected_frames: set['CanvasFrame'] = set()

    def _on_frame_click(self, event: tk.Event) -> None:
        # Handle selection + start drag immediately

    def _on_drag(self, event: tk.Event) -> None:
        # Update position during drag

    def _on_drag_end(self, event: tk.Event) -> None:
        # Complete drag operation
```

### Visual Styling
```python
def _apply_style(self, state: FrameState) -> None:
    if state == FrameState.NORMAL:
        self.configure(relief=tk.FLAT, borderwidth=0)
    elif state == FrameState.HOVERED:
        self.configure(relief=tk.RAISED, borderwidth=1,
                      highlightcolor="#4A90E2")
    elif state == FrameState.SELECTED:
        self.configure(relief=tk.RAISED, borderwidth=2,
                      highlightcolor="#2E5BBA",
                      background="#E3F2FD")
```

## Migration Benefits

### For Users
- **Faster workflow**: Immediate drag behavior
- **Clearer feedback**: Obvious visual states
- **Consistent behavior**: Same patterns across all frames

### For Developers
- **Simpler code**: Fewer states to manage
- **Easier testing**: Less complex state transitions
- **Better maintainability**: Clear separation of concerns

## Testing Focus

### Critical User Flows
1. **Single selection**: Click frame → drag to move
2. **Multi-selection**: Ctrl+Click frames → drag any to move all
3. **Clear selection**: Click empty canvas
4. **Visual feedback**: Verify hover and selection states

### Edge Cases
- **Rapid clicking**: Ensure state consistency
- **Drag cancellation**: Escape key during drag
- **Canvas boundaries**: Prevent moving outside canvas

This simplified design eliminates unnecessary complexity while maintaining all essential functionality for an intuitive user experience.