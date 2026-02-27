"""
This module contains a class which implements a dialog to
show the user how to work with keyboard shortcuts in the code editor.
"""

from dialogs import text_dialog


class ShortCutsDialog:
    """
    This class implements a dialog to show the user how to work with keyboard shortcuts in the code editor.
    """

    def __init__(self):
        content = """1. Ctrl-e loads the text into an external editor.
2. Ctrl-a selects all text.
3. Ctrl-c copies the selection into the clipboard.
4. Ctrl-x cuts the selection into the clipboard.
5. Ctrl-v pastes the content of the clipboard at the position of the insertion cursor, replacing any selection.
6. Ctrl-z undoes the last action.
7. Ctrl-Z or Ctrl-y redoes the last action.
8. Ctrl-Left moves insertion-cursor 1 word left.
9. Ctrl-Right moves insertion-cursor 1 word right.
10. Ctrl-] indents the selection or the current line (works only under Linux).
11. Ctrl-[ unindents the selection or the current line (works only under Linux).
12. Ctrl-Backspace deletes the word before the insertion cursor.
13. Ctrl-Delete deletes the word after the insertion cursor.
14. Tab inserts 4 blanks at the position of the insertion cursor (can be used to indent a line).
15. Shift-Tab unindents the selection or the current line (works only under Windows).
"""
        text_dialog.TextDialog("Keyboard Shortcuts for text editing", content, "1000x260")
