from itertools import islice
from queue import Queue

from foldercore import folder_from_path


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


def collect_results(task_queue: Queue, submit_task):
    new_folder = task_queue.get(block=True)

    new_folder.parent.insert_folder(new_folder)

    for sub_folder_path in sub_paths(new_folder.path):
        submit_task(sub_folder_path, new_folder)


def analyze_folder_task(task_queue: Queue, on_complete, path: Path, parent: Folder):
    folder = folder_from_path(path, parent)

    task_queue.put(folder, block=True)
    on_complete()


def sub_paths(path):
    return [folder for folder in path.iterdir() if folder.is_dir()]


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
