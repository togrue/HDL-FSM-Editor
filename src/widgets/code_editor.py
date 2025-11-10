"""
This module implements some extensions to the standard tkinter.Text widget.

Improvements:
- Better cursor movement and selection and deletion.
- Indent/unindent with brackets.

"""

import re
import tkinter as tk
from typing import Any, Callable


class CodeEditor(tk.Text):
    """
    A code editor widget that extends the standard tkinter.Text widget with word-wise cursor movement and selection.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # Word-wise cursor movement
        self.bind("<Control-Left>", lambda event: self.move_word_left())
        self.bind("<Control-Right>", lambda event: self.move_word_right())
        # Word selection
        self.bind("<Shift-Control-Left>", lambda event: self.select_word_left())
        self.bind("<Shift-Control-Right>", lambda event: self.select_word_right())
        # Handle normal selection (Shift+arrow) to fix anchor issues when switching
        # from word selection to normal selection
        self.bind("<Shift-Left>", lambda event: self._handle_normal_selection_left())
        self.bind("<Shift-Right>", lambda event: self._handle_normal_selection_right())
        # Reset anchor when using normal arrow keys (without Shift) to fix selection issues
        # when switching from word selection to normal selection
        self.bind("<Left>", lambda event: self._reset_anchor_if_no_selection())
        self.bind("<Right>", lambda event: self._reset_anchor_if_no_selection())
        self.bind("<Up>", lambda event: self._reset_anchor_if_no_selection())
        self.bind("<Down>", lambda event: self._reset_anchor_if_no_selection())
        # Whole word deletion
        self.bind("<Control-BackSpace>", lambda event: self.delete_word_backward())
        self.bind("<Control-Delete>", lambda event: self.delete_word_forward())
        # Indent/unindent with brackets
        self.bind("<Control-bracketleft>", lambda event: self.unindent_selection())
        self.bind("<Control-bracketright>", lambda event: self.indent_selection())


    def _handle_normal_selection(self, direction: str) -> str:
        """
        Handle Shift+Left or Shift+Right for normal character selection.
        `direction` should be "-1" for left and "+1" for right.
        Implements correct selection extension/contraction based on anchor position.
        """
        sel_ranges: tuple[str, ...] = self.tag_ranges(tk.SEL)  # type: ignore[assignment]
        anchor_pos = self.index(tk.ANCHOR)
        cursor_pos = self.index(tk.INSERT)

        # If no selection exists, set anchor to current cursor position
        if not sel_ranges:
            self.mark_set(tk.ANCHOR, cursor_pos)
            anchor_pos = cursor_pos

        # Move cursor one character to the left or right
        try:
            delta = "- 1 char" if direction == "left" else "+ 1 char"
            new_cursor_pos = self.index(f"{cursor_pos} {delta}")
        except tk.TclError:
            # Can't move (already at start or end)
            return "break"

        # Update cursor position
        self.mark_set(tk.INSERT, new_cursor_pos)

        # Update selection based on anchor and new cursor position
        if self.compare(anchor_pos, ">", new_cursor_pos):
            # anchor_pos > cursor_pos: selection from cursor to anchor
            sel_start, sel_end = new_cursor_pos, anchor_pos
        else:
            # anchor_pos <= cursor_pos: selection from anchor to cursor
            sel_start, sel_end = anchor_pos, new_cursor_pos

        # Update selection tag
        self.tag_remove(tk.SEL, "1.0", tk.END)
        if self.compare(sel_start, "!=", sel_end):
            self.tag_add(tk.SEL, sel_start, sel_end)

        return "break"  # Prevent default handler
    # Legacy shim methods for clarity and backward compatibility
    def _handle_normal_selection_left(self) -> str:
        """Handle Shift+Left for normal character selection."""
        return self._handle_normal_selection("left")

    def _handle_normal_selection_right(self) -> str:
        """Handle Shift+Right for normal character selection."""
        return self._handle_normal_selection("right")

    def _reset_anchor_if_no_selection(self) -> None:
        """Reset anchor to match cursor position when there's no active selection.
        This fixes issues when switching from word selection to normal selection.
        Uses after_idle to reset anchor after Tkinter's default cursor movement."""
        sel_ranges: tuple[str, ...] = self.tag_ranges(tk.SEL)  # type: ignore[assignment]
        if not sel_ranges:
            # Reset anchor after cursor moves (using after_idle ensures this happens
            # after Tkinter's default handler has moved the cursor)
            def reset_anchor() -> None:
                cursor_pos = self.index(tk.INSERT)
                self.mark_set(tk.ANCHOR, cursor_pos)

            self.after_idle(reset_anchor)

    def _move_cursor(self, find_boundary_func) -> str:
        """Generic cursor movement to token boundary."""
        current_pos = self.index(tk.INSERT)
        target_pos = find_boundary_func(current_pos)
        if not target_pos:
            return "break"

        # Clear any existing selection when moving cursor
        self.tag_remove(tk.SEL, "1.0", tk.END)
        # Reset anchor to match new cursor position
        self.mark_set(tk.ANCHOR, target_pos)
        self.mark_set(tk.INSERT, target_pos)
        return "break"

    def _select_token(self, find_boundary_func) -> str:
        """Generic token selection extending from current position."""
        cursor_pos = self.index(tk.INSERT)
        target_pos = find_boundary_func(cursor_pos)

        if not target_pos:
            return "break"

        # Check if there's an existing selection
        sel_ranges: tuple[str, ...] = self.tag_ranges(tk.SEL)  # type: ignore[assignment]
        self.tag_remove(tk.SEL, "1.0", tk.END)
        if sel_ranges:
            # There's an existing selection
            sel_start, sel_end = sel_ranges[0], sel_ranges[1]
        else:
            sel_start, sel_end = cursor_pos, cursor_pos
        sel_anchor = sel_start if self.compare(sel_end, "==", cursor_pos) else sel_end

        self.mark_set(tk.ANCHOR, sel_anchor)
        self.mark_set(tk.INSERT, target_pos)

        if self.compare(target_pos, "<", sel_anchor):
            sel_start, sel_end = target_pos, sel_anchor
        else:
            sel_start, sel_end = sel_anchor, target_pos

        if self.compare(sel_start, "!=", sel_end):
            self.tag_add(tk.SEL, sel_start, sel_end)
            self.focus_set()

        return "break"

    def _find_token_start_backward(self, idx: str) -> str:
        TOKEN_RX = r"\n|(?:[\w_]+|[^\w\s]+)[ \t]*"

        # TODO: This is pretty inefficient, because it scans (nearly) the entire text.
        txt = self.get("1.0", f"{idx}")

        m = None
        for match in re.finditer(TOKEN_RX, txt):
            m = match
        if not m:
            return ""
        return f"1.0 + {m.start()} chars"

    def _find_token_end_forward(self, idx: str) -> str:
        TOKEN_RX = r"\n|[ \t]*(?:[\w_]+|[^\w\s]+)"

        # Start search from the next character to avoid matching current position
        # TODO: This is pretty inefficient, because it scans (nearly) the entire text.
        txt = self.get(idx, "end - 1c")
        m = re.search(TOKEN_RX, txt)
        if m:
            return f"{idx} + {m.end()} chars"
        return ""

    def _apply_indent_action(self, line_action: Callable[[int], None]) -> str:
        """Helper to apply indent/unindent to selection or current line."""
        sel = self.tag_ranges(tk.SEL)
        if sel:
            sel_start, sel_end = sel
            # Apply line_action to selected lines
            start_line = int(str(sel_start).split(".")[0])
            end_line = int(str(sel_end).split(".")[0])
            for line_num in range(start_line, end_line + 1):
                line_action(line_num)
        else:
            # Apply to current line
            current_line = int(self.index(tk.INSERT).split(".")[0])
            line_action(current_line)
        self.format_after_idle()
        return "break"  # Prevent default key handling

    def indent_selection(self) -> str:
        """Indent selection or current line."""

        def _indent_line(line_num: int) -> None:
            line_start = f"{line_num}.0"
            self.insert(line_start, "    ")

        return self._apply_indent_action(_indent_line)

    def unindent_selection(self) -> str:
        """Unindent selection or current line."""

        def _unindent_line(line_num: int) -> None:
            line_start = f"{line_num}.0"
            line_text = self.get(line_start, f"{line_num}.4")
            spaces_to_remove = min(4, len(line_text) - len(line_text.lstrip()))
            if spaces_to_remove > 0:
                self.delete(line_start, f"{line_num}.{spaces_to_remove}")

        return self._apply_indent_action(_unindent_line)
