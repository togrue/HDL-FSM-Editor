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
        positioning_mode: How to position the tooltip - 'widget' (default) or 'cursor'
    """

    def __init__(self, widget: tk.Widget, text: str, delay: int = 1000, positioning_mode: str = "cursor") -> None:
        self.widget = widget
        self.text = text
        self.delay = delay
        self.positioning_mode = positioning_mode

        self.tooltip_window: tk.Toplevel | None = None
        self.scheduled_id: str | None = None
        self.mouse_x: int = 0
        self.mouse_y: int = 0

        # Bind events to the widget
        self.widget.bind("<Enter>", self._schedule_show)
        self.widget.bind("<Leave>", self._hide)
        self.widget.bind("<Motion>", self._schedule_show)

        # Track mouse position for cursor-based positioning
        if self.positioning_mode == "cursor":
            self.widget.bind("<Motion>", self._track_mouse_position)

        # Clean up when widget is destroyed
        self.widget.bind("<Destroy>", self._destroy)

    def _track_mouse_position(self, event: tk.Event) -> None:
        """Track mouse position for cursor-based positioning."""
        self.mouse_x = event.x_root
        self.mouse_y = event.y_root

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
            bg="#ffffcc",
            fg="black",
        )
        label.pack()

        # Force the window to render and get its size
        self.tooltip_window.update_idletasks()

        # Position the tooltip based on positioning mode
        if self.positioning_mode == "cursor":
            self._position_tooltip_at_cursor(label)
        else:
            # Get widget position and size for widget-based positioning
            self.widget.update_idletasks()
            x = self.widget.winfo_rootx()
            y = self.widget.winfo_rooty()
            width = self.widget.winfo_width()
            height = self.widget.winfo_height()
            self._position_tooltip_at_widget(x, y, width, height, label)

        # Make sure tooltip is on top and visible
        self.tooltip_window.lift()
        self.tooltip_window.attributes("-topmost", True)
        self.tooltip_window.update()

    def _get_screen_bounds(self) -> tuple[int, int, int, int]:
        """Get virtual root bounds for multi-monitor support.

        Returns:
            Tuple of (vroot_x, vroot_y, vroot_width, vroot_height)
        """
        root = self.widget.winfo_toplevel()
        return (
            root.winfo_vrootx(),
            root.winfo_vrooty(),
            root.winfo_vrootwidth(),
            root.winfo_vrootheight(),
        )

    def _position_tooltip_at_widget(self, x: int, y: int, width: int, height: int, label: tk.Label) -> None:
        """Position the tooltip relative to the widget."""
        assert self.tooltip_window is not None, "Tooltip window is not initialized"

        # Get the actual size of the tooltip window
        tooltip_width = self.tooltip_window.winfo_reqwidth()
        tooltip_height = self.tooltip_window.winfo_reqheight()

        # Get virtual root bounds for multi-monitor support
        vroot_x, vroot_y, vroot_width, vroot_height = self._get_screen_bounds()

        # Calculate position (prefer below widget, centered horizontally)
        tooltip_x = x + (width - tooltip_width) // 2
        tooltip_y = y + height + 5

        # Adjust if tooltip would go off screen horizontally
        tooltip_x = self._clamp_horizontal_position(tooltip_x, tooltip_width, vroot_x, vroot_width)

        # If tooltip would go below screen, position above widget
        if tooltip_y + tooltip_height > vroot_y + vroot_height - 5:
            tooltip_y = y - tooltip_height - 5

        # Ensure vertical position is within bounds
        tooltip_y = self._clamp_vertical_position(tooltip_y, tooltip_height, vroot_y, vroot_height)

        # Apply the tooltip position
        self._apply_tooltip_position(tooltip_width, tooltip_height, tooltip_x, tooltip_y)

    def _clamp_horizontal_position(self, tooltip_x: int, tooltip_width: int, vroot_x: int, vroot_width: int) -> int:
        """Clamp tooltip horizontal position to stay within screen bounds."""
        if tooltip_x < vroot_x + 5:
            tooltip_x = vroot_x + 5
        elif tooltip_x + tooltip_width > vroot_x + vroot_width - 5:
            tooltip_x = vroot_x + vroot_width - tooltip_width - 5
        return tooltip_x

    def _clamp_vertical_position(self, tooltip_y: int, tooltip_height: int, vroot_y: int, vroot_height: int) -> int:
        """Clamp tooltip vertical position to stay within screen bounds."""
        if tooltip_y < vroot_y + 5:
            tooltip_y = vroot_y + 5
        elif tooltip_y + tooltip_height > vroot_y + vroot_height - 5:
            tooltip_y = vroot_y + vroot_height - tooltip_height - 5
        return tooltip_y

    def _apply_tooltip_position(self, tooltip_width: int, tooltip_height: int, tooltip_x: int, tooltip_y: int) -> None:
        """Apply tooltip position using withdraw/deiconify approach for reliable positioning."""
        assert self.tooltip_window is not None, "Tooltip window is not initialized"
        self.tooltip_window.withdraw()
        self.tooltip_window.geometry(f"{tooltip_width}x{tooltip_height}+{tooltip_x}+{tooltip_y}")
        self.tooltip_window.deiconify()

    def _position_tooltip_at_cursor(self, label: tk.Label) -> None:
        """Position the tooltip beside the mouse cursor."""
        assert self.tooltip_window is not None, "Tooltip window is not initialized"

        # Get the actual size of the tooltip window
        tooltip_width = self.tooltip_window.winfo_reqwidth()
        tooltip_height = self.tooltip_window.winfo_reqheight()

        # Get virtual root bounds for multi-monitor support
        vroot_x, vroot_y, vroot_width, vroot_height = self._get_screen_bounds()

        # Calculate position (beside cursor with small offset)
        tooltip_x = self.mouse_x + 10
        tooltip_y = self.mouse_y + 10

        # Adjust if tooltip would go off screen horizontally - flip to left side if needed
        if tooltip_x + tooltip_width > vroot_x + vroot_width - 5:
            tooltip_x = self.mouse_x - tooltip_width - 10

        # Adjust if tooltip would go off screen vertically - flip above if needed
        if tooltip_y + tooltip_height > vroot_y + vroot_height - 5:
            tooltip_y = self.mouse_y - tooltip_height - 10

        # Clamp to ensure tooltip doesn't go off screen on any side
        tooltip_x = self._clamp_horizontal_position(tooltip_x, tooltip_width, vroot_x, vroot_width)
        tooltip_y = self._clamp_vertical_position(tooltip_y, tooltip_height, vroot_y, vroot_height)

        # Apply the tooltip position
        self._apply_tooltip_position(tooltip_width, tooltip_height, tooltip_x, tooltip_y)

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
