import curses

import Keys
from Activity import Activity
from ContextUtils import scroll_up, scroll_down
from EventTypes import KeyStroke
from printers import make_top_bar, make_scroll_list


class ExampleActivity(Activity):
    def __init__(self):
        super().__init__()

    def on_start(self):
        self.application.subscribe(KeyStroke, self, self.on_key_stroke)

        self.display_state = {"top_bar": {"items": {"title": "Example"},
                                          "fixed_size": 2,
                                          "line_generator": make_top_bar},
                              "some_text_lines": {"items": [(0, "Hello"), (1, "World")],
                                               "line_generator": make_scroll_list}}

    def on_key_stroke(self, event: KeyStroke):
        if event.key == Keys.ESC:
            self.application.pop_activity()

        if event.key == curses.KEY_UP:
            scroll_up(self.display_state["command_list"])
        if event.key == curses.KEY_DOWN:
            scroll_down(self.display_state["command_list"])
        self.refresh_screen()