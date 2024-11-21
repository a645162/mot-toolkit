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


class DatasetSpilt:
    __abs_path: str = ""
    __rel_path: str = ""

    base_dir_path: str = ""

    current_run_dir: str = ""

    __spilt_type: SpiltType

    def __init__(
            self,
            path="",
            base_dir_path="",
            spilt_type: Optional[SpiltType] = None
    ):
        self.current_run_dir = get_current_cmd_dir()

        self.base_dir_path = base_dir_path
        self.spilt_type = spilt_type

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
    def spilt_type(self) -> SpiltType:
        return self.__spilt_type

    @spilt_type.setter
    def spilt_type(self, spilt_type: Optional[SpiltType]):
        if spilt_type is None:
            spilt_type = SpiltType.NONE

        self.__spilt_type = spilt_type

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
            "base_dir_path": self.base_dir_path,
            "spilt_type": self.spilt_type.value
        }

    @staticmethod
    def from_dict(
            data: dict,
            base_dir_path: str = ""
    ) -> 'DatasetSpilt':
        return DatasetSpilt(
            path=data.get("path", ""),
            base_dir_path=data.get("base_dir_path", ""),
            spilt_type=SpiltType(data.get("spilt_type", SpiltType.NONE.value))
        )


if __name__ == "__main__":
    spilt_type = SpiltType.TRAIN
    print(spilt_type)
