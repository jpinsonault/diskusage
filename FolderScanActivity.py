import curses
import threading
from itertools import islice

import Keys
from Application import Activity, KeyStroke
from FolderScanApp import ScanComplete, ScanStarted
from foldercore import breadth_first


def print_top_bar(screen, context, start_index, remaining_height):
    items = [text for key, text in context["items"].items()]
    screen.addstr(start_index, 0, " | ".join(items), curses.A_BOLD)
    return context["fixed_size"]


def print_bottom_bar(screen, context, start_index, remaining_height):
    num_rows, num_cols = screen.getmaxyx()
    items = [text for key, text in context["items"].items()]

    screen.addstr(num_rows-1, 0, " | ".join(items), curses.A_BOLD)
    return context["fixed_size"]


def start_stop(index, window_size, list_size):
    if window_size % 2 == 0:
        up = window_size//2
        down = window_size//2 - 1
    else:
        up = window_size//2
        down = window_size//2

    # if topped out
    if index - up < 0:
        return 0, min(window_size, list_size)
    # if bottomed out
    elif index + down > list_size:
        return max(0, list_size-window_size), list_size
    else:
        return index - up, index + down+1


def print_folder_tree(screen, context, start_index, remaining_height):
    folders = [folder for folder, _ in context["folder_data"]]

    while context["selected_folder"] is not None and context["selected_folder"] not in folders:
        context["selected_folder"] = context["selected_folder"].parent

    selected_index = 0

    if context["selected_folder"] is not None:
        selected_index = folders.index(context["selected_folder"])

    start, stop = start_stop(selected_index, remaining_height, len(folders))
    print(f"index: {selected_index}, window_size: {remaining_height}, list_size: {len(folders)}, start: {start}, stop: {stop}")
    y_index = start_index
    for folder, depth in islice(context["folder_data"], start, stop):
        size_gb = folder.folder_stats.size / pow(1024, 3)

        if folder == context["selected_folder"]:
            mode = curses.A_REVERSE
        else:
            mode = curses.A_NORMAL

        text = "{size:.2f}GB - {name}".format(size=size_gb, name=folder.path)
        screen.addstr(y_index, depth * 2, text, mode)
        y_index += 1

    return y_index - start_index


class FolderScanActivity(Activity):
    def __init__(self):
        super().__init__()

    def on_start(self):
        self.application.subscribe(event_type=KeyStroke, activity=self)
        self.application.subscribe(event_type=ScanComplete, activity=self)
        self.application.subscribe(event_type=ScanStarted, activity=self)

        self.display_state = {"top_bar": {"items": {"title": "Beagle's Folder Analyzer",
                                                    "help": "Press 'h' for help"},
                                          "fixed_size": 2,
                                          "print_fn": print_top_bar},
                              "folder_tree": {"to_depth": 4,
                                              "folder_data": [],
                                              "selected_folder": None,
                                              "print_fn": print_folder_tree},
                              "bottom_bar": {"fixed_size": 2,
                                             "items": {"status": "Folder scan in progress"},
                                             "print_fn": print_bottom_bar}}

        self._refresh_timer()


    def on_stop(self):
        self.application.unsubscribe(event_type=KeyStroke, activity=self)
        self.application.unsubscribe(event_type=ScanComplete, activity=self)
        self.application.unsubscribe(event_type=ScanStarted, activity=self)

    def on_event(self, event):
        if isinstance(event, KeyStroke):
            if event.key == curses.KEY_UP:
                self.move_selected_folder_up()
            elif event.key == curses.KEY_DOWN:
                self.move_selected_folder_down()
            elif event.key == Keys.LEFT_BRACKET:
                self.display_state["folder_tree"]["to_depth"] = max(1, self.display_state["folder_tree"]["to_depth"] - 1)
                self.refresh_tree_state()
            elif event.key == Keys.RIGHT_BRACKET:
                self.display_state["folder_tree"]["to_depth"] = min(10, self.display_state["folder_tree"]["to_depth"] + 1)
                self.refresh_tree_state()
            else:
                self.display_state["top_bar"]["items"]["last_key"] = f"Last key: {event.key}"

            self.refresh_screen()

        if isinstance(event, ScanComplete):
            self.update_bottom_bar("status", "Scan complete")

        if isinstance(event, ScanStarted):
            self.update_bottom_bar("status", "Folder scan in progress")

    def _refresh_timer(self):
        thread = threading.Timer(1.0, self._refresh_timer)
        thread.daemon = True
        thread.start()

        self.refresh_tree_state()

        self.application.main_thread.submit_async(self.refresh_screen)

    def refresh_tree_state(self):
        if self.application.folder_scan_tree is not None:
            context = self.display_state["folder_tree"]
            folder_data = breadth_first(self.application.folder_scan_tree, to_depth=context["to_depth"])

            context["folder_data"] = folder_data
            if context["selected_folder"] is None:
                context["selected_folder"] = folder_data[0][0]
            self.update_scroll_percent()

    def _index_of_selected_folder(self):
        context = self.display_state["folder_tree"]
        folders = [folder for folder, _ in context["folder_data"]]

        while context["selected_folder"] is not None and context["selected_folder"] not in folders:
            context["selected_folder"] = context["selected_folder"].parent

        index = folders.index(context["selected_folder"])
        return index, folders

    def move_selected_folder_up(self):
        index, folders = self._index_of_selected_folder()

        new_selected = folders[max(0, index-1)]

        self.display_state["folder_tree"]["selected_folder"] = new_selected
        self.update_scroll_percent()

    def move_selected_folder_down(self):
        index, folders = self._index_of_selected_folder()

        new_selected = folders[min(len(folders)-1, index+1)]

        self.display_state["folder_tree"]["selected_folder"] = new_selected
        self.update_scroll_percent()

    def update_scroll_percent(self):
        index, folders = self._index_of_selected_folder()

        percent = int(index/len(folders)*100)

        self.update_bottom_bar("scroll_percent", f"Scroll: {percent}%")
        self.refresh_screen()

    def update_bottom_bar(self, tag, value):
        self.display_state["bottom_bar"]["items"][tag] = value
        self.refresh_screen()
