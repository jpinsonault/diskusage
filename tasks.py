from asyncio import Future
from itertools import islice
from pathlib import Path
from queue import Queue, Empty
from time import sleep

from CentralDispatch import SerialDispatchQueue, ConcurrentDispatchQueue
from folder import Folder
from foldercore import folder_from_path
from funcutils import wrap_with_try


def print_task(stdscr, root_folder: Folder, done_signal: Future):
    while not done_signal.done():
        sleep(1)
        stdscr.clear()
        lines = []
        print_folder_tree(lines, root_folder, to_depth=2)
        for index, line in enumerate(lines):
            stdscr.addstr(index, 0, line)
        stdscr.refresh()


def print_folder_tree(lines: [str], folder: Folder, to_depth: int, current_depth: int=0):
    if current_depth <= to_depth:
        size_gb = folder.folder_stats.size/pow(1024, 3)
        lines.append("{tabs}{size:.2f}GB - {name}".format(tabs="  "*current_depth, size=size_gb, name=folder.path))

        sub_folders = sorted(folder.folders, key=lambda f: f.folder_stats.size, reverse=True)
        for sub_folder in islice(sub_folders, min(4, len(sub_folders))):
            print_folder_tree(lines, sub_folder, to_depth=to_depth, current_depth=current_depth+1)


def collect_results(new_folder):
    new_folder.parent.insert_folder(new_folder)


@wrap_with_try
def analyze_folder_task(folder_work_dispatch_queue: ConcurrentDispatchQueue, update_tree_dispatch_queue: SerialDispatchQueue, path: Path, parent: Folder):
    folder = folder_from_path(path, parent)

    for sub_folder_path in sub_paths(folder.path):
        print(f"Adding work for {sub_folder_path}")
        folder_work_dispatch_queue.submit_async(analyze_folder_task, folder_work_dispatch_queue, update_tree_dispatch_queue, sub_folder_path, folder)

    update_tree_dispatch_queue.submit_async(collect_results, folder)


def sub_paths(path):
    return [folder for folder in path.iterdir() if folder.is_dir()]


@wrap_with_try
def wait_on_futures(futures_queue: Queue):
    try:
        future = futures_queue.get_nowait()

        while True:
            _ = future.result()
            future = futures_queue.get_nowait()
    except Empty:
        return
