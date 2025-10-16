"""
Tooltip widget for tkinter that displays help text when hovering over widgets.
"""

from __future__ import annotations

import tkinter as tk


class Tooltip:
    """
    A tooltip that appears when hovering over a widget for a specified delay.

    Args:
        widget: The tkinter widget to attach the tooltip to
        text: The text to display in the tooltip
        delay: Delay in milliseconds before showing tooltip (default: 1000)
    """

    def __init__(self, widget: tk.Widget, text: str, delay: int = 1000) -> None:
        self.widget = widget
        self.text = text
        self.delay = delay

        self.tooltip_window: tk.Toplevel | None = None
        self.scheduled_id: str | None = None

        # Bind events to the widget
        self.widget.bind("<Enter>", self._schedule_show)
        self.widget.bind("<Leave>", self._hide)
        self.widget.bind("<Motion>", self._schedule_show)

        # Clean up when widget is destroyed
        self.widget.bind("<Destroy>", self._destroy)

    def _schedule_show(self, event: tk.Event) -> None:
        """Schedule the tooltip to be shown after the delay."""
        # Cancel any existing scheduled show
        if self.scheduled_id:
            self.widget.after_cancel(self.scheduled_id)

        # Schedule the tooltip to show after delay
        self.scheduled_id = self.widget.after(self.delay, self._show)

    def _show(self) -> None:
        """Create and display the tooltip window."""
        if self.tooltip_window:
            return  # Already showing

        # Get widget position and size
        self.widget.update_idletasks()
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty()
        width = self.widget.winfo_width()
        height = self.widget.winfo_height()

        # Create tooltip window
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)

        # Create label with text
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            justify="left",
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=4,
            wraplength=300,
        )
        label.pack()

        # Style the tooltip to match application colors
        self._apply_styling(label)

        # Force the window to render and get its size
        self.tooltip_window.update_idletasks()

        # Position the tooltip using place() geometry manager
        self._position_tooltip(x, y, width, height, label)

        # Make sure tooltip is on top and visible
        self.tooltip_window.lift()
        self.tooltip_window.attributes("-topmost", True)
        self.tooltip_window.update()

    def _apply_styling(self, label: tk.Label) -> None:
        """Apply styling to match the application's color scheme."""
        try:
            # Try to get colors from the widget or its parent
            bg_color = self.widget.cget("bg")
            fg_color = self.widget.cget("fg")

            # If colors are system defaults, try parent colors
            if bg_color in ["", "SystemButtonFace"]:
                parent = self.widget.master
                while parent and bg_color in ["", "SystemButtonFace"]:
                    try:
                        bg_color = parent.cget("bg")
                        parent = parent.master
                    except tk.TclError:
                        break

            # Set tooltip colors
            if bg_color and bg_color not in ["", "SystemButtonFace"]:
                label.configure(bg=bg_color)
            else:
                label.configure(bg="#ffffcc")  # Light yellow fallback

            if fg_color and fg_color not in ["", "SystemButtonText"]:
                label.configure(fg=fg_color)
            else:
                label.configure(fg="black")  # Black fallback

        except tk.TclError:
            # Fallback to default colors if there's an error
            label.configure(bg="#ffffcc", fg="black")

    def _position_tooltip(self, x: int, y: int, width: int, height: int, label: tk.Label) -> None:
        """Position the tooltip relative to the widget."""
        # Get the actual size of the tooltip window
        tooltip_width = self.tooltip_window.winfo_reqwidth()
        tooltip_height = self.tooltip_window.winfo_reqheight()

        # Get screen dimensions
        screen_width = self.widget.winfo_screenwidth()
        screen_height = self.widget.winfo_screenheight()

        # Calculate position (prefer below widget, centered horizontally)
        tooltip_x = x + (width - tooltip_width) // 2
        tooltip_y = y + height + 5

        # Adjust if tooltip would go off screen horizontally
        if tooltip_x < 5:
            tooltip_x = 5
        elif tooltip_x + tooltip_width > screen_width - 5:
            tooltip_x = screen_width - tooltip_width - 5

        # If tooltip would go below screen, position above widget
        if tooltip_y + tooltip_height > screen_height - 5:
            tooltip_y = y - tooltip_height - 5

        # Use withdraw/deiconify approach for reliable positioning
        self.tooltip_window.withdraw()
        self.tooltip_window.geometry(f"{tooltip_width}x{tooltip_height}+{tooltip_x}+{tooltip_y}")
        self.tooltip_window.deiconify()

    def _hide(self, event: tk.Event) -> None:
        """Hide the tooltip and cancel any scheduled show."""
        # Cancel scheduled show
        if self.scheduled_id:
            self.widget.after_cancel(self.scheduled_id)
            self.scheduled_id = None

        # Destroy tooltip window
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def _destroy(self, event: tk.Event) -> None:
        """Clean up when the widget is destroyed."""
        self._hide(event)

    def update_text(self, text: str) -> None:
        """Update the tooltip text."""
        self.text = text
        if self.tooltip_window:
            # Update existing tooltip
            for child in self.tooltip_window.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(text=text)
                    break

    def destroy(self) -> None:
        """Manually destroy the tooltip."""
        self._hide(tk.Event())
