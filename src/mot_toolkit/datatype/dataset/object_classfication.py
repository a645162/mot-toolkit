import os
import json

from typing import List, Optional


class ObjectClass:
    class_id: str
    class_name: str

    def __init__(self, class_id: str = "", class_name: str = ""):
        self.class_id = class_id
        self.class_name = class_name

    def __str__(self):
        return f"[{self.class_id}] {self.class_name}"

    def is_valid(self) -> bool:
        return (
                len(self.class_id) > 0 and
                len(self.class_name) > 0
        )

    def to_dict(self) -> dict:
        return {
            "class_id": self.class_id,
            "class_name": self.class_name
        }

    def from_dict(self, dict_obj: dict):
        self.class_id = dict_obj.get("class_id", "")
        self.class_name = dict_obj.get("class_name", "")


class ObjectClassConfigure:
    object_classes: List[ObjectClass]

    __file_path: str = ""

    def __init__(
            self,
            object_classes: Optional[List[ObjectClass]] = None
    ):
        if object_classes is None:
            object_classes = []

        self.object_classes = object_classes

    def to_dict(self) -> dict:
        object_classes = []
        for obj_class in self.object_classes:
            object_classes.append(obj_class.to_dict())

        return {
            "object_classes": object_classes
        }

    def from_dict(self, dict_obj: dict):
        object_classes_dict_list = dict_obj.get("object_classes", [])
        self.object_classes.clear()

        for obj_class_dict in object_classes_dict_list:
            new_obj_class = ObjectClass()

            new_obj_class.from_dict(obj_class_dict)

            self.object_classes.append(new_obj_class)

    @property
    def file_path(self) -> str:
        return self.__file_path

    @file_path.setter
    def file_path(self, file_path: str):
        if not os.path.exists(file_path):
            return

        self.__file_path = file_path

        self.parse_configure_file(file_path)

    def parse_configure_file(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            dict_obj = json.load(f)
            self.from_dict(dict_obj)

    def save_configure_file(self, file_path: str):
        with open(file_path, "w", encoding="utf-8") as f:
            dict_obj = self.to_dict()
            json.dump(dict_obj, f, indent=4)

    @staticmethod
    def create_by_configure_file(file_path: str) -> "Optional[ObjectClassConfigure]":
        if not os.path.exists(file_path):
            return None

        obj = ObjectClassConfigure()
        obj.file_path = file_path
        return obj


if __name__ == "__main__":
    class_configure = ObjectClassConfigure()
