import os
from typing import List


class DirectoryAndFile:
    directory_path: str = ""
    directory_name: str = ""

    child_dir_object_list: List["DirectoryAndFile"]
    file_path_list: List[str]
    file_name_list: List[str]

    __walked: bool = False

    def __init__(self, directory_path: str):
        self.directory_path = directory_path

        self.child_dir_object_list = []
        self.file_path_list = []
        self.file_name_list = []

        self.update()

    def walk_dir(self, max_depth=0):
        self.__walked = True

        # Walk Current Dir
        for entry in os.listdir(self.directory_path):
            # Get the full path of the entry
            entry_path = os.path.join(self.directory_path, entry)

            if os.path.isdir(entry_path):
                # Create a new object for the subdirectory
                child_dir = self.__class__(entry_path)
                self.child_dir_object_list.append(child_dir)

                # Recursively walk the subdirectory if max_depth is not reached
                if max_depth > 0 and len(self.child_dir_object_list) > 0:
                    child_dir.walk_dir(max_depth=max_depth - 1)
            else:
                # Add file_path to the list
                self.file_path_list.append(entry_path)

    def is_walked(self) -> bool:
        return self.__walked

    def update(self):
        self.directory_path = os.path.abspath(self.directory_path)
        self.directory_name = os.path.basename(self.directory_path)

        self.file_name_list.clear()
        for file_path in self.file_path_list:
            self.file_name_list.append(os.path.basename(file_path))


if __name__ == "__main__":
    directory_path = "."
    directory_path = os.path.abspath(directory_path)
    print(directory_path)
    root_dir = DirectoryAndFile(directory_path)
    root_dir.walk_dir(5)
    print()
