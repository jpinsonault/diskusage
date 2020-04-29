import curses
from itertools import islice
from pathlib import Path

from folder import Folder, FolderStats
from printers import start_stop, is_hidden, make_context_menu
from ScreenLine import ScreenLine


def folder_from_path(path: Path, parent: Folder):
    size = 0
    last_modified = 0

    try:
        files = list(path.iterdir())
        size = sum(file.stat().st_size for file in files)
        last_modified = max(file.stat().st_mtime for file in files)
    except (ValueError, PermissionError):
        pass

    new_folder = Folder(path, parent, FolderStats(size, last_modified))

    return new_folder


def sub_paths(path):
    try:
        return [folder for folder in path.iterdir() if folder.is_dir()]
    except PermissionError:
        return []


def breadth_first(folder, to_depth) -> [Folder]:
    collector = []

    _breadth_first(folder, collector, to_depth=to_depth)

    return collector


def _breadth_first(folder: Folder, collector: [Folder], to_depth, current_depth: int = 0):
    if current_depth <= to_depth:
        collector.append((folder, current_depth))
        sub_folders = sorted(folder.folders, key=lambda f: f.folder_stats.size, reverse=True)
        for sub_folder in islice(sub_folders, min(4, len(sub_folders))):
            _breadth_first(sub_folder, collector, to_depth=to_depth, current_depth=current_depth + 1)


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

    selected_index = index_for_folder(context["selected_folder"], visible_folders)
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
                context_menu = make_context_menu(context["context_menu"])
                screen_lines += context_menu
        else:
            screen_lines.append(ScreenLine(context=context, x=depth * 2, text=text, mode=curses.A_NORMAL))
    return screen_lines

