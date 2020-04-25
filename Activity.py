class Activity:
    def __init__(self):
        self.application = None
        self.display_state = {}
        self.previous_display_state = {}

    def _start(self, application):
        self.application = application
        self.on_start()
        self.refresh_screen()

    def on_start(self): pass

    def _stop(self):
        self.on_stop()
        self.application = None

    def on_stop(self): pass

    def on_event(self, event: object): pass

    def refresh_screen(self):
        screen = self.application.curses_screen
        screen.clear()
        num_rows, num_cols = self.application.curses_screen.getmaxyx()

        next_y_index = 0

        total_fixed_size = sum(context.get("fixed_size", 0) for _, context in self.display_state.items())

        for view, context in self.display_state.items():
            remaining_height = (num_rows - total_fixed_size) + context.get("fixed_size", 0)
            used_lines = context["print_fn"](screen, context, next_y_index, remaining_height)
            next_y_index += used_lines

            if next_y_index >= num_rows:
                break

        screen.refresh()
        self.previous_display_state = self.display_state
