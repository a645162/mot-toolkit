from typing import List


class DirectoryAndFile:
    directory_path: str = ""

    child_dir_object_list: List
    file_path: List[str]

    def __init__(self):
        self.child_dir_object_list = []
        self.file_path = []

    def walk_dir(self, depth=0):
        pass
