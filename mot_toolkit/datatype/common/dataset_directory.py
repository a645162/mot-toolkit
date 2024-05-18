from typing import List
import os


class AnnotationDirectory:
    dir_path: str = ""

    file_list: List[str] = []

    def __init__(self, dir_path: str = ""):
        self.dir_path = dir_path

    def walk_dir(
            self,
            file_extension: str = "json",
            scan_dir_path: str = "",
            recursive: bool = False,
            clear_old: bool = True
    ) -> None:
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
                if file.endswith(file_extension):
                    self.file_list.append(os.path.join(root, file))

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
