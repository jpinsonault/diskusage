import curses

import Keys
from ScreenLine import ScreenLine
from Activity import Activity
from EventTypes import KeyStroke
from printers import print_top_bar, get_text, print_text_input, get_cursor_index, get_text_length, print_text_line


class TextInputTest(Activity):
    def __init__(self):
        super().__init__()

    def on_start(self):
        self.application.subscribe(KeyStroke, self)

        self.display_state = {"top_bar": {"items": {"title": "Type some stuff"},
                                          "fixed_size": 2,
                                          "print_fn": print_top_bar},
                              "text_input": {"label": "What's your name?",
                                             "size": 30,
                                             "x": 0,
                                             "focus": True,
                                             "fixed_size": 1,
                                             "input_handler": self.handle_text_box_input,
                                             "print_fn": self.print_text_input}}

    def print_text_input(self,screen, context, start_index, remaining_height):
        line = ScreenLine(context, 0, print_fn=print_text_input)
        line.print_to(screen, start_index)

        return context["fixed_size"]


    def on_event(self, event):
        if isinstance(event, KeyStroke):
            self.handle_ui_input(event)

            if event.key == Keys.ESC:
                self.application.pop_activity()

    def handle_text_box_input(self, context, event):
        text = get_text(context)
        key = event.key

        if 32 <= key <= 126:
            i = get_cursor_index(context)
            if get_text_length(context) >= 0:
                context["text"] = text[:i] + chr(key) + text[i:]
            else:
                context["text"] = chr(key)
            context["cursor_index"] = get_cursor_index(context) + 1
        if key == Keys.ESC:
            self.application.pop_activity()
        if key == Keys.BACKSPACE:
            if len(context["text"]) > 0:
                i = get_cursor_index(context)
                context["text"] = text[:i-1] + text[i:]
                context["cursor_index"] = get_cursor_index(context) - 1

        if event.key == curses.KEY_LEFT:
            print(get_cursor_index(context))
            if get_cursor_index(context) > 0:
                context["cursor_index"] = get_cursor_index(context) - 1
                print(get_cursor_index(context))

        elif event.key == curses.KEY_RIGHT:
            print(get_cursor_index(context))
            if get_cursor_index(context) < get_text_length(context):
                context["cursor_index"] = get_cursor_index(context) + 1
                print(get_cursor_index(context))

        if event.key == curses.CTL_LEFT:
            context["cursor_index"] = get_cursor_index(context)
            text = get_text(context)

            print(text, len(text), context["cursor_index"])
            while context["cursor_index"] > 0 and text[context["cursor_index"] - 1] != " ":
                context["cursor_index"] = context["cursor_index"] - 1

            while context["cursor_index"] > 0 and text[context["cursor_index"] - 1] == " ":
                context["cursor_index"] = context["cursor_index"] - 1

        elif event.key == curses.CTL_RIGHT:
            context["cursor_index"] = get_cursor_index(context)
            text = get_text(context)

            print(text, len(text), context["cursor_index"])
            while context["cursor_index"] < len(text) and text[context["cursor_index"] - 1] != " ":
                context["cursor_index"] = context["cursor_index"] + 1

            while context["cursor_index"] < len(text) and text[context["cursor_index"] - 1] == " ":
                context["cursor_index"] = context["cursor_index"] + 1

        elif event.key == curses.KEY_HOME:
            context["cursor_index"] = 0

        elif event.key == curses.KEY_END:
            context["cursor_index"] = len(text)

        elif event.key == Keys.ENTER:
            # Dynamically add in ui elements
            def update_ui():
                self.display_state["response"] = {"print_fn": print_text_line,
                                                  "text": f"Hello {get_text(context)}",
                                                  "fixed_size": 1}

                self.refresh_screen()

            # Hell yes dispatch queues
            self.main_thread.submit_async(update_ui)

        self.refresh_screen()

