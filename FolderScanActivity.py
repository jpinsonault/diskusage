import curses
from itertools import islice

import Keys
from Activity import Activity
from CentralDispatch import CentralDispatch
from EventTypes import KeyStroke
from FolderScanApp import ScanComplete, ScanStarted
from HelpActivity import HelpActivity
from foldercore import breadth_first
from printers import print_bottom_bar, print_top_bar, start_stop, ScreenLine


def print_context_menu(screen, context, start_index) -> []:
    pass


def print_folder_tree(screen, context, start_index, remaining_height):
    folders = [folder for folder, _ in context["folder_data"]]

    while context["selected_folder"] is not None and context["selected_folder"] not in folders:
        context["selected_folder"] = context["selected_folder"].parent

    selected_index = 0

    if context["selected_folder"] is not None:
        selected_index = folders.index(context["selected_folder"])

    start, stop = start_stop(selected_index, remaining_height, len(folders))
    y_index = start_index

    screen_lines = []

    for folder, depth in islice(context["folder_data"], start, stop):
        size_gb = folder.folder_stats.size / pow(1024, 3)

        if folder == context["selected_folder"]:
            mode = curses.A_REVERSE
        else:
            mode = curses.A_NORMAL

        # screen_lines += print_context_menu(screen, context, start_index)

        text = "{size:.2f}GB - {name}".format(size=size_gb, name=folder.path)
        screen_lines.append(ScreenLine(y_index, depth * 2, text, mode))
        y_index += 1

    for screen_line in islice(screen_lines, start, stop):
        screen_line.print_to(screen)

    return len(screen_lines)


class FolderScanActivity(Activity):
    def __init__(self):
        super().__init__()

    def on_start(self):
        self.application.subscribe(event_type=KeyStroke, delegate=self)
        self.application.subscribe(event_type=ScanComplete, delegate=self)
        self.application.subscribe(event_type=ScanStarted, delegate=self)

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

        self._refresh_timer(shutdown_signal=self.application.shutdown_signal)

    def on_event(self, event):
        if isinstance(event, KeyStroke):
            if chr(event.key) == "h":
                self.application.segue_to(HelpActivity())
            if chr(event.key) == "e":
                raise Exception("This is just a test")
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

    def _refresh_timer(self, shutdown_signal):
        timer = CentralDispatch.timer(1.0, self._refresh_timer, shutdown_signal)

        if not shutdown_signal.done() and self.application is not None:
            timer.start()

            self.refresh_tree_state()

            if not shutdown_signal.done():
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
