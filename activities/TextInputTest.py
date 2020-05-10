import curses
from functools import partial

import Keys
from Activity import Activity
from ContextUtils import get_text, get_cursor_index, get_text_length
from EventTypes import KeyStroke
from input_handlers import handle_text_box_input
from printers import print_text_input, make_top_bar, print_line, make_text_input


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
                                             "fixed_size": 1,
                                             "line_generator": make_text_input}}

    def on_event(self, event):
        if isinstance(event, KeyStroke):
            self.handle_text_box_input(self.display_state["text_input"], event)

            if event.key == Keys.ESC:
                self.application.pop_activity()

    def handle_text_box_input(self, input_context, event):
        handle_text_box_input(input_context, event)

        if event.key == Keys.ENTER:
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

