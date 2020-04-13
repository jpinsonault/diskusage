# Usage: python3 main.py PATH_TO_ANALYZE -s MIN_SIZE_GB 

import argparse
import traceback
from concurrent.futures import ThreadPoolExecutor, Future
from curses import wrapper
from datetime import datetime
from functools import partial
from itertools import islice
from pathlib import Path
from queue import Queue, Empty
from time import sleep


class FolderStats:
    def __init__(self, size, last_modified):
        self.size = size
        self.last_modified = last_modified


class Folder:
    def __init__(self, path: Path, parent, folder_stats: FolderStats):
        self.path = path
        self.folders = []
        self.parent = parent
        self.folder_stats = folder_stats

    def insert_folder(self, folder):
        self.folders.append(folder)

        self.update_folder_stats(folder.folder_stats)

    def update_folder_stats(self, leaf_node_folder_stats):
        current_node = self

        while current_node is not None:
            current_node.folder_stats.size = current_node.folder_stats.size + leaf_node_folder_stats.size
            current_node.folder_stats.last_modified = max(current_node.folder_stats.last_modified, leaf_node_folder_stats.last_modified)

            current_node = current_node.parent

    def iter_folders(self):
        stack = [sub_folder for sub_folder in self.folders]

        while len(stack) > 0:
            current_folder = stack.pop()
            yield current_folder
            for sub_folder in current_folder.folders:
                stack.append(sub_folder)

    def __repr__(self):
        size_gb = self.folder_stats.size / pow(1024, 3)
        date_modified = datetime.utcfromtimestamp(self.folder_stats.last_modified).strftime('%Y-%m-%dTZ')
        return "{modified} - {size:.2f}GB - {name}".format(modified=date_modified, size=size_gb, name=self.path)


def main(args, stdscr):
    task_pool = ThreadPoolExecutor(5)

    wait_pool = ThreadPoolExecutor(1)
    status_pool = ThreadPoolExecutor(1)
    task_queue = Queue()
    future_queue = Queue()

    root_path = Path(args.path)
    root_folder = folder_from_path(root_path, None)

    def submit_task(current_path, parent_folder):
        future = task_pool.submit(wrap_with_try(folder_task),
                                  task_queue,
                                  wrap_with_try(on_complete),
                                  current_path,
                                  parent_folder)

        future_queue.put(future)

    def on_complete():
        collect_results(task_queue, wrap_with_try(submit_task))

    for sub_folder_path in sub_paths(root_path):
        submit_task(sub_folder_path, root_folder)

    done_signal = wait_pool.submit(wrap_with_try(wait_task), future_queue)
    status_pool.submit(wrap_with_try(print_task), stdscr, root_folder, done_signal)
    done_signal.result()
    # stdscr.getkey()

    all_folders = list(root_folder.iter_folders())

    threshold = args.min_size_gb * pow(1024, 3)  # 1GB
    over_threshold = [f for f in all_folders if f.folder_stats.size > threshold]

    over_threshold.sort(key=lambda f: f.folder_stats.size, reverse=True)
    over_threshold.sort(key=lambda f: depth(f.path, root_path), reverse=False)
    over_threshold.sort(key=lambda f: f.folder_stats.last_modified, reverse=False)

    print("min size", args.min_size_gb)
    for folder in over_threshold[:30]:
        print(folder)


def depth(path: Path, root: Path):
    return len(path.relative_to(root).parts)


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


def wrap_with_try(function):
    def inner_function(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as e:
            print(f"Error: {e}")
            print(traceback.format_exc())

    return inner_function


def collect_results(task_queue: Queue, submit_task):
    new_folder = task_queue.get(block=True)

    new_folder.parent.insert_folder(new_folder)

    for sub_folder_path in sub_paths(new_folder.path):
        submit_task(sub_folder_path, new_folder)


def folder_task(task_queue: Queue, on_complete, path: Path, parent: Folder):
    folder = folder_from_path(path, parent)

    task_queue.put(folder, block=True)
    on_complete()


def sub_paths(path):
    return [folder for folder in path.iterdir() if folder.is_dir()]


def folder_from_path(path: Path, parent: Folder):
    size = 0
    last_modified = 0

    try:
        files = list(path.iterdir())
        size = sum(file.stat().st_size for file in files)
        last_modified = max(file.stat().st_mtime for file in files)
    except ValueError:
        pass

    new_folder = Folder(path, parent, FolderStats(size, last_modified))

    return new_folder


def wait_task(futures_queue: Queue):
    def dequeue_or_none(queue: Queue):
        try:
            return queue.get(timeout=1)
        except Empty:
            return None

    future: Future = dequeue_or_none(futures_queue)

    while future is not None:
        _ = future.result()
        future = dequeue_or_none(futures_queue)


def curses(stdscr):
    # Clear screen
    stdscr.clear()

    # This raises ZeroDivisionError when i == 10.
    for i in range(1, 11):
        v = i
        print(v)
        stdscr.addstr(i, 0, '10 divided by {} is {}'.format(v, 10/v))

    stdscr.refresh()
    stdscr.getkey()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Disk Usage')
    parser.add_argument("path", help="The path to analyze")
    parser.add_argument("-s", "--min_size_gb", dest="min_size_gb", default=1, type=int, help="The smallest folder to report")

    args = parser.parse_args()

    wrapper(partial(main, args))


