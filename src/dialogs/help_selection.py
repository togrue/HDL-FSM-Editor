"""This module contains a class which implements a dialog to
show the user how to work with text selections in the code editor."""

from dialogs import text_dialog


class SelectionDialog:
    """This class implements a dialog to show the user how to work with text selections in the code editor."""

    def __init__(self):
        content = """
1. The key Shift-Left selects the character to the left of the insertion cursor, extending the selection.
2. The key Shift-Right selects the character to the right of the insertion cursor, extending the selection.
3. The key Shift-Control-Left  selects 1 word to the left.
4. The key Shift-Control-Right  selects 1 word to the right.
5. Dragging with mouse button 1 strokes out a selection between the insertion cursor and the character under the mouse.
6. Double-clicking with mouse button 1 selects the word under the mouse.
7. Dragging after a double click will stroke out a selection consisting of whole words.
8. Triple-clicking with mouse button 1 selects the line under the mouse.
9. Dragging after a triple click will stroke out a selection consisting of whole lines.
10. The end of the selection can be adjusted by dragging with mouse button 1 (before the last release of a single, \
double or triple clicking) while the Shift key is down.
11. The end of the selection can be adjusted character-wise when Left or Right is typed with the Shift key down.
12. The end of the selection can be adjusted word-wise when Ctrl-Left or Ctrl-Right is typed with the Shift key down.
13. The end of the selection can be adjusted line-wise when Up or Down is typed with the Shift key down.
14. The end of the selection can be adjusted page-wise when PageUp or PageDown is typed with the Shift key down.
15. Clicking mouse button 1 with the Ctrl key down will reposition the insertion cursor without affecting the selection.
16. The Insert key inserts the selection at the position of the insertion cursor.
17. If mouse button 2 (scroll wheel) is clicked without moving the mouse, the selection is copied into the text at the \
position of the mouse cursor.
"""
        text_dialog.TextDialog("Working with Selections", content, "1000x300")
