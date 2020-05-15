import curses
from queue import Queue

from loguru import logger

import Keys
from ContextUtils import get_text, get_cursor_index, get_text_length, scroll_up, scroll_down


class UIEvent:
    def __init__(self, ui_element):
        self.ui_element = ui_element


class TextBoxChange(UIEvent): pass


class TextBoxSubmit(UIEvent): pass


class ScrollChange(UIEvent): pass


def handle_text_box_input(ui_element: str, input_context, event, event_queue: Queue):
    """
    Handles basic text input, cursor movement, shortcut keys
    """
    text = get_text(input_context)
    key = event.key

    if 32 <= key <= 126:
        i = get_cursor_index(input_context)
        if get_text_length(input_context) >= 0:
            input_context["text"] = text[:i] + chr(key) + text[i:]
        else:
            input_context["text"] = chr(key)
        input_context["cursor_index"] = get_cursor_index(input_context) + 1
        event_queue.put(TextBoxChange(ui_element=ui_element))

    if key == Keys.BACKSPACE:
        i = get_cursor_index(input_context)
        if i > 0:
            input_context["text"] = text[:i - 1] + text[i:]
            input_context["cursor_index"] = get_cursor_index(input_context) - 1
            event_queue.put(TextBoxChange(ui_element=ui_element))

    if event.key == curses.KEY_LEFT:
        if get_cursor_index(input_context) > 0:
            input_context["cursor_index"] = get_cursor_index(input_context) - 1

    elif event.key == curses.KEY_RIGHT:
        if get_cursor_index(input_context) < get_text_length(input_context):
            input_context["cursor_index"] = get_cursor_index(input_context) + 1

    if event.key == curses.CTL_LEFT:
        input_context["cursor_index"] = get_cursor_index(input_context)
        text = get_text(input_context)

        while input_context["cursor_index"] > 0 and text[input_context["cursor_index"] - 1] != " ":
            input_context["cursor_index"] = input_context["cursor_index"] - 1

        while input_context["cursor_index"] > 0 and text[input_context["cursor_index"] - 1] == " ":
            input_context["cursor_index"] = input_context["cursor_index"] - 1

    elif event.key == curses.CTL_RIGHT:
        input_context["cursor_index"] = get_cursor_index(input_context)
        text = get_text(input_context)

        while input_context["cursor_index"] < len(text) and text[input_context["cursor_index"] - 1] != " ":
            input_context["cursor_index"] = input_context["cursor_index"] + 1

        while input_context["cursor_index"] < len(text) and text[input_context["cursor_index"] - 1] == " ":
            input_context["cursor_index"] = input_context["cursor_index"] + 1

    elif event.key == curses.KEY_HOME:
        input_context["cursor_index"] = 0

    elif event.key == curses.KEY_END:
        input_context["cursor_index"] = len(text)

    elif event.key == Keys.ENTER:
        input_context["cursor_index"] = len(text)
        event_queue.put(TextBoxSubmit(ui_element=ui_element))


def handle_scroll_list_input(ui_element: str, scroll_context, event, event_queue: Queue):
    if event.key == curses.KEY_UP:
        scroll_up(scroll_context)
    if event.key == curses.KEY_DOWN:
        scroll_down(scroll_context)

    event_queue.put(ScrollChange(ui_element))
