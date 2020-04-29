import curses
from itertools import islice
from typing import Optional

from ScreenLine import ScreenLine


def is_hidden(context):
    return context.get("hidden", False)


def print_top_bar(screen, context, start_index, remaining_height) -> int:
    items = [text for key, text in context["items"].items()]
    screen.addstr(start_index, 0, " | ".join(items), curses.A_BOLD)
    return context["fixed_size"]


def print_bottom_bar(screen, context, start_index, remaining_height) -> int:
    num_rows, num_cols = screen.getmaxyx()
    items = [text for key, text in context["items"].items()]

    screen.addstr(num_rows-1, 0, " | ".join(items), curses.A_BOLD)
    return context["fixed_size"]


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


# Sanitizes index to make sure it's in a list
def get_selected(item, items) -> (Optional[object], int):
    if item is None:
        if len(items) > 0:
            return items[0], 0
        else:
            return None, 0

    if item in items:
        return item, items.index(item)
    else:
        return None, 0


def cut_items_to_window(selected_index, items, window_size):
    start, stop = start_stop(selected_index, window_size, len(items))
    return islice(items, start, stop)


def default_item_printer(screen, y_index, item, mode):
    screen.addstr(y_index, 0, str(item), mode)


def tuple_item_printer(screen, y_index, item, mode):
    screen.addstr(y_index, 0, str(item[0]), mode)


def scroll_up(context):
    selected_item = context["selected"]
    items = context["items"]
    item, index = get_selected(selected_item, items)

    try:
        new_selected_item = items[max(0, index - 1)]
    except IndexError:
        new_selected_item = None

    context["selected"] = new_selected_item


def scroll_down(context):
    selected_item = context["selected"]
    items = context["items"]
    item, index = get_selected(selected_item, items)

    try:
        new_selected_index = min(len(items) - 1, index + 1)
        new_selected_item = items[new_selected_index]
    except IndexError:
        new_selected_item = None

    context["selected"] = new_selected_item


def print_scroll_list(screen, context, start_index, remaining_height, item_printer=default_item_printer) -> int:
    selected_item, selected_index = get_selected(context["selected"], context["items"])

    y_index = start_index
    visible_items = cut_items_to_window(selected_index, context["items"], remaining_height)

    for item in visible_items:
        if item == selected_item:
            mode = curses.A_REVERSE
        else:
            mode = curses.A_NORMAL

        item_printer(screen, y_index, item, mode)
        y_index += 1

    return y_index - start_index


def print_multiline_text(screen, context, start_index, remaining_height) -> int:
    def expand_tabs(text):
        return "    ".join(text.split("\t"))

    num_rows, num_cols = screen.getmaxyx()

    lines = []
    for index, line in enumerate(context["text"].split("\n")):
        lines.append((expand_tabs(line), index))

    context["items"] = lines

    return print_scroll_list(screen, context, start_index, remaining_height, item_printer=tuple_item_printer)


def move_menu_left(context):
    selected_index = context.get("selected_index", 0)

    context["selected_index"] = (selected_index - 1) % len(context["items"])


def move_menu_right(context):
    selected_index = context.get("selected_index", 0)

    context["selected_index"] = (selected_index + 1) % len(context["items"])


def print_context_menu(screen, context, screen_line, y):
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


def make_context_menu(context) -> []:
    return [ScreenLine(context=context, x=context["x"], print_fn=print_context_menu),
            ScreenLine(context=context, x=context["x"], text="")]


def get_text(context):
    return context.get("text", "")


def print_text_input(screen, context, screen_line, y):
    cursor_index = get_cursor_index(context)
    text = get_text(context)

    x = screen_line.x

    label = f"{context.get('label', '')}: "
    screen.addstr(y, x, label, curses.A_BOLD)
    x += len(label)

    for index in range(len(text)):
        char = text[index]
        if index == cursor_index:
            screen.addch(y, x, char, curses.A_REVERSE)
        else:
            screen.addch(y, x, char, curses.A_NORMAL)
        x += 1

    if cursor_index == len(text):
        screen.addch(y, x, " ", curses.A_REVERSE)
        x += 1


def get_cursor_index(context):
    return context.get("cursor_index", 0)


def get_text_length(context):
    if "text" in context:
        return len(context["text"])
    else:
        return -1


def get_x(context):
    return context.get("x", 0)


def print_text_line(screen, context, start_index, remaining_height):
    screen.addstr(start_index, get_x(context), context["text"])

    return context["fixed_size"]