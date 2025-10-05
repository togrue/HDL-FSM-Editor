"""
Creates a menu.
"""

import tkinter as tk
from typing import Any


class OptionMenu(tk.Listbox):
    def __init__(self, master: tk.Widget, items: list[str], *args: Any, **kwargs: Any) -> None:
        tk.Listbox.__init__(self, master, *args, exportselection=False, background="grey", **kwargs)

        for item in items:
            self.insert(tk.END, item)

        self.bind("<Enter>", self.snap_highlight_to_mouse)
        self.bind("<Motion>", self.snap_highlight_to_mouse)

    def snap_highlight_to_mouse(self, event: tk.Event) -> None:
        self.selection_clear(0, tk.END)
        self.selection_set(self.nearest(event.y))
