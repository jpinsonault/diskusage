import curses
from functools import partial

import Keys
from Activity import Activity
from ContextUtils import get_text, get_cursor_index, get_text_length
from EventTypes import KeyStroke
from printers import print_text_input, make_top_bar, print_line


class TextInputTest(Activity):
    def __init__(self):
        super().__init__()

    def on_start(self):
        self.application.subscribe(KeyStroke, self)

        self.display_state = {"top_bar": {"items": {"title": "Type some stuff"},
                                          "fixed_size": 2,
                                          "line_generator": make_top_bar},
                              "text_input": {"label": "What's your name?",
                                             "size": 30,
                                             "x": 0,
                                             "focus": True,
                                             "fixed_size": 1,
                                             "input_handler": self.handle_text_box_input,
                                             "line_generator": self.make_text_input}}

    def make_text_input(self, context, remaining_height):
        return [partial(print_text_input, 0, context)]

    def on_event(self, event):
        if isinstance(event, KeyStroke):
            self.handle_ui_input(event)

            if event.key == Keys.ESC:
                self.application.pop_activity()

    def handle_text_box_input(self, input_context, event):
        text = get_text(input_context)
        key = event.key

        if 32 <= key <= 126:
            i = get_cursor_index(input_context)
            if get_text_length(input_context) >= 0:
                input_context["text"] = text[:i] + chr(key) + text[i:]
            else:
                input_context["text"] = chr(key)
            input_context["cursor_index"] = get_cursor_index(input_context) + 1
        if key == Keys.BACKSPACE:
                i = get_cursor_index(input_context)
                input_context["text"] = text[:i - 1] + text[i:]
                input_context["cursor_index"] = get_cursor_index(input_context) - 1

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
            def update_ui():
                def make_line(context, _):
                    return [partial(print_line, 0, f"Hello {get_text(context)}")]

                # Dynamically add in ui elements
                self.display_state["response"] = {"line_generator": make_line,
                                                  "text": get_text(input_context),
                                                  "fixed_size": 1}

                self.refresh_screen()

            # Hell yes dispatch queues
            self.main_thread.submit_async(update_ui)

        self.refresh_screen()

