"""
This class lets the user configure a color.
"""

from tkinter import colorchooser


class ColorChanger:
    def __init__(self, default_color: str) -> None:
        self.default_color = default_color

    def ask_color(self) -> str | None:
        return colorchooser.askcolor(self.default_color)[1]
