from ContextUtils import get_fixed_size
from exception_utils import try_make_lines, try_print_line


class Activity:
    def __init__(self):
        self.application = None
        self.event_queue = None
        self.screen = None
        self.main_thread = None
        self.display_state = {}
        self.previous_display_state = {}

    def _start(self, application):
        self.application = application
        self.event_queue = application.event_queue
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

    def generate_line_printers(self) -> [callable]:
        num_rows, num_cols = self.application.curses_screen.getmaxyx()

        next_y_index = 0

        total_fixed_size = sum(get_fixed_size(context) for _, context in self.display_state.items())
        remaining_height = num_rows - total_fixed_size

        screen_line_printers = []
        for key, context in self.display_state.items():
            fixed_size = get_fixed_size(context)

            line_printers = try_make_lines(context, remaining_height)
            screen_line_printers += line_printers

            next_y_index += len(line_printers)

            # 0 = it doesn't have a fixed size
            if fixed_size == 0:
                remaining_height -= len(line_printers)

            if next_y_index >= num_rows:
                break

        return screen_line_printers

    def refresh_screen(self):
        screen = self.application.curses_screen
        screen_line_printers = self.generate_line_printers()

        screen.clear()
        for y, line_printer in enumerate(screen_line_printers):
            try_print_line(line_printer, screen, y)

        screen.refresh()

        self.previous_display_state = self.display_state

