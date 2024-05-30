from typing import List
import os
import uuid

from PySide6.QtCore import Signal, QObject

image_extension = [".jpg", ".png", ".jpeg", ".bmp"]

final_image_extension = []

for ext in image_extension:
    ext = ext.strip().lower()
    if not ext.startswith("."):
        ext = f".{ext}"
    final_image_extension.append(ext)


class AnnotationFile(QObject):
    uuid: str = ""

    label: str = ""

    file_path: str = ""

    is_modified: bool = False

    pic_path: str
    __pic_path: str = ""

    slot_modified: Signal = Signal()

    ori_dict: dict

    other_shape_dict_list: List[dict]

    def __init__(self, label: str = ""):
        super().__init__()

        self.uuid = str(uuid.uuid4())

        self.label = label

        self.ori_dict = {}
        self.other_shape_dict_list = []

    def check_file_is_exist(self) -> bool:
        return os.path.exists(self.file_path)

    def __get_pic_path(self) -> str:
        filename = os.path.basename(self.file_path)
        filename_no_ext = os.path.splitext(filename)[0]
        directory = os.path.dirname(self.file_path)

        for ext_name in final_image_extension:
            image_path = os.path.join(
                directory,
                f"{filename_no_ext}{ext_name}"
            )
            if os.path.exists(image_path):
                return image_path

        return ""

    @property
    def pic_path(self) -> str:
        if not os.path.exists(self.__pic_path):
            self.__pic_path = self.__get_pic_path()

        if not os.path.exists(self.__pic_path):
            return ""

        return self.__pic_path

    def check_pic_is_exist(self) -> bool:
        return self.pic_path != ""

    def is_valid(self) -> bool:
        result = self.check_file_is_exist()
        result = result and self.check_pic_is_exist()

        return result

    def modifying(self):
        self.is_modified = True
        self.slot_modified.emit()

    def save(self) -> bool:
        if not self.is_modified:
            return False

        return True

    def __eq__(self, other):
        return self.uuid == other.uuid

    def __ne__(self, other):
        return self.uuid != other.uuid

    def __str__(self):
        return self.label
