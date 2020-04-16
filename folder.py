from datetime import datetime
from pathlib import Path


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
