"""
Creates a menu.
"""

import tkinter as tk


class OptionMenu(tk.Listbox):
    def __init__(self, master, items, *args, **kwargs):
        tk.Listbox.__init__(self, master, exportselection=False, background="grey", *args, **kwargs)

        for item in items:
            self.insert(tk.END, item)

        self.bind("<Enter>", self.snap_highlight_to_mouse)
        self.bind("<Motion>", self.snap_highlight_to_mouse)

    def snap_highlight_to_mouse(self, event):
        self.selection_clear(0, tk.END)
        self.selection_set(self.nearest(event.y))
