from typing import List
import json
import os.path

from PySide6.QtCore import Signal

from mot_toolkit.datatype.common.object_annotation import ObjectAnnotation
from mot_toolkit.datatype.common.annotation_file import AnnotationFile
from mot_toolkit.datatype.common.dataset_directory import AnnotationDirectory
from mot_toolkit.datatype.common.rect_data_annotation import (
    RectDataAnnotation
)
from mot_toolkit.parser.json_parser import parse_json_to_dict


class XAnyLabelingRect(RectDataAnnotation):
    group_id: str = ""
    shape_type: str = ""
    flags: dict = {}

    def __init__(self, label: str = ""):
        super().__init__(label)


class XAnyLabelingAnnotation(AnnotationFile):
    version: str
    flags: dict

    rect_annotation_list: List[XAnyLabelingRect]

    image_path = ""
    image_data = None
    image_height = 0
    image_width = 0

    def __init__(self, label: str = ""):
        super().__init__(label)

        self.version = ""
        self.flags = {}

        self.rect_annotation_list = []

    def to_dict(self) -> dict:
        result_dict = {}

        result_dict.update(self.ori_dict)

        result_dict["version"] = self.version
        result_dict["flags"] = self.flags

        result_dict["shapes"] = []
        for rect_item in self.rect_annotation_list:
            final_shape_dict = {}

            final_shape_dict.update(rect_item.ori_dict)

            current_shape_dict = {
                "label": rect_item.label,
                "text": rect_item.text,
                "points": rect_item.get_rect_two_point_2dim_array(),
                "group_id": rect_item.group_id,
                "shape_type": rect_item.shape_type,
                "flags": rect_item.flags
            }
            final_shape_dict.update(current_shape_dict)

            result_dict["shapes"].append(final_shape_dict)

        for other_shape_dict in self.other_shape_dict_list:
            result_dict["shapes"].append(other_shape_dict)

        result_dict["imagePath"] = self.image_path
        result_dict["imageData"] = self.image_data
        result_dict["imageHeight"] = self.image_height
        result_dict["imageWidth"] = self.image_width

        return result_dict

    def __dict__(self) -> dict:
        return self.to_dict()

    def __str__(self) -> str:
        return self.to_json_string()

    def to_json_string(self) -> str:
        result_dict = self.to_dict()

        # Convert Dict to Json String
        json_string = \
            json.dumps(
                result_dict,
                sort_keys=False,
                indent=2,
                separators=(',', ': ')
            )

        return json_string.strip() + "\n"

    def save_json(self, save_path: str = ""):
        save_path = save_path.strip()
        if len(save_path) == 0:
            save_path = self.file_path

        save_path = save_path.strip()
        if len(save_path) == 0:
            return

        # Save to json file
        with open(save_path, "w") as f:
            f.write(self.to_json_string())

        print("Save Json File Successfully: " + save_path)

    def save(self) -> bool:
        if not super().save():
            return False

        self.save_json(self.file_path)

        return True

    def reload(self, check=True) -> bool:
        if check and not super().reload():
            return False

        data = self.ori_dict

        self.version = data.get("version", "")
        self.flags = data.get("flags", {})

        shapes_list: List[dict] = data.get("shapes", [])
        self.rect_annotation_list.clear()
        for shape_item in shapes_list:
            item_label = shape_item.get("label", "")
            item_text = shape_item.get("text", "")
            item_points = shape_item.get("points", [])
            item_group_id = shape_item.get("group_id", "")
            item_shape_type = shape_item.get("shape_type", "")
            item_flags = shape_item.get("flags", {})

            if item_shape_type == "rectangle":
                current_rect_annotation = XAnyLabelingRect(item_label)

                self.ori_dict.update(shape_item)

                current_rect_annotation.text = item_text

                current_rect_annotation.set_by_rect_two_point(
                    item_points[0][0], item_points[0][1],
                    item_points[1][0], item_points[1][1]
                )

                current_rect_annotation.group_id = item_group_id
                current_rect_annotation.shape_type = item_shape_type
                current_rect_annotation.flags = item_flags

                self.rect_annotation_list.append(
                    current_rect_annotation
                )
            else:
                self.other_shape_dict_list.append(shape_item)
                print(f"Unknown shape type: {item_shape_type} in {self.file_path}")

        self.image_path = data.get("imagePath", "")
        self.image_data = data.get("imageData", None)
        self.image_height = data.get("imageHeight", 0)
        self.image_width = data.get("imageWidth", 0)

        self.slot_modified.emit(self.index)

        return True

    def fix_bugs(self) -> bool:
        modified = False

        for rect_item in self.rect_annotation_list:
            if (
                    rect_item.fix_bugs(
                        image_width=self.image_width,
                        image_height=self.image_height
                    )
            ):
                modified = True

        return modified

    def del_by_label(self, label: str) -> bool:
        for rect_item in self.rect_annotation_list:
            if rect_item.label == label:
                self.rect_annotation_list.remove(rect_item)
                self.modifying()
                return True

        return False

    def del_by_group_id(self, group_id: str):
        operate_result = False

        for rect_item in self.rect_annotation_list:
            if rect_item.group_id == group_id:
                self.rect_annotation_list.remove(rect_item)
                self.modifying()
                operate_result = True

        return operate_result

    def get_label_list(self) -> List[str]:
        label_list = []

        for rect_item in self.rect_annotation_list:
            text = rect_item.label
            if text not in label_list:
                label_list.append(text)

        return label_list

    @property
    def annotation_count(self) -> int:
        return len(self.rect_annotation_list)

    def check_annotation_list_is_valid_tracking(self) -> bool:
        def get_keywords(obj: XAnyLabelingRect):
            return obj.label

        annotation_keywords = []

        # Ensure all labels are unique
        for rect_item in self.rect_annotation_list:
            text = get_keywords(rect_item)
            if text not in annotation_keywords:
                annotation_keywords.append(text)
            else:
                return False

        return True

    def check_annotation_list_is_same(self, other: "XAnyLabelingAnnotation"):
        if self.annotation_count != other.annotation_count:
            return False

        def get_keywords(obj: XAnyLabelingRect):
            return obj.label

        for self_rect_item in self.rect_annotation_list:
            found = False

            for other_rect_item in other.rect_annotation_list:
                if get_keywords(self_rect_item) == get_keywords(other_rect_item):
                    found = True
                    break

            if not found:
                return False

        return True

    def check_error(self):
        if not self.check_annotation_list_is_valid_tracking():
            self.have_error = True

    def get_tag_list(self) -> List[str]:
        tag_list = []

        for rect_item in self.rect_annotation_list:
            if rect_item.label not in tag_list:
                tag_list.append(rect_item.label)

        return tag_list

    def get_target_name_rect_annotation_list(self, target_name: str) -> List[RectDataAnnotation]:
        target_name_annotation_list = []

        for rect_item in self.rect_annotation_list:
            if rect_item.label == target_name:
                target_name_annotation_list.append(rect_item)

        return target_name_annotation_list

    def get_target_name_annotation_list(self, target_name: str) -> List[ObjectAnnotation]:
        target_name_annotation_list: List[ObjectAnnotation] = []

        target_name_annotation_list.extend(self.get_target_name_rect_annotation_list(target_name))

        return target_name_annotation_list

    def add_or_update_rect(self, rect_item: XAnyLabelingRect):
        self.modifying()

        for i, current_rect_item in enumerate(self.rect_annotation_list):
            if current_rect_item.label == rect_item.label:
                self.rect_annotation_list[i].update_by(rect_item)
                return

        self.rect_annotation_list.append(rect_item)

    def add_rect(
            self,
            label_name: str,
            x: int = 0, y: int = 0,
            width: int = 50, height: int = 50,
    ) -> bool:
        label_name = label_name.strip()

        new_rect_item = XAnyLabelingRect()

        new_rect_item.label = label_name
        new_rect_item.group_id = label_name
        new_rect_item.shape_type = "rectangle"

        if x < 0 or y < 0 or width <= 0 or height <= 0:
            return False

        new_rect_item.x = x
        new_rect_item.y = y
        new_rect_item.width = width
        new_rect_item.height = height

        self.rect_annotation_list.append(new_rect_item)

        self.modifying()

        return True


