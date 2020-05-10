import curses

import Keys
from Activity import Activity
from ContextUtils import scroll_up, scroll_down
from EventTypes import KeyStroke
from input_handlers import handle_text_box_input, handle_scroll_list_input
from printers import make_top_bar, make_scroll_list, make_text_input
from loguru import logger

class LogViewerActivity(Activity):

    def __init__(self):
        super().__init__()
        self.tab_order = ["log_output", "search_bar"]

        self.focus = "log_output"

    def on_start(self):
        self.application.subscribe(KeyStroke, self)

        self.display_state = {"top_bar": {"items": {"title": "Application Log",
                                                    "help": "Press ESC to go back"},
                                          "fixed_size": 2,
                                          "line_generator": make_top_bar},
                              "log_output": {"items": [("woah", 1)],
                                             "line_generator": make_scroll_list,
                                             "input_handler": handle_scroll_list_input},
                              "search_bar": {"label": "Search",
                                             "line_generator": make_text_input,
                                             "fixed_size": 1,
                                             "input_handler": handle_text_box_input}}

        self.display_state[self.focus]["focused"] = True

    def on_event(self, event):
        if isinstance(event, KeyStroke):
            focused_context = self.display_state[self.focus]
            input_handler = focused_context["input_handler"]
            input_handler(focused_context, event)

            if event.key == Keys.ENTER:
                logger.info(self.display_state["search_bar"]["text"])
                self.display_state["log_output"]["items"].append((self.display_state["search_bar"]["text"], 1))

            if event.key == Keys.ESC:
                self.application.pop_activity()

            if event.key == Keys.TAB:
                focused_context["focused"] = False
                self.focus = self.tab_order[(self.tab_order.index(self.focus) + 1) % len(self.tab_order)]
                self.display_state[self.focus]["focused"] = True

            self.refresh_screen()

