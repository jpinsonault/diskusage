import curses
import threading
from itertools import islice

from Application import Activity, KeyStroke
from FolderScanApp import ScanResult
from folder import Folder


class FolderScanActivity(Activity):
    def __init__(self):
        super().__init__()
        self.display_state = {"y_index": 0,
                              "selected_line": 0}

        self.counter = 0

    def on_start(self):
        self.application.subscribe(event_type=KeyStroke, activity=self)

        self._refresh_timer()

    def on_stop(self):
        self.application.unsubscribe(event_type=KeyStroke, activity=self)

    def on_event(self, event):
        if isinstance(event, KeyStroke):
            if event.key == curses.KEY_UP:
                self.display_state["selected_line"] = max(0, self.display_state["selected_line"] - 1)
            elif event.key == curses.KEY_DOWN:
                rows, cols = self.application.curses_screen.getmaxyx()
                self.display_state["selected_line"] = min(rows, self.display_state["selected_line"] + 1)

            self.refresh_display()

    def _refresh_timer(self):
        thread = threading.Timer(1.0, self._refresh_timer)
        thread.daemon = True
        thread.start()

        self.refresh_display()

    def refresh_display(self):
        screen = self.application.curses_screen
        screen.clear()
        self.display_state["y_index"] = 0

        self._print_folder_tree(screen, self.application.folder_scan_tree, to_depth=2)

        screen.refresh()

    def _print_folder_tree(self, screen, folder: Folder, to_depth: int, current_depth: int = 0):
        if current_depth <= to_depth:
            size_gb = folder.folder_stats.size/pow(1024, 3)
            y_index = self.display_state["y_index"]
            if y_index == self.display_state["selected_line"]:
                mode = curses.A_REVERSE
            else:
                mode = curses.A_NORMAL

            text = "{size:.2f}GB - {name}".format(size=size_gb, name=folder.path)
            screen.addstr(y_index, current_depth*2, text, mode)

            self.display_state["y_index"] += 1
            sub_folders = sorted(folder.folders, key=lambda f: f.folder_stats.size, reverse=True)
            for sub_folder in islice(sub_folders, min(4, len(sub_folders))):
                self._print_folder_tree(screen, sub_folder,
                                        to_depth=to_depth,
                                        current_depth=current_depth + 1)
