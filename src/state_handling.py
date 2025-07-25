"""
This module contains all methods for inserting states.
"""

import tkinter as tk
from tkinter import messagebox

import canvas_editing
import constants
import main_window
import move_handling_initialization
import state_action_handling
import state_comment
import transition_handling
import undo_handling
from dialogs.color_changer import ColorChanger
from widgets.OptionMenu import OptionMenu

state_number = 0  # Defaultvalue, will be increased with every new state.
difference_x = 0
difference_y = 0


def move_to(event_x, event_y, state_id, first, last) -> None:
    global difference_x, difference_y
    if first is True:
        # Calculate the difference between the "anchor" point and the event:
        coords = main_window.canvas.coords(state_id)
        middle_point = _calculate_middle_point(coords)
        difference_x, difference_y = -event_x + middle_point[0], -event_y + middle_point[1]
    # Keep the distance between event and anchor point constant:
    event_x, event_y = event_x + difference_x, event_y + difference_y
    if last is True:
        event_x = canvas_editing.state_radius * round(event_x / canvas_editing.state_radius)
        event_y = canvas_editing.state_radius * round(event_y / canvas_editing.state_radius)
    text_tag = _determine_the_tag_of_the_state_name(state_id)
    state_radius = _determine_the_radius_of_the_state(state_id)
    main_window.canvas.coords(
        state_id, event_x - state_radius, event_y - state_radius, event_x + state_radius, event_y + state_radius
    )
    main_window.canvas.coords(text_tag, event_x, event_y)
    main_window.canvas.tag_raise(state_id, "all")
    main_window.canvas.tag_raise(text_tag, state_id)


def _calculate_middle_point(coords) -> list:
    middle_x = (coords[0] + coords[2]) / 2
    middle_y = (coords[1] + coords[3]) / 2
    return [middle_x, middle_y]


def _determine_the_tag_of_the_state_name(state_id):
    tags = main_window.canvas.gettags(state_id)
    for tag in tags:
        if tag.startswith("state") and not tag.endswith("_comment_line_end"):
            return tag + "_name"


def _determine_the_radius_of_the_state(state_id):
    state_coords = main_window.canvas.coords(state_id)
    return (state_coords[2] - state_coords[0]) // 2


def get_canvas_id_of_state_name(state_id):
    tags = main_window.canvas.gettags(state_id)
    return main_window.canvas.find_withtag(tags[0] + "_name")[0]


def insert_state(event) -> None:
    global state_number
    state_number += 1
    event_x, event_y = canvas_editing.translate_window_event_coordinates_in_rounded_canvas_coordinates(event)
    overlapping_items = main_window.canvas.find_overlapping(
        event_x - canvas_editing.state_radius,
        event_y - canvas_editing.state_radius,
        event_x + canvas_editing.state_radius,
        event_y + canvas_editing.state_radius,
    )
    for overlapping_item in overlapping_items:
        if "grid_line" not in main_window.canvas.gettags(overlapping_item):
            return
    state_id = main_window.canvas.create_oval(
        event_x - canvas_editing.state_radius,
        event_y - canvas_editing.state_radius,
        event_x + canvas_editing.state_radius,
        event_y + canvas_editing.state_radius,
        fill=constants.STATE_COLOR,
        width=2,
        outline="blue",
        tags="state" + str(state_number),
    )
    # main_window.canvas.tag_lower(state_id,'all')
    text_id = main_window.canvas.create_text(
        event_x,
        event_y,
        text="S" + str(state_number),
        tags="state" + str(state_number) + "_name",
        font=canvas_editing.state_name_font,
    )
    main_window.canvas.tag_bind(
        text_id, "<Double-Button-1>", lambda event, text_id=text_id: edit_state_name(event, text_id)
    )
    main_window.canvas.tag_bind(
        state_id, "<Enter>", lambda event, id=state_id: main_window.canvas.itemconfig(id, width=4)
    )
    main_window.canvas.tag_bind(
        state_id, "<Leave>", lambda event, id=state_id: main_window.canvas.itemconfig(id, width=2)
    )
    main_window.canvas.tag_bind(state_id, "<Button-3>", lambda event, id=state_id: show_menu(event, id))
    undo_handling.design_has_changed()
    # print ("New State"    , state_id, main_window.canvas.coords(state_id))
    # print ("New Statename", text_id , main_window.canvas.coords(text_id))


def show_menu(event, state_id) -> None:
    listbox = OptionMenu(
        main_window.canvas,
        ["add action", "add comment", "change color"],
        height=3,
        bg="lightgrey",
        width=14,
        activestyle="dotbox",
        relief=tk.RAISED,
    )
    [event_x, event_y] = canvas_editing.translate_window_event_coordinates_in_exact_canvas_coordinates(event)
    window = main_window.canvas.create_window(event_x + 40, event_y, window=listbox)
    listbox.bind(
        "<Button-1>",
        lambda event, window=window, listbox=listbox, menu_x=event_x, menu_y=event_y, state_id=state_id: _evaluate_menu(
            event, window, listbox, menu_x, menu_y, state_id
        ),
    )
    listbox.bind("<Leave>", lambda event, window=window, listbox=listbox: _close_menu(window, listbox))


