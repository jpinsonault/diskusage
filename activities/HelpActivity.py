import curses
from functools import partial

from loguru import logger

import Keys
from EventTypes import KeyStroke
from Activity import Activity
from printers import make_scroll_list, make_top_bar
from ContextUtils import scroll_up, scroll_down

commands = [
    "Up/Down | Navigate around",
    "[       | Collapse tree up one level",
    "]       | Expand tree one level lower",
    "h       | Show this help",
    "F1      | Show application log",
    "Ctrl-C  | Exit the program"
]


class HelpActivity(Activity):
    def __init__(self):
        super().__init__()

    def on_start(self):
        self.application.subscribe(KeyStroke, self, self.on_key_stroke)

        self.display_state = {"top_bar": {"items": {"title": "Command help",
                                                    "message": "Press ESC to return"},
                                          "fixed_size": 2,
                                          "line_generator": make_top_bar},
                              "command_list": {"items": commands,
                                               "focused": True,
                                               "line_generator": make_scroll_list}}

    def on_key_stroke(self, event: KeyStroke):
        if event.key == Keys.ESC:
            self.application.pop_activity()

        if event.key == curses.KEY_UP:
            scroll_up(self.display_state["command_list"])
        if event.key == curses.KEY_DOWN:
            scroll_down(self.display_state["command_list"])
        self.refresh_screen()
