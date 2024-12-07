import os
from enum import Enum
from typing import Optional

from mot_toolkit.config.program_path import get_current_cmd_dir


class SpiltType(Enum):
    TRAIN = "train"
    TEST = "test"
    VAL = "val"
    NONE = "none"

    def __str__(self):
        return self.value

    def to_title(self):
        if self == SpiltType.TRAIN:
            return "Train"
        elif self == SpiltType.TEST:
            return "Test"
        elif self == SpiltType.VAL:
            return "Validation"
        else:
            return "Other"


class DatasetSpilt:
    __abs_path: str = ""
    __rel_path: str = ""

    base_dir_path: str = ""

    current_run_dir: str = ""

    __spilt_type: SpiltType

    __depth: int = 2

    __file_name_depth: int = 2

    def __init__(
            self,
            path="",
            base_dir_path="",
            spilt_type: Optional[SpiltType] = None,
            depth: int = 2,
            file_name_depth: int = 2,
    ):
        self.current_run_dir = get_current_cmd_dir()

        self.base_dir_path = base_dir_path
        self.spilt_type = spilt_type
        self.depth = depth
        self.file_name_depth = file_name_depth

        self.path = path

    @property
    def path(self) -> str:
        return self.__abs_path if self.__abs_path else self.__rel_path

    @path.setter
    def path(self, path: str):
        if not os.path.exists(path):
            # Not Found Path
            if self.base_dir_path:
                path = os.path.join(self.base_dir_path, path)

        if os.path.exists(path):
            self.__abs_path = os.path.abspath(path)
        else:
            return

        base_dir = self.base_dir_path
        if len(base_dir) == 0:
            base_dir = self.current_run_dir

        self.__rel_path = os.path.relpath(self.__abs_path, base_dir)

    @property
    def abs_path(self) -> str:
        return self.__abs_path

    @property
    def rel_path(self) -> str:
        return self.__rel_path

    @property
    def unique_path(self):
        rel_path = self.rel_path

        while rel_path.find('\\') != -1:
            rel_path = rel_path.replace('\\', '/')

        return rel_path.strip()

    @property
    def spilt_type(self) -> SpiltType:
        return self.__spilt_type

    @spilt_type.setter
    def spilt_type(self, spilt_type: Optional[SpiltType]):
        if spilt_type is None:
            spilt_type = SpiltType.NONE

        self.__spilt_type = spilt_type

    @property
    def depth(self) -> int:
        return self.__depth

    @depth.setter
    def depth(self, depth: int):
        if depth < 1:
            return

        self.__depth = depth

    @property
    def file_name_depth(self) -> int:
        return self.__file_name_depth

    @file_name_depth.setter
    def file_name_depth(self, depth: int):
        if depth < 1:
            return

        self.__file_name_depth = depth

    def get_spilt_type_str(self) -> str:
        return self.spilt_type.value

    def is_exists(self) -> bool:
        return os.path.exists(self.abs_path)

    def is_valid(self) -> bool:
        return self.spilt_type != SpiltType.NONE

    def __str__(self):
        return f"[{self.spilt_type}]{self.rel_path}"

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "abs_path": self.abs_path,
            "rel_path": self.rel_path,
            "unique_path": self.unique_path,
            "base_dir_path": self.base_dir_path,
            "spilt_type": self.spilt_type.value,
            "depth": self.depth,
            "file_name_depth": self.file_name_depth,
        }

    @staticmethod
    def from_dict(
            data: dict,
            base_dir_path: str = ""
    ) -> 'DatasetSpilt':
        return DatasetSpilt(
            path=data.get("path", ""),
            base_dir_path=data.get("base_dir_path", ""),
            spilt_type=SpiltType(data.get("spilt_type", SpiltType.NONE.value)),
            depth=data.get("depth", 2),
            file_name_depth=data.get("file_name_depth", 2),
        )

    def generate_new_name(self, path: str = "") -> str:
        if len(path) == 0:
            path = self.abs_path

        current_depth = self.file_name_depth - 1

        current_dir = path
        last_1_level_dir_name = os.path.basename(current_dir)

        current_name = f"{last_1_level_dir_name}"
        while current_depth > 0:
            current_depth -= 1
            current_dir = os.path.dirname(current_dir)
            base_name = os.path.basename(current_dir)
            current_name = f"{base_name}-{current_name}"

        return current_name


if __name__ == "__main__":
    spilt_type = SpiltType.TRAIN
    print(spilt_type)
