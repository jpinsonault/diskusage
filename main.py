# Usage: python3 main.py PATH_TO_ANALYZE -s MIN_SIZE_GB

import argparse
import curses
from curses import wrapper
from functools import partial
from pathlib import Path

from CentralDispatch import CentralDispatch
from FolderScanActivity import FolderScanActivity
from FolderScanApp import FolderScanApp
from folder import Folder


def main(args, stdscr):
    try:
        app = FolderScanApp(args, stdscr)
        app.start(FolderScanActivity())
    except Exception as e:
        print("They got through!")


def print_final_output(root_folder: Folder, root_path: Path):
    all_folders = list(root_folder.iter_folders())

    threshold = args.min_size_gb * pow(1024, 3)  # 1GB
    over_threshold = [f for f in all_folders if f.folder_stats.size > threshold]

    over_threshold.sort(key=lambda f: f.folder_stats.size, reverse=True)
    over_threshold.sort(key=lambda f: depth(f.path, root_path), reverse=False)
    over_threshold.sort(key=lambda f: f.folder_stats.last_modified, reverse=False)

    for folder in over_threshold[:30]:
        print(folder)


def depth(path: Path, root: Path):
    return len(path.relative_to(root).parts)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Disk Usage')
    parser.add_argument("path", help="The path to analyze")
    parser.add_argument("-s", "--min_size_gb", dest="min_size_gb", default=1, type=int, help="The smallest folder to report")

    args = parser.parse_args()

    # main(args, None)
    wrapper(partial(main, args))


