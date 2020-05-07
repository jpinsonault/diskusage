from ContextUtils import get_fixed_size


class Activity:
    def __init__(self):
        self.application = None
        self.screen = None
        self.main_thread = None
        self.display_state = {}
        self.previous_display_state = {}

    def _start(self, application):
        self.application = application
        self.screen = application.curses_screen
        self.main_thread = application.main_thread
        self.on_start()
        self.refresh_screen()

    def on_start(self): pass

    def _stop(self):
        self.on_stop()
        self.application = None

    def on_stop(self): pass

    def on_event(self, event: object): pass

    def handle_ui_input(self, event):
        for name, context in self.display_state.items():
            if context.get("focus", False):
                context["input_handler"](context, event)

    def refresh_screen(self):
        screen = self.application.curses_screen
        screen.clear()
        num_rows, num_cols = self.application.curses_screen.getmaxyx()

        next_y_index = 0

        total_fixed_size = sum(get_fixed_size(context) for _, context in self.display_state.items())

        screen_line_printers = []
        for key, context in self.display_state.items():
            fixed_size = get_fixed_size(context)
            remaining_height = (num_rows - total_fixed_size) + fixed_size

            line_printers = self._try_make_line(context, remaining_height)
            screen_line_printers += line_printers

            next_y_index += len(line_printers)

            if next_y_index >= num_rows:
                break

        for y, line_printer in enumerate(screen_line_printers):
            self._try_print_line(line_printer, screen, y)

        screen.refresh()
        self.previous_display_state = self.display_state

    def _try_make_line(self, context, remaining_height):
        try:
            line_printers = context["line_generator"](context, remaining_height)
            return line_printers
        except Exception as e:
            print("problem with line generator {}, context={}".format(context["line_generator"], context))
            raise e

    def _try_print_line(self, line_printer, screen, y):
        try:
            line_printer(screen, y)
        except Exception as e:
            print("problem with line printer {}".format(line_printer))
            raise e
