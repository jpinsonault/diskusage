from itertools import islice
from pathlib import Path

from folder import Folder, FolderStats


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


def sub_paths(path):
    return [folder for folder in path.iterdir() if folder.is_dir()]


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
