import curses


def default_line_printer(screen, context, screen_line, y):
    screen.addstr(y, screen_line.x, screen_line.text, screen_line.mode)


# A print item is line of text. It has
class PrintItem:
    def __init__(self, context):
        self.context = context

    def print_to(self, screen, y):
        self.print_fn(screen, y, self.context)