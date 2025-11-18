"""
This class modifies the data at file-write in a way
that the resulting file will only differ from the read file
if the user added/removed/moved any schematic-element or
changed any text/name/contol-information. Any scrolling, zooming
will not create a different file content.
The "include timestamp in generated HDL" must be switched off if
the file shall not change.
"""
import canvas_editing

class WriteDataCreator:
    def __init__(self, standard_size) -> None:
        self.standard_size = standard_size
        self.last_design_dictionary = None

    def store_as_compare_object(self, design_dictionary) -> None:
        self.last_design_dictionary = design_dictionary

    def zoom_graphic_to_standard_size(self, actual_size) -> float:
        zoom_factor = self.standard_size/actual_size
        canvas_editing.canvas_zoom([0,0], zoom_factor)
        return zoom_factor

    def zoom_graphic_back_to_actual_size(self, zoom_factor) -> None:
        canvas_editing.canvas_zoom([0,0], 1/zoom_factor)
        return

    def round_and_sort_data(self, design_dictionary, all_graphical_elements) -> dict[str, list]:
        used_graphic_elements = self._create_used_graphic_elements(design_dictionary, all_graphical_elements)
        design_dictionary = self._sort_graphic_elements(design_dictionary, used_graphic_elements)
        design_dictionary = self._round_coordinates    (design_dictionary, used_graphic_elements)
        design_dictionary = self._round_parameters     (design_dictionary)
        self.store_as_compare_object(design_dictionary)
        return design_dictionary

    def _create_used_graphic_elements(self, design_dictionary, all_graphical_elements) -> list:
        used_graphic_elements = []
        for graphical_element in all_graphical_elements:
            if graphical_element in design_dictionary:
                used_graphic_elements.append(graphical_element)
        return used_graphic_elements
    
    def _round_coordinates(self, design_dictionary, used_graphic_elements) -> dict[str, list]:
        for graphical_element in used_graphic_elements:
            if graphical_element in ("window_condition_action_block", "window_global_actions"):
                index_of_tags = 3
            elif graphical_element.startswith("window_"):
                index_of_tags = 2
            else:
                index_of_tags = 1
            for graphic_instance_index, graphical_instance_property_list in enumerate(design_dictionary[graphical_element]):
                identifier_at_write  = graphical_instance_property_list[index_of_tags][0]
                coordinates_at_write = graphical_instance_property_list[0]
                identifier_from_last, coordinates_from_last = self._get_info_from_last_data_by_index(graphical_element, graphic_instance_index, index_of_tags)
                #print("lastdata = ", identifier_from_last, coordinates_from_last, coordinates_at_write)
                for coordinate_index, coordinate_at_write in enumerate(coordinates_at_write):
                    coordinate_at_write = round(coordinate_at_write, 0) # round to integer
                    if (identifier_from_last != "" and # In the last data there is a corresponding graphical instance.
                        identifier_at_write == identifier_from_last and # The graphic instance exists in last data at same position in the list.
                        coordinates_from_last[coordinate_index]%1 == 0 and # The last coordinate is already a (rounded) integer value ...
                        coordinates_from_last[coordinate_index] != coordinate_at_write and # ... and differs from the new value ...
                        abs(coordinates_from_last[coordinate_index] - coordinate_at_write) < 0.2 * self.standard_size # ... only by a small amount.
                    ):
                        #print("Write Coordinate differs and is replaced by:", identifier_at_write, coordinate_at_write, coordinates_from_last[coordinate_index])
                        coordinate_at_write = coordinates_from_last[coordinate_index]
                    graphical_instance_property_list[0][coordinate_index] = coordinate_at_write
        return design_dictionary

    def _get_info_from_last_data_by_index(self, graphical_element, graphic_instance_index, index_of_tags) -> list:
        if (self.last_design_dictionary is not None and
            graphical_element in self.last_design_dictionary and
            graphic_instance_index<len(self.last_design_dictionary[graphical_element])
        ):
            identifier_from_last  = self.last_design_dictionary[graphical_element][graphic_instance_index][index_of_tags][0]
            coordinates_from_last = self.last_design_dictionary[graphical_element][graphic_instance_index][0]
        else:
            identifier_from_last  = ""
            coordinates_from_last = []
        return identifier_from_last, coordinates_from_last
    
    def _round_parameters(self, design_dictionary) -> dict[str, list]:
        design_dictionary["label_fontsize"   ] = round(design_dictionary["label_fontsize"   ], 0)
        design_dictionary["priority_distance"] = round(design_dictionary["priority_distance"], 0)
        return design_dictionary

    def _sort_graphic_elements(self, design_dictionary, used_graphic_elements) -> dict[str, list]:
        # At all sorts the key is the first tag which the graphical element has (identifier tag).
        # The sorting will always give the same result if the order of tags is not changed by tkinter.
        for graphical_element in used_graphic_elements:
            if graphical_element in ("window_condition_action_block", "window_global_actions"):
                index_of_tags = 3
            elif graphical_element.startswith("window_"):
                index_of_tags = 2
            else:
                index_of_tags = 1
            design_dictionary[graphical_element] = sorted(design_dictionary[graphical_element], key=lambda x: x[index_of_tags][0] )
        return design_dictionary
