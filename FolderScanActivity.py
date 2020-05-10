import curses
import subprocess

import Keys
from Activity import Activity
from CentralDispatch import CentralDispatch
from EventTypes import KeyStroke, ButtonEvent
from FolderScanApp import ScanComplete, ScanStarted
from HelpActivity import HelpActivity
from TextInputTest import TextInputTest
from foldercore import breadth_first, make_folder_tree
from printers import make_top_bar, make_bottom_bar, make_spacer
from ContextUtils import move_menu_left, move_menu_right, is_hidden


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
                                          "line_generator": make_top_bar},
                              "folder_tree": {"to_depth": 4,
                                              "folder_data": [],
                                              "selected_folder": None,
                                              "context_menu": {"label": "Menu",
                                                               "items": ["open in explorer", "delete"],
                                                               "hidden": True},
                                              "text_input": {"label": "Send us your reckons",
                                                             "size": 30},
                                              "line_generator": make_folder_tree,
                                              "input_handler": self._handle_folder_tree_input,
                                              "focus": True},
                              "spacer": {"line_generator": make_spacer},
                              "bottom_bar": {"fixed_size": 2,
                                             "items": {"status": "Folder scan in progress"},
                                             "line_generator": make_bottom_bar}}

        self._refresh_timer(shutdown_signal=self.application.shutdown_signal)

    def on_event(self, event):
        if isinstance(event, ButtonEvent):
            if event.identifier == "open in explorer":
                folder = self.display_state["folder_tree"]["selected_folder"]

                subprocess.Popen(r'explorer /select,"{}"'.format(folder.path))

        if isinstance(event, KeyStroke):
            self.handle_ui_input(event)
            if chr(event.key) == "h":
                self.application.segue_to(HelpActivity())
            elif chr(event.key) == "e":
                raise Exception("This is just a test")
            elif chr(event.key) == "t":
                self.application.segue_to(TextInputTest())
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

    def toggle_text_input(self):
        context = self.display_state["folder_tree"]["text_input"]

        context["hidden"] = not is_hidden(context)
        context["selected_index"] = 0
