from typing import List
import os

from PySide6.QtCore import QObject


class AnnotationDirectory(QObject):
    __dir_path: str = ""

    file_list: List[str]
    file_name_black_list: List[str]

    __walked: bool = False

    def __init__(self, dir_path: str = ""):
        super().__init__()

        self.file_list = []
        self.file_name_black_list = [
            "__MACOSX",
            "Thumbs.db",
            ".DS_Store"
        ]

        self.dir_path = dir_path

    @property
    def dir_path(self) -> str:
        return self.__dir_path

    @dir_path.setter
    def dir_path(self, dir_path: str):
        dir_path = os.path.abspath(dir_path)

        if dir_path != self.__dir_path:
            self.__dir_path = dir_path

    def sort_path(self, group_directory=False):
        if group_directory:
            self.__sort_path_group()
        else:
            self.__sort_path_simple()

    def __sort_path_simple(self):
        temp_list: List[tuple] = []

        for file_path in self.file_list:
            file_name = os.path.basename(file_path)
            file_name_no_ext = os.path.splitext(file_name)[0]

            temp_list.append(
                (file_name_no_ext, file_path)
            )

        temp_list.sort(
            key=lambda x: x[0]
        )

        self.file_list.clear()
        for _, file_path in temp_list:
            self.file_list.append(file_path)

    def __sort_path_group(self):
        temp_group_dict = {}

        # Group by directory
        for file_path in self.file_list:
            file_dir = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            file_name_no_ext = os.path.splitext(file_name)[0]

            if file_dir not in temp_group_dict.keys():
                temp_group_dict[file_dir] = []

            temp_group_dict[file_dir].append(
                (file_dir, file_name_no_ext, file_path)
            )

        # Sort by file name
        for file_dir in temp_group_dict.keys():
            temp_group_dict[file_dir].sort(
                key=lambda x: x[1]
            )

        # Sort by directory
        directory_list = list(temp_group_dict.keys())
        # Sort by length
        directory_list.sort(
            key=lambda x: len(x)
        )

        # Clear old list
        self.file_list.clear()

        # Append to list
        for file_dir in directory_list:
            for _, _, file_path in temp_group_dict[file_dir]:
                self.file_list.append(file_path)

    def walk_dir(
            self,
            file_extension: str = "json",
            scan_dir_path: str = "",
            recursive: bool = False,
            clear_old: bool = True
    ) -> None:
        __loaded = True

        scan_dir_path = scan_dir_path.strip()
        if len(scan_dir_path) == 0:
            scan_dir_path = self.dir_path.strip()
        if len(scan_dir_path) == 0:
            return

        file_extension = file_extension.strip()
        if len(file_extension) == 0:
            return
        if not file_extension.startswith("."):
            file_extension = f".{file_extension}"

        recursive = bool(recursive)
        clear_old = bool(clear_old)

        if clear_old:
            self.file_list.clear()

        for root, dirs, files in os.walk(scan_dir_path, topdown=True):
            if not recursive:
                dirs.clear()
            for file in files:
                if file in self.file_name_black_list:
                    continue

                if file.startswith("."):
                    # Ignore macOS Hidden Files
                    continue

                if file.endswith(file_extension):
                    self.file_list.append(os.path.join(root, file))

    @property
    def walked(self) -> bool:
        return self.__walked

    def is_empty(self) -> bool:
        return len(self.file_list) == 0

    def check_can_load(self) -> bool:
        return not self.is_empty()

    def print_file_list(self, include_directory_path: bool = False) -> None:
        for file in self.file_list:
            if include_directory_path:
                print(file)
            else:
                print(os.path.basename(file))


if __name__ == "__main__":
    annotation_directory = AnnotationDirectory()

    annotation_directory.dir_path = r"/Test"
    annotation_directory.walk_dir(
        recursive=False
    )

    annotation_directory.print_file_list()
