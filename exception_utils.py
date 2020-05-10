def try_make_lines(context, remaining_height):
    try:
        line_printers = context["line_generator"](context, remaining_height)
        return line_printers
    except Exception as e:
        raise Exception("problem with line generator {}, context={}".format(context["line_generator"], context)) from e


def try_print_line(line_printer, screen, y):
    try:
        line_printer(screen, y)
    except Exception as e:
        raise Exception("problem with line printer {}".format(line_printer)) from e
