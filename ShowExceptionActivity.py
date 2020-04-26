import curses
import random
import traceback

import Keys
from EventTypes import KeyStroke
from Activity import Activity
from printers import print_top_bar, print_scroll_list, scroll_up, scroll_down, print_bottom_bar, print_multiline_text

admonishments = [
    "Please try harder next time.",
    "Typical...",
    "Ugh, Again?",
    "Really? You're better than this",
    "Good thing I was here to catch it",
    "Won't be the last time!",
    "Computers are terrible."
]


class ShowExceptionActivity(Activity):
    def __init__(self, exception):
        super().__init__()
        self.exception = exception

    def on_start(self):
        self.application.subscribe(KeyStroke, self)
        try:
            raise self.exception
        except Exception as e:
            exception_text = f"{e.__class__.__name__}: {e}\n\n{traceback.format_exc()}"

        admonishment = random.choice(admonishments)

        self.display_state = {"top_bar": {"items": {"title": "App has caught an exception",
                                                    "help": "Press ESC to try and go back"},
                                          "fixed_size": 2,
                                          "print_fn": print_top_bar},
                              "exception_text": {"text": exception_text,
                                                 "selected": None,
                                                 "print_fn": print_multiline_text},
                              "bottom_bar": {"items": {"admonishment": admonishment},
                                             "fixed_size": 2,
                                             "print_fn": print_bottom_bar}}

    def on_stop(self):
        self.application.last_exception = None

    def on_event(self, event):
        if isinstance(event, KeyStroke):
            if event.key == Keys.ESC:
                self.application.pop_activity()

            if event.key == curses.KEY_UP:
                scroll_up(self.display_state["exception_text"])
            if event.key == curses.KEY_DOWN:
                scroll_down(self.display_state["exception_text"])
            self.refresh_screen()