def _evaluate_menu(event, window, listbox, menu_x, menu_y, state_id) -> None:
    selected_entry = listbox.get(listbox.curselection())
    listbox.destroy()
    main_window.canvas.delete(window)
    if selected_entry == "add action":
        tags = main_window.canvas.gettags(state_id)
        action_block_exists = False
        for tag in tags:
            if tag.startswith("connection"):
                action_block_exists = True
        if not action_block_exists:
            action_ref = state_action_handling.MyText(menu_x, menu_y, height=1, width=8, padding=3, increment=True)
            action_ref.connect_to_state(menu_x, menu_y, state_id)
            action_ref.tag()
            undo_handling.design_has_changed()
    elif selected_entry == "add comment":
        tags = main_window.canvas.gettags(state_id)
        for tag in tags:
            if tag.endswith("comment_line_end"):
                return  # There is already a comment attached to this state.
        for tag in tags:
            if tag.startswith("state"):
                state_identifier = tag
                comment_ref = state_comment.StateComment(menu_x, menu_y, height=1, width=8, padding=3)
                comment_ref.add_line(menu_x, menu_y, state_identifier)
                comment_ref.tag(state_identifier)
                undo_handling.design_has_changed()
    elif selected_entry == "change color":
        new_color = ColorChanger(constants.STATE_COLOR).ask_color()
        main_window.canvas.itemconfigure(state_id, fill=new_color)
        undo_handling.design_has_changed()


def _close_menu(window, listbox) -> None:
    listbox.destroy()
    main_window.canvas.delete(window)


def edit_state_name(event, text_id) -> None:
    main_window.canvas.unbind("<Button-1>")
    main_window.canvas.unbind_all("<Delete>")
    old_text = main_window.canvas.itemcget(text_id, "text")
    text_box = tk.Entry(main_window.canvas, width=10, justify=tk.CENTER)
    # text_box = Entry(None, width=10, justify=tk.CENTER) funktioniert auch, unklar, was richtig/besser ist.
    text_box.insert(tk.END, old_text)
    text_box.select_range(0, tk.END)
    text_box.bind("<Return>", lambda event, text_id=text_id, text_box=text_box: _update_state_name(text_id, text_box))
    text_box.bind(
        "<Escape>",
        lambda event, text_id=text_id, text_box=text_box, old_text=old_text: _abort_edit_text(
            text_id, text_box, old_text
        ),
    )
    event_x, event_y = canvas_editing.translate_window_event_coordinates_in_rounded_canvas_coordinates(event)
    main_window.canvas.create_window(event_x, event_y, window=text_box, tag="entry-window")
    text_box.focus_set()


def _update_state_name(text_id, text_box) -> None:
    main_window.canvas.delete("entry-window")
    new_text = text_box.get()
    text_box.destroy()
    tags = main_window.canvas.gettags(text_id)
    for t in tags:
        if t.startswith("state"):  # Format of text_id tag: 'state' + str(state_number) + "_name"
            state_tag = t[:-5]
            _show_new_state_name(new_text, text_id)
            _resize_state(state_tag, text_id)
    undo_handling.design_has_changed()
    main_window.canvas.bind("<Button-1>", move_handling_initialization.move_initialization)
    main_window.canvas.bind_all("<Delete>", lambda event: canvas_editing.delete())
    tags = main_window.canvas.gettags(state_tag)
    for t in tags:
        if t.endswith("_start"):
            transition_handling.extend_transition_to_state_middle_points(t[:-6])
            transition_handling.shorten_to_state_border(t[:-6])
        elif t.endswith("_end") and not t.endswith("_comment_line_end"):
            transition_handling.extend_transition_to_state_middle_points(t[:-4])
            transition_handling.shorten_to_state_border(t[:-4])


def __get_list_of_state_names(text_id) -> list:
    state_name_list = []
    all_canvas_ids = main_window.canvas.find_withtag("all")
    for canvas_id in all_canvas_ids:
        if main_window.canvas.type(canvas_id) == "oval":
            state_tags = main_window.canvas.gettags(canvas_id)
            for tag in state_tags:
                if (
                    tag.startswith("state")
                    and not tag.endswith("_comment_line_end")
                    and main_window.canvas.find_withtag(tag + "_name")[0] != text_id
                ):
                    state_name_list.append(main_window.canvas.itemcget(tag + "_name", "text"))
    return state_name_list


def _abort_edit_text(text_id, text_box, old_text) -> None:
    main_window.canvas.delete("entry-window")
    main_window.canvas.itemconfig(text_id, text=old_text)
    text_box.destroy()
    main_window.canvas.bind("<Button-1>", move_handling_initialization.move_initialization)
    main_window.canvas.bind_all("<Delete>", lambda event: canvas_editing.delete())


def _show_new_state_name(new_text, text_id) -> None:
    state_name_list = __get_list_of_state_names(text_id)
    if new_text != "":
        if new_text not in state_name_list:
            main_window.canvas.itemconfig(text_id, text=new_text)
        else:
            messagebox.showerror("Error", "The state name\n" + new_text + "\nis already used at another state.")


def _resize_state(state_tag, text_id) -> None:
    state_coords = main_window.canvas.coords(state_tag)
    state_width = state_coords[2] - state_coords[0]
    size = main_window.canvas.bbox(text_id)
    text_width = (
        size[2] - size[0] + 15
    )  # Make the text a little bit bigger, so that it does not touch the state circle.
    if text_width < 2 * canvas_editing.state_radius:
        text_width = 2 * canvas_editing.state_radius
    difference = text_width - state_width
    state_coords[0] = state_coords[0] - difference // 2
    state_coords[1] = state_coords[1] - difference // 2
    state_coords[2] = state_coords[2] + difference // 2
    state_coords[3] = state_coords[3] + difference // 2
    overlapping_list = main_window.canvas.find_overlapping(*state_coords)
    state_is_too_big = False
    for canvas_item in overlapping_list:
        if (
            main_window.canvas.type(canvas_item) not in ["text", "line", "rectangle"]
            and canvas_item != main_window.canvas.find_withtag(state_tag)[0]
        ):
            state_is_too_big = True
    if not state_is_too_big:
        main_window.canvas.coords(state_tag, state_coords)
