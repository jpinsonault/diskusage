import curses
import time
from concurrent.futures import Future
from functools import partial

import Keys
from Activity import Activity
from CentralDispatch import CentralDispatch
from ContextUtils import scroll_up, scroll_down, scroll_to_bottom, get_selected_index, get_items_len
from EventTypes import KeyStroke
from input_handlers import handle_text_box_input, handle_scroll_list_input, TextBoxSubmit, ScrollChange
from printers import make_top_bar, make_scroll_list, make_text_input, make_spacer, make_bottom_bar, make_multiline_text, \
    make_text_editor
from loguru import logger


class TextEditorActivity(Activity):

    def __init__(self):
        super().__init__()
        self.stop_signal = False
        self.log_watcher: Future = None

    def on_start(self):
        self.application.subscribe(KeyStroke, self, self.on_key_stroke)
        self.application.subscribe(TextBoxSubmit, self, self.on_enter_pressed)
        self.application.subscribe(ScrollChange, self, self.on_scroll_change)

        self.display_state = {
            "editor": {"items": [],
                       "line_generator": partial(make_text_editor, self.screen),
                       "input_handler": handle_text_editor_input},
            "spacer": {"line_generator": make_spacer},
            "search_bar": {"label": "Search",
                           "fixed_size": 1,
                           "line_generator": make_text_input,
                           "input_handler": handle_text_box_input},
            "bottom_bar": {"items": {},
                           "fixed_size": 2,
                           "line_generator": make_bottom_bar}
        }

        self.display_state[self.focus]["focused"] = True
        self.log_watcher = CentralDispatch.future(self._run_log_watcher, self.application.log_filename)

    def on_stop(self):
        self.stop_signal = True
        self.log_watcher.result()

    def update_scroll_percent(self):
        log_context = self.display_state["log_output"]
        bottom_context = self.display_state["bottom_bar"]
        index = get_selected_index(log_context)
        num_items = get_items_len(log_context)

        if num_items is not None:
            percent = int((index/num_items)*100)
        else:
            percent = 0

        bottom_context["items"]["scroll_percent"] = f"Scroll: {percent}%"
        self.refresh_screen()

    def on_new_log_line(self, line):
        log_context = self.display_state["log_output"]
        log_items = log_context["items"]
        is_at_bottom = get_selected_index(log_context) == len(log_items) - 1
        log_items.append(line)

        if is_at_bottom:
            scroll_to_bottom(log_context)
        self.display_state["bottom_bar"]["items"]["num_lines"] = f"Lines: {len(log_items)}"
        self.refresh_screen()

    def on_new_log_lines(self, lines):
        log_items = self.display_state["log_output"]["items"]
        for line in lines:
            log_items.append(line)

        scroll_to_bottom(self.display_state["log_output"])
        self.display_state["bottom_bar"]["items"]["num_lines"] = f"Lines: {len(log_items)}"
        self.refresh_screen()

    def on_enter_pressed(self, event: TextBoxSubmit):
        text = self.display_state["search_bar"]["text"]
        logger.info(f"You just pressed enter: {text}")

    def on_key_stroke(self, event: KeyStroke):
        focused_context = self.display_state[self.focus]
        input_handler = focused_context["input_handler"]
        input_handler(self.focus, focused_context, event, self.event_queue)

        if event.key == Keys.ESC:
            self.application.pop_activity()

        if event.key == Keys.TAB:
            logger.info("You pressed tab!")
            focused_context["focused"] = False
            self.focus = self.tab_order[(self.tab_order.index(self.focus) + 1) % len(self.tab_order)]
            self.display_state[self.focus]["focused"] = True

        self.refresh_screen()

    def on_scroll_change(self, event: ScrollChange):
        self.update_scroll_percent()

    def _run_log_watcher(self, log_filename):
        """This is my favorite function"""
        with open(log_filename, 'r') as log_file:
            starting_lines = []
            where = log_file.tell()
            line = log_file.readline()

            while line:
                starting_lines.append(line.strip())
                where = log_file.tell()
                line = log_file.readline()
            log_file.seek(where)

            self.main_thread.submit_async(self.on_new_log_lines, starting_lines)

            while not (self.stop_signal or self.application.shutdown_signal.done()):
                lines = []
                where = log_file.tell()
                line = log_file.readline()

                while line:
                    lines.append(line.strip())
                    where = log_file.tell()
                    line = log_file.readline()
                log_file.seek(where)
                if len(lines) > 0:
                    self.main_thread.submit_async(self.on_new_log_lines, lines)
                time.sleep(.1)