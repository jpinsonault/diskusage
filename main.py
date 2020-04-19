# Usage: python3 main.py PATH_TO_ANALYZE -s MIN_SIZE_GB

import argparse
from pathlib import Path
from queue import Queue

from CentralDispatch import CentralDispatch, SerialDispatchQueue, ConcurrentDispatchQueue
from folder import Folder
from foldercore import folder_from_path
from funcutils import wrap_with_try
from tasks import analyze_folder_task, sub_paths


def submit_task(folder_work_dispatch_queue: ConcurrentDispatchQueue, task_queue: Queue,
                     update_tree_dispatch_queue: SerialDispatchQueue):

    @wrap_with_try
    def submit_task(current_path, parent_folder):
        future = folder_work_dispatch_queue.submit_async(analyze_folder_task,
                                                         folder_work_dispatch_queue,
                                                         update_tree_dispatch_queue,
                                                         current_path,
                                                         parent_folder)

        return future

    return submit_task


def main(args, stdscr):
    root_path = Path(args.path)
    root_folder = folder_from_path(root_path, None)

    collect_results_dispatch_queue = CentralDispatch.create_serial_queue()
    print_status_dispatch_queue = CentralDispatch.create_serial_queue()

    folder_work_dispatch_queue = CentralDispatch.create_concurrent_queue(size=5)

    for sub_folder_path in sub_paths(root_path):
        folder_work_dispatch_queue.submit_async(analyze_folder_task, folder_work_dispatch_queue, collect_results_dispatch_queue, sub_folder_path, root_folder)

    work_done = folder_work_dispatch_queue.finish_work()
    results_collected = collect_results_dispatch_queue.finish_work()

    work_done.result()
    results_collected.result()

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

    main(args, None)
    # wrapper(partial(main, args))


