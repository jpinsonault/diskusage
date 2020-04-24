from collections import defaultdict
from queue import Queue

from CentralDispatch import CentralDispatch


class StopApplication: pass


class KeyStroke:
    def __init__(self, key):
        self.key = key


class Activity:
    def __init__(self):
        self.application = None
        self.display_state = {}
        self.previous_display_state = {}

    def start(self, application):
        self.application = application

    def on_start(self): pass

    def stop(self):
        self.application = None

    def on_stop(self): pass

    def on_event(self, event: object): pass

    def refresh_screen(self):
        screen = self.application.curses_screen
        screen.clear()
        num_rows, num_cols = self.application.curses_screen.getmaxyx()

        next_y_index = 0

        for view, context in self.display_state.items():
            used_lines = context["print_fn"](screen, context, next_y_index)
            next_y_index += used_lines

            if next_y_index >= num_rows:
                break

        screen.refresh()
        self.previous_display_state = self.display_state


class Application:
    def __init__(self, curses_screen):
        self.curses_screen = curses_screen
        self.event_subscribers = defaultdict(set)
        self.current_activity = None

        self.event_queue = Queue()

        self.shutdown_signal = None
        self.main_thread = CentralDispatch.create_serial_queue()

    def subscribe(self, event_type, activity: Activity):
        self.event_subscribers[event_type].add(activity)

    def unsubscribe(self, event_type, activity: Activity):
        self.event_subscribers[event_type].remove(activity)

    def unsubscribe_all(self, activity: Activity):
        for event_type in self.event_subscribers:
            self.unsubscribe(event_type, activity)

    def start(self, activity: Activity):
        self.shutdown_signal = CentralDispatch.future(self._event_monitor)
        self.start_key_monitor()
        self.on_start()

        self.segue_to(activity)
        self.shutdown_signal.result()

    def on_start(self): pass

    def _segue_to(self, activity: Activity):
        if self.current_activity is not None:
            self.current_activity.stop()
            self.current_activity.on_stop()

        self.current_activity = activity
        activity.start(application=self)
        activity.on_start()

    def segue_to(self, activity: Activity):
        self.main_thread.submit_async(self._segue_to, activity)

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

    def _key_monitor(self, screen):
        # TODO hook up the shutdown signal
        while True:
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
        pass
