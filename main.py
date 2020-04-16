# Usage: python3 main.py PATH_TO_ANALYZE -s MIN_SIZE_GB

import argparse
import traceback
from builtins import function
from concurrent.futures import ThreadPoolExecutor, Future
from curses import wrapper
from datetime import datetime
from functools import partial
from itertools import islice
from pathlib import Path
from queue import Queue, Empty
from time import sleep

from CentralDispatch import CentralDispatch
from folder import Folder
from foldercore import folder_from_path
from funcutils import wrap_with_try
from tasks import analyze_folder_task, sub_paths, print_task, collect_results, wait_task


def make_submit_task(task_pool: ThreadPoolExecutor, task_queue: Queue, future_queue: Queue):
    def on_complete():
        collect_results(task_queue, wrap_with_try(submit_task))

    def submit_task(current_path, parent_folder, ):
        future = task_pool.submit(wrap_with_try(analyze_folder_task),
                                  task_queue,
                                  wrap_with_try(on_complete),
                                  current_path,
                                  parent_folder)

        future_queue.put(future)

    return submit_task


def main(args, stdscr):
    task_pool = ThreadPoolExecutor(5)

    wait_pool = ThreadPoolExecutor(1)
    status_pool = ThreadPoolExecutor(1)
    task_queue = Queue()
    future_queue = Queue()

    root_path = Path(args.path)
    root_folder = folder_from_path(root_path, None)

    centralDispatch = CentralDispatch()
    
    submit_task = make_submit_task(task_pool, task_queue, future_queue)

    for sub_folder_path in sub_paths(root_path):
        submit_task(sub_folder_path, root_folder)

    done_signal = wait_pool.submit(wrap_with_try(wait_task), future_queue)
    status_pool.submit(wrap_with_try(print_task), stdscr, root_folder, done_signal)
    done_signal.result()

    print_final_output(root_folder, root_path)


def print_final_output(root_folder: Folder, root_path: Path):
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Disk Usage')
    parser.add_argument("path", help="The path to analyze")
    parser.add_argument("-s", "--min_size_gb", dest="min_size_gb", default=1, type=int, help="The smallest folder to report")

    args = parser.parse_args()

    wrapper(partial(main, args))


