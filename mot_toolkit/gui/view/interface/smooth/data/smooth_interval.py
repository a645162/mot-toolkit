from typing import List

from datatype.xanylabeling import AnnotationFileInterval, XAnyLabelingAnnotation


class SmoothInterval(AnnotationFileInterval):
    group_name: str = ""

    __is_checked: bool = False
    __is_valid: bool = False

    error_file_name_list: List[str]
    error_obj_list: List[XAnyLabelingAnnotation]

    def __init__(self):
        super().__init__()

        self.error_file_name_list = []
        self.error_obj_list = []

    @staticmethod
    def from_parent(parent_obj: AnnotationFileInterval) -> "SmoothInterval":
        new_obj = SmoothInterval()
        new_obj.__dict__.update(parent_obj.__dict__)

        return new_obj

    def check(self):
        self.__is_checked = True

    @property
    def is_valid(self) -> bool:
        return True
