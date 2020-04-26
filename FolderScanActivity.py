import curses
import os
import shutil
import subprocess
from itertools import islice

import Keys
from Activity import Activity
from CentralDispatch import CentralDispatch
from EventTypes import KeyStroke, ButtonEvent
from FolderScanApp import ScanComplete, ScanStarted
from HelpActivity import HelpActivity
from folder import Folder
from foldercore import breadth_first
from printers import print_bottom_bar, print_top_bar, start_stop, ScreenLine, is_hidden


def move_menu_left(context):
    selected_index = context.get("selected_index", 0)

    context["selected_index"] = (selected_index - 1) % len(context["items"])


def move_menu_right(context):
    selected_index = context.get("selected_index", 0)

    context["selected_index"] = (selected_index + 1) % len(context["items"])


def print_context_menu(screen, context, screen_line, y):
    selected_index = context.get("selected_index", 0)
    x = screen_line.x

    title = f"{context.get('title', '')}: "
    screen.addstr(y, x, title, curses.A_BOLD)
    x += len(title)

    for index in range(len(context["items"])):
        item = context["items"][index]
        text = f"[{item}]"
        if index == selected_index:
            screen.addstr(y, x, text, curses.A_REVERSE)
        else:
            screen.addstr(y, x, text, curses.A_NORMAL)

        x += len(text) + 1


def make_context_menu(screen, screen_lines, context) -> []:
    return [
            ScreenLine(context=context, x=context["x"], print_fn=print_context_menu),
            ScreenLine(context=context, x=context["x"], text="")]


def walk_selected_folder_up(folder, visible_folders) -> Folder:
    folder_iter = folder

    while folder_iter is not None and folder_iter not in visible_folders:
        folder_iter = folder_iter.parent

    return folder_iter


def index_for_folder(folder, folders) -> int:
    index = 0

    if folder is not None:
        index = folders.index(folder)

    return index


def print_folder_tree(screen, context, start_index, remaining_height):
    visible_folders = [folder for folder, _ in context["folder_data"]]

    walk_selected_folder_up(context["selected_folder"], visible_folders)

    selected_index = index_for_folder(context["selected_index"], visible_folders)
    start, stop = start_stop(selected_index, remaining_height, len(visible_folders))

    screen_lines = make_folder_tree(context, screen, start, stop)

    y_index = start_index
    for screen_line in islice(screen_lines, start, stop):
        screen_line.print_to(screen, y_index)
        y_index += 1

    return len(screen_lines)


def make_folder_tree(context, screen, start, stop):
    screen_lines = []
    for folder, depth in islice(context["folder_data"], start, stop):
        size_gb = folder.folder_stats.size / pow(1024, 3)

        text = "{size:.2f}GB - {name}".format(size=size_gb, name=folder.path)
        if folder == context["selected_folder"]:
            if is_hidden(context["context_menu"]):
                screen_lines.append(ScreenLine(context=context, x=depth * 2, text=text, mode=curses.A_REVERSE))
            else:
                screen_lines.append(ScreenLine(context=context, x=depth * 2, text=text, mode=curses.A_BOLD))

                context["context_menu"]["x"] = depth * 2
                context_menu = make_context_menu(screen, screen_lines, context["context_menu"])
                screen_lines += context_menu
        else:
            screen_lines.append(ScreenLine(context=context, x=depth * 2, text=text, mode=curses.A_NORMAL))
    return screen_lines


class FolderScanActivity(Activity):
    def __init__(self):
        super().__init__()

    def on_start(self):
        self.application.subscribe(event_type=KeyStroke, delegate=self)
        self.application.subscribe(event_type=ScanComplete, delegate=self)
        self.application.subscribe(event_type=ScanStarted, delegate=self)
        self.application.subscribe(event_type=ButtonEvent, delegate=self)

        self.display_state = {"top_bar": {"items": {"title": "Beagle's Folder Analyzer",
                                                    "help": "Press 'h' for help"},
                                          "fixed_size": 2,
                                          "print_fn": print_top_bar},
                              "folder_tree": {"to_depth": 4,
                                              "folder_data": [],
                                              "selected_folder": None,
                                              "context_menu": {"title": "Menu",
                                                               "items": ["open in explorer", "delete"],
                                                               "hidden": True},
                                              "print_fn": print_folder_tree,
                                              "input_handler": self._handle_folder_tree_input,
                                              "focus": True},
                              "bottom_bar": {"fixed_size": 2,
                                             "items": {"status": "Folder scan in progress"},
                                             "print_fn": print_bottom_bar}}

        self._refresh_timer(shutdown_signal=self.application.shutdown_signal)

    def on_event(self, event):
        if isinstance(event, ButtonEvent):
            if event.identifier == "open in explorer":
                folder = self.display_state["folder_tree"]["selected_folder"]

                # raise Exception(f"start '{folder.path}'")
                subprocess.Popen(r'explorer /select,"{}"'.format(folder.path))
        if isinstance(event, KeyStroke):
            self.handle_ui_input(event)
            if chr(event.key) == "h":
                self.application.segue_to(HelpActivity())
            elif chr(event.key) == "e":
                raise Exception("This is just a test")
            else:
                self.display_state["top_bar"]["items"]["last_key"] = f"Last key: {event.key}"

            self.refresh_screen()

        if isinstance(event, ScanComplete):
            self.update_bottom_bar("status", "Scan complete")

        if isinstance(event, ScanStarted):
            self.update_bottom_bar("status", "Folder scan in progress")

    def _handle_folder_tree_input(self, context, event):
        if chr(event.key) == " " or chr(event.key) == Keys.ENTER:
            self.toggle_context_menu()
        elif event.key == curses.KEY_UP:
                self.move_selected_folder_up()
        elif event.key == curses.KEY_DOWN:
            self.move_selected_folder_down()
        elif event.key == Keys.LEFT_BRACKET:
            self.move_display_depth_up(context)
        elif event.key == Keys.RIGHT_BRACKET:
            self.move_display_depth_down(context)

        context_menu = context["context_menu"]
        if not is_hidden(context_menu):
            if event.key == curses.KEY_LEFT:
                move_menu_left(context=context_menu)
            elif event.key == curses.KEY_RIGHT:
                move_menu_right(context=context_menu)
            elif event.key == Keys.ENTER:
                selected_item = context_menu["items"][context_menu["selected_index"]]
                button_event = ButtonEvent(identifier=selected_item)
                self.application.event_queue.put(button_event)
                self.toggle_context_menu()

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
            context["folder_data"] = breadth_first(self.application.folder_scan_tree, to_depth=context["to_depth"])

            if context["selected_folder"] is None:
                context["selected_folder"] = context["folder_data"][0][0]

            self.update_scroll_percent()

    def _index_of_selected_folder(self):
        context = self.display_state["folder_tree"]
        folders = [folder for folder, _ in context["folder_data"]]

        while context["selected_folder"] is not None and context["selected_folder"] not in folders:
            context["selected_folder"] = context["selected_folder"].parent

        index = folders.index(context["selected_folder"])
        return index, folders

    def move_display_depth_up(self,context):
        context["to_depth"] = max(1, context["to_depth"] - 1)
        self.refresh_tree_state()

    def move_display_depth_down(self, context):
        context["to_depth"] = min(10, context["to_depth"] + 1)
        self.refresh_tree_state()

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

    def toggle_context_menu(self):
        context = self.display_state["folder_tree"]["context_menu"]

        context["hidden"] = not is_hidden(context)
        context["selected_index"] = 0
        self.refresh_screen()