def parse_xanylabeling_json(
        json_path: str,
        index: int = -1
) -> XAnyLabelingAnnotation:
    data: dict = parse_json_to_dict(json_path)

    current_annotation_obj: XAnyLabelingAnnotation = \
        XAnyLabelingAnnotation()
    current_annotation_obj.index = index

    # Save Original Dict
    current_annotation_obj.ori_dict.update(data)

    # Set Json Path
    current_annotation_obj.file_path = json_path

    # Load Data from Dict
    current_annotation_obj.reload(check=False)

    return current_annotation_obj


class AnnotationFileInterval:
    name: str = ""

    first_file: XAnyLabelingAnnotation = None
    last_file: XAnyLabelingAnnotation = None

    other_files_list: List[XAnyLabelingAnnotation]

    def __init__(self):
        self.other_files_list = []


modify_store_file_name = "modified_files.json"


class XAnyLabelingAnnotationDirectory(AnnotationDirectory):
    slot_modified: Signal = Signal(int)

    annotation_file: List[XAnyLabelingAnnotation]

    label_list: List[str]

    # {"1": ["000001.json"]}
    label_obj_list_dict: dict = {}

    file_name_list: List[str]
    __can_only_file_name: bool = False

    __loaded: bool = False

    def __init__(self):
        super().__init__()

        self.annotation_file = []
        self.label_list = []
        self.file_name_list = []

        self.file_name_black_list.append(modify_store_file_name)

    @property
    def loaded(self) -> bool:
        return self.__loaded

    def load_json_files(self):
        # Check File Path List
        if self.is_empty():
            return

        __loaded = True

        # Clear
        self.annotation_file.clear()
        self.file_name_list.clear()

        for i, json_file in enumerate(self.file_list):
            annotation = \
                parse_xanylabeling_json(
                    json_path=json_file,
                    index=i
                )

            annotation.slot_modified.connect(self.slot_modified)

            self.annotation_file.append(annotation)

        self.__check_can_only_file_name()

        for annotation in self.annotation_file:
            self.file_name_list.append(annotation.file_name_no_extension)

    def save_json_files(self):
        for annotation_obj in self.annotation_file:
            if annotation_obj.is_modified:
                annotation_obj.save()

    def update_label_list(self) -> List[str]:
        # Clear
        label_list = self.label_list
        label_list.clear()
        self.label_obj_list_dict = {}

        for annotation_obj in self.annotation_file:

            current_label_list = annotation_obj.get_label_list()
            for label in current_label_list:
                # Update Label List
                if label not in label_list:
                    label_list.append(label)

                # Update Label-List[Obj] Dict
                if label not in self.label_obj_list_dict.keys():
                    self.label_obj_list_dict[label] = []
                self.label_obj_list_dict[label].append(annotation_obj)

        return label_list

    def __check_can_only_file_name(self) -> bool:
        directory_list = []
        ext_list = []
        for annotation in self.annotation_file:
            file_path = annotation.file_path
            directory_path = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[1]
            if (
                    directory_path not in directory_list and
                    os.path.isdir(directory_path)
            ):
                directory_list.append(directory_path)
            if file_ext not in ext_list:
                ext_list.append(file_ext)

        only_file_name = (
                len(directory_list) == 1 and
                len(ext_list) == 1
        )

        self.__can_only_file_name = only_file_name

        return only_file_name

    @property
    def can_only_file_name(self) -> bool:
        return self.__can_only_file_name

    @property
    def save_record_path(self) -> str:
        path = os.path.join(self.dir_path, modify_store_file_name)

        if not os.path.exists(path):
            open(path, "w").close()

        return path

    @property
    def first_file(self) -> XAnyLabelingAnnotation:
        return self.annotation_file[0] if len(self.annotation_file) > 0 else None

    @property
    def last_file(self) -> XAnyLabelingAnnotation:
        return self.annotation_file[-1] if len(self.annotation_file) > 0 else None

    def get_file_object_by_file_name(self, file_name: str) -> XAnyLabelingAnnotation | None:
        for annotation_obj in self.annotation_file:
            if annotation_obj.file_name == file_name:
                return annotation_obj

        return None

    def get_file_object_index(self, file_obj: XAnyLabelingAnnotation) -> int:
        for i, annotation_obj in enumerate(self.annotation_file):
            if annotation_obj.is_same_path(file_obj):
                return i

        return -1

    def get_file_object_index_by_name(self, file_name: str) -> int:
        for i, annotation_obj in enumerate(self.annotation_file):
            if annotation_obj.file_name == file_name:
                return i

        return -1

    def check_is_last_file(self, file_obj: XAnyLabelingAnnotation) -> bool:
        index = self.get_file_object_index(file_obj)

        if index == -1:
            return False

        return index == len(self.annotation_file) - 1

    def get_annotation_file_interval_list(self) -> List[AnnotationFileInterval]:
        interval_list: List[AnnotationFileInterval] = []

        if len(self.annotation_file) == 0:
            return interval_list

        with open(self.save_record_path, "r", encoding="utf-8") as f:
            json_str = f.read().strip()
            if len(json_str) == 0:
                return interval_list
            json_data: dict = json.loads(json_str)

        file_name_list = json_data.keys()

        # Remove Empty Line
        file_name_list = [
            file_name.strip()
            for file_name in file_name_list
            if len(file_name.strip())
        ]

        # Remove File Not Exist
        file_name_list = [
            file_name
            for file_name in file_name_list
            if os.path.exists(os.path.join(self.dir_path, file_name))
        ]

        all_file_name_list = [
            file_obj.file_name
            for file_obj in self.annotation_file
        ]

        # Remove File Name Not Exist
        file_name_list = [
            file_name
            for file_name in all_file_name_list
            if file_name in file_name_list
        ]

        first_file_name = all_file_name_list[0]
        last_file_name = all_file_name_list[-1]

        if first_file_name not in file_name_list:
            file_name_list.append(first_file_name)

        if last_file_name not in file_name_list:
            file_name_list.append(last_file_name)

        file_name_list.sort()

        # Create AnnotationFileInterval objects
        for i in range(len(file_name_list) - 1):
            first_file_index = self.get_file_object_index_by_name(file_name_list[i])
            last_file_index = self.get_file_object_index_by_name(file_name_list[i + 1])

            interval = AnnotationFileInterval()
            interval.name = str(i + 1)
            interval.first_file = self.annotation_file[first_file_index]
            interval.last_file = self.annotation_file[last_file_index]

            for j in range(first_file_index + 1, last_file_index):
                interval.other_files_list.append(self.annotation_file[j])

            interval_list.append(interval)

        return interval_list

    def fix_bugs(self) -> bool:
        modified = False
        for annotation_obj in self.annotation_file:
            if annotation_obj.fix_bugs():
                modified = True

        return modified


if __name__ == '__main__':
    # Single File Test
    result = parse_xanylabeling_json(
        r"../../../Test/00000000.json"
    )
    print(result.version)
    print()
    for rect_item in result.rect_annotation_list:
        print(str(rect_item))

    # Directory Test
    annotation_directory = XAnyLabelingAnnotationDirectory()
    annotation_directory.dir_path = r"../../../Test"
    annotation_directory.walk_dir(recursive=False)
    annotation_directory.sort_path(group_directory=True)
    annotation_directory.load_json_files()

    print(annotation_directory.update_label_list())

    print()

    smooth_list = annotation_directory.get_annotation_file_interval_list()

    print()
