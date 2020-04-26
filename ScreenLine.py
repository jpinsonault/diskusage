import curses


def default_line_printer(screen, context, screen_line, y):
    screen.addstr(y, screen_line.x, screen_line.text, screen_line.mode)


class ScreenLine:
    def __init__(self, context, x, text=None, mode=curses.A_NORMAL, print_fn=default_line_printer):
        self.context = context
        self.x = x
        self.text = text
        self.mode = mode
        self.print_fn = print_fn

    def print_to(self, screen, y):
        self.print_fn(screen, self.context, self, y)