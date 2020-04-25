import functools
import traceback
from collections import defaultdict
from enum import Enum
from queue import Queue

from CentralDispatch import CentralDispatch


class StopApplication:
    def __init__(self, exception=None):
        self.exception = exception


class ExceptionOccured:
    def __init__(self, exception):
        self.exception = exception


class KeyStroke:
    def __init__(self, key):
        self.key = key


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


class Segue(Enum):
    PUSH = 0
    REPLACE = 1


class Application:
    def __init__(self, curses_screen):
        self.curses_screen = curses_screen
        self.event_subscribers = defaultdict(set)
        self.stack = []

        self.event_queue = Queue()

        self.shutdown_signal = None
        self.main_thread = CentralDispatch.create_serial_queue()

    def handle_shutdown(self, shutdown_event):
        if shutdown_event.exception:
            try:
                raise shutdown_event.exception
            except Exception as e:
                print("Shutdown because of error:")
                print(f"{e.__class__.__name__}: {e}")
                print(traceback.format_exc())
        else:
            print("Exited Normally")

    def subscribe(self, event_type, delegate):
        self.event_subscribers[event_type].add(delegate)

    def unsubscribe(self, event_type, delegate):
        self.event_subscribers[event_type].remove(delegate)

    def unsubscribe_all(self, delegate):
        for event_type in self.event_subscribers:
            self.unsubscribe(event_type, delegate)

    def start(self, activity: Activity):
        self.subscribe(event_type=ExceptionOccured, delegate=self)
        CentralDispatch.default_exception_handler = self._shutdown_app_exception_handler
        self.shutdown_signal = CentralDispatch.future(self._event_monitor)
        self.start_key_monitor()
        self.on_start()

        self.segue_to(activity)
        shutdown_event = self.shutdown_signal.result()

        self.handle_shutdown(shutdown_event)

    def on_start(self): pass

    def _stop_activity(self, activity):
        activity._stop()
        self.unsubscribe_all(activity)

    def _start_activity(self, activity):
        activity._start(application=self)

    def _segue_to(self, activity: Activity, seque_type=Segue.REPLACE):
        if len(self.stack) > 0:
            if seque_type == Segue.REPLACE:
                current_activity = self.stack.pop()
            else:
                current_activity = self.stack[-1]

            current_activity._stop()
            current_activity.on_stop()
            self.unsubscribe_all(current_activity)

        self.stack.append(activity)
        activity._start(application=self)
        activity.on_start()

    def segue_to(self, activity: Activity):
        self.main_thread.submit_async(self._segue_to, activity)

    def _pop_activity(self):
        current_activity = self.stack.pop()
        if len(self.stack) > 0:
            returning_activity = self.stack[-1]

            self._stop_activity(current_activity)
            self._start_activity(returning_activity)
        else:
            # We've popped the last activity
            self.event_queue.put(StopApplication())

    def pop_activity(self):
        self.main_thread.submit_async(self._pop_activity)

    def _dispatch_event(self, subscriber, event):
        subscriber.on_event(event)

    def dispatch_event(self, event):
        for subscriber in self.event_subscribers[type(event)]:
            self.main_thread.submit_async(self._dispatch_event, subscriber, event)

    def _event_monitor(self):
        event = self.event_queue.get()

        while not isinstance(event, StopApplication):
            self.dispatch_event(event)
            event = self.event_queue.get()

        # Return the last even, because it might contain an exception
        return event

    def _key_monitor(self, screen):
        while not self.shutdown_signal.done():
            key = screen.getch()

            # 3 = ctrl-c
            if key == 3:
                self.event_queue.put(StopApplication())
                return
            else:
                self.event_queue.put(KeyStroke(key))

    def start_key_monitor(self):
        CentralDispatch.future(self._key_monitor, self.curses_screen)

    def _debug_message(self, lines):
        self.curses_screen.clear()
        for index, line in enumerate(lines):
            self.curses_screen.addstr(index, 0, line)

        self.curses_screen.refresh()

    def debug_message(self, message: str):
        lines = message.split("\n")

        self.main_thread.submit_async(self._debug_message, lines)

    def on_event(self, event):
        if isinstance(event, ExceptionOccured):
            self.event_queue.put(StopApplication(exception=event.exception))

    def _shutdown_app_exception_handler(self, function):
        def inner_function(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except Exception as e:
                self.event_queue.put(StopApplication(exception=e))

        return inner_function
