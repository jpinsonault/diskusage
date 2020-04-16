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
