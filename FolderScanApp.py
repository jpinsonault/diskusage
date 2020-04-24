from collections import namedtuple
from pathlib import Path
from queue import Queue

from Application import Application
from CentralDispatch import CentralDispatch
from folder import Folder
from foldercore import folder_from_path, sub_paths
from funcutils import wrap_with_try

ScanResult = namedtuple("ScanResult", ["folder"])
ScanError = namedtuple("ScanError", ["error"])


class FolderScanApp(Application):
    def __init__(self, args, curses_screen):
        super().__init__(curses_screen)
        self.args = args
        self.folder_scan_future = None
        self.collect_results_dispatch_queue = None
        self.folder_work_dispatch_queue = None
        self.folder_scan_tree = None

    def on_started(self):
        self.collect_results_dispatch_queue = CentralDispatch.create_serial_queue()
        self.folder_work_dispatch_queue = CentralDispatch.create_concurrent_queue(size=5)

        self.folder_scan_future = self.start_folder_scan(self.args.path)

    def start_folder_scan(self, path):
        self.folder_scan_future = CentralDispatch.future(self._scan_folder, Path(path))

    def _scan_folder(self, root_path: Path):
        self.folder_scan_tree = folder_from_path(root_path, None)

        for sub_folder_path in sub_paths(root_path):
            self.folder_work_dispatch_queue.submit_async(
                self.analyze_folder_task, sub_folder_path, self.folder_scan_tree
            )

        work_done = self.folder_work_dispatch_queue.finish_work()
        results_collected = self.collect_results_dispatch_queue.finish_work()

        return CentralDispatch.concat(work_done, results_collected)

    def collect_results(self, new_folder: Folder):
        new_folder.parent.insert_folder(new_folder)

    @wrap_with_try
    def analyze_folder_task(self, path: Path, parent: Folder):
        folder = folder_from_path(path, parent)

        if not self.shutdown_signal.done():
            for sub_folder_path in sub_paths(folder.path):
                print(f"Adding work for {sub_folder_path}")
                self.folder_work_dispatch_queue.submit_async(self.analyze_folder_task, sub_folder_path, folder)

        self.collect_results_dispatch_queue.submit_async(self.collect_results, folder)
