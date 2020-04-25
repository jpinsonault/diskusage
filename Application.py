import traceback
from collections import defaultdict
from enum import Enum
from queue import Queue

from Activity import Activity
from CentralDispatch import CentralDispatch
from EventTypes import StopApplication, ExceptionOccured, KeyStroke
from ShowExceptionActivity import ShowExceptionActivity


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
        self.main_thread = None

        self.last_exception = None

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
        try:
            self.event_subscribers[event_type].remove(delegate)
        except KeyError:
            pass

    def unsubscribe_all(self, delegate):
        for event_type in self.event_subscribers:
            self.unsubscribe(event_type, delegate)

    def redirect_stdout(self):
        pass

    def start(self, activity: Activity):
        self.redirect_stdout()
        CentralDispatch.default_exception_handler = self._shutdown_app_exception_handler

        self.main_thread = CentralDispatch.create_serial_queue()
        self.subscribe(event_type=ExceptionOccured, delegate=self)
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

    def _segue_to(self, activity: Activity, segue_type):
        if len(self.stack) > 0:
            if segue_type == Segue.REPLACE:
                current_activity = self.stack.pop()
            else:
                current_activity = self.stack[-1]

            current_activity._stop()
            current_activity.on_stop()
            self.unsubscribe_all(current_activity)

        self.stack.append(activity)
        activity._start(application=self)

    def segue_to(self, activity: Activity, segue_type=Segue.PUSH):
        self.main_thread.submit_async(self._segue_to, activity, segue_type=segue_type)

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

        # Return the last event, because it might contain an exception
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
            if self.last_exception is not None:
                print("While handling one exception, another occurred:")
                self.event_queue.put(StopApplication(exception=event.exception))
            else:
                self.last_exception = event.exception
                self.segue_to(ShowExceptionActivity(event.exception), segue_type=Segue.PUSH)

    def _shutdown_app_exception_handler(self, function):
        def inner_function(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except Exception as e:
                self.event_queue.put(ExceptionOccured(exception=e))

        return inner_function
