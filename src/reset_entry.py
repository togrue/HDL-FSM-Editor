from project_manager import project_manager


class ResetEntry:
    difference_x = 0
    difference_y = 0

    def __init__(self, reset_entry_polygon_coords, tags) -> None:
        polygon_id = project_manager.canvas.create_polygon(
            *reset_entry_polygon_coords, fill="red", outline="orange", tags=tags
        )
        project_manager.canvas.tag_bind(
            polygon_id, "<Enter>", lambda event, id=polygon_id: project_manager.canvas.itemconfig(id, width=2)
        )
        project_manager.canvas.tag_bind(
            polygon_id, "<Leave>", lambda event, id=polygon_id: project_manager.canvas.itemconfig(id, width=1)
        )
        project_manager.canvas.create_text(
            reset_entry_polygon_coords[4] - 4 * project_manager.reset_entry_size / 5,
            reset_entry_polygon_coords[5],
            text="Reset",
            tag="reset_text",
            font=project_manager.state_name_font,
        )

    @classmethod
    def move_to(cls, event_x, event_y, polygon_id, first, last) -> None:
        if first is True:
            # Calculate the difference between the "anchor" point and the event:
            coords = project_manager.canvas.coords(polygon_id)
            middle_point = [coords[4], coords[5]]
            cls.difference_x, cls.difference_y = -event_x + middle_point[0], -event_y + middle_point[1]
        # Keep the distance between event and anchor point constant:
        event_x, event_y = event_x + cls.difference_x, event_y + cls.difference_y
        if last is True:
            event_x = project_manager.state_radius * round(event_x / project_manager.state_radius)
            event_y = project_manager.state_radius * round(event_y / project_manager.state_radius)
        width = cls._determine_width_of_the_polygon(polygon_id)
        height = cls._determine_height_of_the_polygon(polygon_id)
        new_upper_left_corner = cls._calculate_new_upper_left_corner_of_the_polygon(event_x, event_y, width, height)
        new_upper_right_corner = cls._calculate_new_upper_right_corner_of_the_polygon(event_x, event_y, width, height)
        new_point_right_corner = [event_x, event_y]
        new_lower_right_corner = cls._calculate_new_lower_right_corner_of_the_polygon(event_x, event_y, width, height)
        new_lower_left_corner = cls._calculate_new_lower_left_corner_of_the_polygon(event_x, event_y, width, height)
        new_coords = [
            *new_upper_left_corner,
            *new_upper_right_corner,
            *new_point_right_corner,
            *new_lower_right_corner,
            *new_lower_left_corner,
        ]
        new_center = cls._calculate_new_center_of_the_polygon(event_x, event_y, width)
        cls._move_polygon_in_canvas(polygon_id, new_coords, new_center)

    @classmethod
    def _determine_width_of_the_polygon(cls, polygon_id):
        polygon_coords = project_manager.canvas.coords(polygon_id)
        return polygon_coords[2] - polygon_coords[0]

    @classmethod
    def _determine_height_of_the_polygon(cls, polygon_id):
        polygon_coords = project_manager.canvas.coords(polygon_id)
        return polygon_coords[9] - polygon_coords[1]

    @classmethod
    def _calculate_new_upper_left_corner_of_the_polygon(cls, event_x, event_y, width, height) -> list:
        return [event_x - 13 * width / 10, event_y - height / 2]

    @classmethod
    def _calculate_new_upper_right_corner_of_the_polygon(cls, event_x, event_y, width, height) -> list:
        return [event_x - 3 * width / 10, event_y - height / 2]

    @classmethod
    def _calculate_new_lower_right_corner_of_the_polygon(cls, event_x, event_y, width, height) -> list:
        return [event_x - 3 * width / 10, event_y + height / 2]

    @classmethod
    def _calculate_new_lower_left_corner_of_the_polygon(cls, event_x, event_y, width, height) -> list:
        return [event_x - 13 * width / 10, event_y + height / 2]

    @classmethod
    def _calculate_new_center_of_the_polygon(cls, event_x, event_y, width) -> list:
        return [event_x - 4 * width / 5, event_y]

    @classmethod
    def _move_polygon_in_canvas(cls, polygon_id, new_coords, new_center) -> None:
        project_manager.canvas.coords(polygon_id, *new_coords)
        project_manager.canvas.coords("reset_text", *new_center)
