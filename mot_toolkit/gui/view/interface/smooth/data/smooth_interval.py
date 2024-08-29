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
        if self.__is_checked:
            return

        self.__is_checked = True

        self.__is_valid = True

        if not self.first_file.check_annotation_list_is_same(self.last_file):
            self.__is_valid = False
            self.last_file.have_error = True

        self.first_file.check_error()
        self.last_file.check_error()

        for annotation_file_obj in self.other_files_list:
            if not annotation_file_obj.check_annotation_list_is_same(self.first_file):
                self.__is_valid = False
                annotation_file_obj.have_error = True

                continue

            # Basic check
            annotation_file_obj.check_error()

    @property
    def is_valid(self) -> bool:
        if not self.__is_checked:
            self.check()

        return self.__is_valid
