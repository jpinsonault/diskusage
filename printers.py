import curses
from functools import partial
from itertools import islice
from typing import Optional
from loguru import logger
from ContextUtils import get_text, get_cursor_index, get_x, get_selected_index
from PrintItem import PrintItem


def print_empty_line(screen, y):
    pass


def print_line(x, text, screen, y):
    screen.addstr(y, x, text, curses.A_NORMAL)


def print_highlighted_line(x, text, screen, y):
    screen.addstr(y, x, text, curses.A_REVERSE)


def print_bold_line(x, text, screen, y):
    screen.addstr(y, x, text, curses.A_BOLD)


def make_top_bar(context, remaining_height):
    def print_top_bar(screen, y):
        items = [text for key, text in context["items"].items()]
        screen.addstr(y, 0, " | ".join(items), curses.A_BOLD)

    return [print_top_bar, print_empty_line]


def make_bottom_bar(context, remaining_height):
    def print_bottom_bar(screen, y) -> int:
        items = [text for key, text in context["items"].items()]

        screen.addstr(y, 0, " | ".join(items), curses.A_BOLD)

    return [print_empty_line, print_bottom_bar]


def make_spacer(context, remaining_height):
    """
        Fills up the remaining space with empty lines
        Useful for shoving ui bits to the bottom of the screen
    """
    return [print_empty_line for _ in range(remaining_height)]


def start_stop(index, window_size, list_size):
    if window_size % 2 == 0:
        up = window_size//2
        down = window_size//2 - 1
    else:
        up = window_size//2
        down = window_size//2

    # if topped out
    if index - up < 0:
        return 0, min(window_size, list_size)
    # if bottomed out
    elif index + down > list_size:
        return max(0, list_size-window_size), list_size
    else:
        return index - up, index + down+1


def cut_items_to_window(selected_index, items, window_size):
    start, stop = start_stop(selected_index, window_size, len(items))
    return start, stop, islice(items, start, stop)


def default_item_printer(screen, y_index, item, mode):
    screen.addstr(y_index, 0, str(item), mode)


def tuple_item_printer(screen, y_index, item, mode):
    screen.addstr(y_index, 0, str(item[0]), mode)


def make_scroll_list(context, remaining_height) -> []:
    selected_index = get_selected_index(context)
    is_focused = get_focused(context)

    start, stop, visible_items = cut_items_to_window(selected_index, context["items"], remaining_height)

    print_items = []
    for index, item in zip(range(start, stop), visible_items):
        if index == selected_index and is_focused:
            print_items.append(partial(print_highlighted_line, 0, str(item)))
        else:
            print_items.append(partial(print_line, 0, str(item)))

    return print_items


def make_multiline_text(context, remaining_height) -> []:
    def expand_tabs(text):
        return "    ".join(text.split("\t"))

    text_lines = []
    for index, line in enumerate(context["text"].split("\n")):
        text_lines.append((expand_tabs(line), index))

    context["items"] = text_lines

    return make_scroll_list(context, remaining_height)


def print_context_menu(context, screen, y):
    selected_index = context.get("selected_index", 0)
    x = context["x"]

    label = f"{context.get('label', '')}: "
    screen.addstr(y, x, label, curses.A_BOLD)
    x += len(label)

    for index in range(len(context["items"])):
        item = context["items"][index]
        text = f"[{item}]"
        if index == selected_index:
            screen.addstr(y, x, text, curses.A_REVERSE)
        else:
            screen.addstr(y, x, text, curses.A_NORMAL)

        x += len(text) + 1


def make_context_menu(context, remaining_heigh=0) -> []:
    return [partial(print_context_menu, context),
            print_empty_line]


def get_focused(context) -> bool:
    return context.get("focused", False)


def print_text_input(x, context, screen, y):
    cursor_index = get_cursor_index(context)
    text = get_text(context)
    is_focused = get_focused(context)

    x_index = x

    label = f"{context.get('label', '')}: "
    screen.addstr(y, x_index, label, curses.A_BOLD)
    x_index += len(label)

    screen.addch(y, x_index, "[", curses.A_BOLD)
    x_index += 1

    for index in range(len(text)):
        char = text[index]
        if index == cursor_index and is_focused:
            screen.addch(y, x_index, char, curses.A_REVERSE)
        else:
            screen.addch(y, x_index, char, curses.A_NORMAL)
        x_index += 1

    if cursor_index == len(text) and is_focused:
        screen.addch(y, x_index, "]", curses.A_REVERSE)
        x_index += 1
    else:
        screen.addch(y, x_index, "]", curses.A_BOLD)
        x_index += 1


def print_text_line(screen, context, start_index, remaining_height):
    screen.addstr(start_index, get_x(context), context["text"])

    return context["fixed_size"]


def make_text_input(context, remaining_height):
    return [partial(print_text_input, 0, context)]