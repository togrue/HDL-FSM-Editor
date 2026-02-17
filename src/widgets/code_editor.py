"""
Extensions to the standard tkinter.Text widget for code editing.

- Word-wise cursor movement (Ctrl+Left/Right) and selection (Ctrl+Shift+Left/Right)
- Correct Shift+Arrow selection and anchor handling
- Whole-word deletion (Ctrl+BackSpace, Ctrl+Delete)
- Indent/unindent (Ctrl+], Ctrl+[ and Shift+Tab)
"""

import re
import tkinter as tk
from typing import Any, Callable


class CodeEditor(tk.Text):
    """
    A code editor widget extending tkinter.Text with word movement,
    selection, word deletion, and indent/unindent.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Word-wise cursor movement
        self.bind("<Control-Left>", lambda event: self.move_word_left())
        self.bind("<Control-Right>", lambda event: self.move_word_right())
        # Word selection
        self.bind("<Shift-Control-Left>", lambda event: self.select_word_left())
        self.bind("<Shift-Control-Right>", lambda event: self.select_word_right())
        # Shift+arrow: normal selection with correct anchor when switching from word selection
        self.bind("<Shift-Left>", lambda event: self._handle_normal_selection_left())
        self.bind("<Shift-Right>", lambda event: self._handle_normal_selection_right())
        # Reset anchor when moving with arrow keys (no shift)
        self.bind("<Left>", lambda event: self._reset_anchor_if_no_selection())
        self.bind("<Right>", lambda event: self._reset_anchor_if_no_selection())
        self.bind("<Up>", lambda event: self._reset_anchor_if_no_selection())
        self.bind("<Down>", lambda event: self._reset_anchor_if_no_selection())
        # Whole word deletion
        self.bind("<Control-BackSpace>", lambda event: self.delete_word_backward())
        self.bind("<Control-Delete>", lambda event: self.delete_word_forward())
        # Indent/unindent
        self.bind("<Control-bracketleft>", lambda event: self.unindent_selection())
        self.bind("<Control-bracketright>", lambda event: self.indent_selection())

    def format_after_idle(self) -> None:
        """Override in subclass to trigger formatting after indent/unindent. No-op by default."""
        pass

    def _handle_normal_selection(self, direction: str) -> str:
        """
        Handle Shift+Left or Shift+Right for character selection.
        direction: "left" or "right".
        """
        sel_ranges: tuple[str, ...] = self.tag_ranges(tk.SEL)  # type: ignore[assignment]
        anchor_pos = self.index(tk.ANCHOR)
        cursor_pos = self.index(tk.INSERT)
        if not sel_ranges:
            self.mark_set(tk.ANCHOR, cursor_pos)
            anchor_pos = cursor_pos
        try:
            delta = "- 1 char" if direction == "left" else "+ 1 char"
            new_cursor_pos = self.index(f"{cursor_pos} {delta}")
        except tk.TclError:
            return "break"
        self.mark_set(tk.INSERT, new_cursor_pos)
        if self.compare(anchor_pos, ">", new_cursor_pos):
            sel_start, sel_end = new_cursor_pos, anchor_pos
        else:
            sel_start, sel_end = anchor_pos, new_cursor_pos
        self.tag_remove(tk.SEL, "1.0", tk.END)
        if self.compare(sel_start, "!=", sel_end):
            self.tag_add(tk.SEL, sel_start, sel_end)
        return "break"

    def _handle_normal_selection_left(self) -> str:
        return self._handle_normal_selection("left")

    def _handle_normal_selection_right(self) -> str:
        return self._handle_normal_selection("right")

    def _reset_anchor_if_no_selection(self) -> None:
        """Reset anchor to cursor when there is no selection (after default movement)."""
        sel_ranges: tuple[str, ...] = self.tag_ranges(tk.SEL)  # type: ignore[assignment]
        if not sel_ranges:

            def reset_anchor() -> None:
                self.mark_set(tk.ANCHOR, self.index(tk.INSERT))

            self.after_idle(reset_anchor)

    def _move_cursor(self, find_boundary_func: Callable[[str], str]) -> str:
        """Move cursor to token boundary; clear selection and set anchor."""
        current_pos = self.index(tk.INSERT)
        target_pos = find_boundary_func(current_pos)
        if not target_pos:
            return "break"
        self.tag_remove(tk.SEL, "1.0", tk.END)
        self.mark_set(tk.ANCHOR, target_pos)
        self.mark_set(tk.INSERT, target_pos)
        return "break"

    def _select_token(self, find_boundary_func: Callable[[str], str]) -> str:
        """Extend selection by one token in the given direction."""
        cursor_pos = self.index(tk.INSERT)
        target_pos = find_boundary_func(cursor_pos)
        if not target_pos:
            return "break"
        sel_ranges: tuple[str, ...] = self.tag_ranges(tk.SEL)  # type: ignore[assignment]
        self.tag_remove(tk.SEL, "1.0", tk.END)
        if sel_ranges:
            sel_start, sel_end = sel_ranges[0], sel_ranges[1]
        else:
            sel_start = sel_end = cursor_pos
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
        token_rx = re.compile(r"\n|(?:[\w_]+|[^\w\s]+)[ \t]*")
        txt = self.get("1.0", idx)
        m = None
        for match in re.finditer(token_rx, txt):
            m = match
        if not m:
            return ""
        return f"1.0 + {m.start()} chars"

    def _find_token_end_forward(self, idx: str) -> str:
        token_rx = re.compile(r"\n|[ \t]*(?:[\w_]+|[^\w\s]+)")
        txt = self.get(idx, "end-1c")
        m = re.search(token_rx, txt)
        if m:
            return f"{idx} + {m.end()} chars"
        return ""

    def move_word_left(self) -> str:
        return self._move_cursor(self._find_token_start_backward)

    def move_word_right(self) -> str:
        return self._move_cursor(self._find_token_end_forward)

    def select_word_left(self) -> str:
        return self._select_token(self._find_token_start_backward)

    def select_word_right(self) -> str:
        return self._select_token(self._find_token_end_forward)

    def _delete_token(
        self,
        find_boundary_func: Callable[[str], str],
        backward: bool,
    ) -> str:
        """Delete one token backward or forward. Override to call format_after_idle."""
        current_pos = self.index(tk.INSERT)
        target_pos = find_boundary_func(current_pos)
        if not target_pos:
            return "break"
        if backward:
            self.delete(target_pos, current_pos)
        else:
            self.delete(current_pos, target_pos)
        self.format_after_idle()
        return "break"

    def delete_word_backward(self) -> str:
        return self._delete_token(self._find_token_start_backward, backward=True)

    def delete_word_forward(self) -> str:
        return self._delete_token(self._find_token_end_forward, backward=False)

    def _apply_indent_action(self, line_action: Callable[[int], None]) -> str:
        """Apply indent/unindent to selection or current line."""
        sel = self.tag_ranges(tk.SEL)
        if sel:
            sel_start, sel_end = sel[0], sel[1]
            start_line = int(str(sel_start).split(".")[0])
            end_line = int(str(sel_end).split(".")[0])
            for line_num in range(start_line, end_line + 1):
                line_action(line_num)
        else:
            current_line = int(self.index(tk.INSERT).split(".")[0])
            line_action(current_line)
        self.format_after_idle()
        return "break"

    def indent_selection(self) -> str:
        def _indent_line(line_num: int) -> None:
            self.insert(f"{line_num}.0", "    ")

        return self._apply_indent_action(_indent_line)

    def unindent_selection(self) -> str:
        def _unindent_line(line_num: int) -> None:
            line_start = f"{line_num}.0"
            line_text = self.get(line_start, f"{line_num}.4")
            spaces_to_remove = min(4, len(line_text) - len(line_text.lstrip()))
            if spaces_to_remove > 0:
                self.delete(line_start, f"{line_num}.{spaces_to_remove}")

        return self._apply_indent_action(_unindent_line)
