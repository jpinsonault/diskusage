import curses
from itertools import islice


def print_top_bar(screen, context, start_index, remaining_height):
    items = [text for key, text in context["items"].items()]
    screen.addstr(start_index, 0, " | ".join(items), curses.A_BOLD)
    return context["fixed_size"]


def print_bottom_bar(screen, context, start_index, remaining_height):
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
def get_selected(index, items):
    if index is None: return None

    if 0 <= index <= len(items):
        return items[index]
    else:
        return None


def cut_items_to_window(selected_index, items, window_size):
    start, stop = start_stop(selected_index, window_size, len(items))
    return islice(items, start, stop)


def default_item_printer(screen, y_index, item, mode):
    screen.addstr(y_index, 0, str(item), mode)


def print_scroll_list(screen, context, start_index, remaining_height, item_printer=default_item_printer):
    selected_item = get_selected(context["selected"], context["commands"])

    y_index = start_index
    visible_items = cut_items_to_window(context["selected"], context["commands"], remaining_height)

    for item in visible_items:
        if item == selected_item:
            mode = curses.A_REVERSE
        else:
            mode = curses.A_NORMAL

        item_printer(screen, y_index, item, mode)
        y_index += 1

    return y_index - start_index
