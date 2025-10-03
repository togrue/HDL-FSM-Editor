"""
A MoveCanvasWindow object is created, when the user moves a Canvas window object.
"""

import main_window
import move_handling
import move_handling_finish
import move_handling_initialization


class MoveHandlingCanvasWindow:
    def __init__(self, event, widget, window_id):
        self.widget = widget
        self.window_id = window_id
        window_coords = main_window.canvas.coords(self.window_id)
        self.move_list = move_handling_initialization.create_move_list(
            [self.window_id], window_coords[0], window_coords[1]
        )
        self.touching_point_x = event.x
        self.touching_point_y = event.y

        # This first move does not move the object.
        # It is needed to set self.difference_x, self.difference_y of the moved window to 0.
        # Both values are used, when the window is picked up at its border.
        # The values are set to 0 by using window_coords[0] and window_coords[1] as event coords:
        move_handling.move_to_coordinates(
            window_coords[0],
            window_coords[1],
            self.move_list,
            first=True,
            move_to_grid=False,
        )

        # Create a binding for the now following movements of the mouse and for finishing the moving:
        self.funcid_motion = widget.bind("<Motion>", self._motion)
        self.funcid_release = widget.bind("<ButtonRelease-1>", self._release)

    def _motion(self, motion_event):
        delta_x = motion_event.x - self.touching_point_x
        delta_y = motion_event.y - self.touching_point_y
        window_coords = main_window.canvas.coords(self.window_id)
        move_handling.move_to_coordinates(
            window_coords[0] + delta_x,
            window_coords[1] + delta_y,
            self.move_list,
            first=False,
            move_to_grid=False,
        )

    def _release(self, _):
        self.widget.unbind("<Motion>", self.funcid_motion)
        self.widget.unbind("<ButtonRelease-1>", self.funcid_release)
        window_coords = main_window.canvas.coords(self.window_id)
        move_handling.move_to_coordinates(
            window_coords[0],
            window_coords[1],
            self.move_list,
            first=False,
            move_to_grid=False,  # Only used by the line to a window.
        )
        move_handling_finish.move_finish_for_transitions(self.move_list)
