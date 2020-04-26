import time


def animate_line(screen, screen_line):
    start = time.time_ns()

    time_delta = time.time_ns() - start
    while time_delta < 5000:
