from typing import List
import json
import os.path

from PySide6.QtCore import Signal

import cv2
import numpy as np
from PySide6.QtGui import QColor

from mot_toolkit.datatype.common.object_annotation import ObjectAnnotation
from mot_toolkit.datatype.common.annotation_file import AnnotationFile
from mot_toolkit.datatype.common.dataset_directory import AnnotationDirectory
from mot_toolkit.datatype.common.rect_data_annotation import (
    RectDataAnnotation
)
from mot_toolkit.parser.json_parser import parse_json_to_dict

from mot_toolkit.utils.logs import get_logger

logger = get_logger()


class XAnyLabelingRect(RectDataAnnotation):
    group_id: str = ""
    shape_type: str = ""
    flags: dict = {}

    description: str = ""

    def __init__(self, label: str = ""):
        super().__init__(label)

    def __copy__(self):
        new_object = XAnyLabelingRect(self.label)

        new_object.text = self.text

        new_object.x1 = self.x1
        new_object.y1 = self.y1

        new_object.x2 = self.x2
        new_object.y2 = self.y2

        new_object.ori_dict = {}
        new_object.ori_dict.update(self.ori_dict)

        new_object.picture_width = self.picture_width
        new_object.picture_height = self.picture_height

        new_object.group_id = self.group_id
        new_object.shape_type = self.shape_type
        new_object.flags = {}
        new_object.flags.update(self.flags)

        return new_object


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
                "flags": rect_item.flags,
                "description": rect_item.description,
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

    def to_yolo_format(self, replace_label_dict: dict = None) -> str:
        yolo_text_item: List[str] = []

        for rect_item in self.rect_annotation_list:
            x, y, w, h = (
                rect_item.center_x_ratio,
                rect_item.center_y_ratio,
                rect_item.width_ratio,
                rect_item.height_ratio
            )

            end_count = 6
            x, y, w, h = (
                round(x, end_count),
                round(y, end_count),
                round(w, end_count),
                round(h, end_count)
            )

            label = rect_item.label

            if replace_label_dict is not None:
                if label in replace_label_dict.keys():
                    label = replace_label_dict[label]
                else:
                    for key in replace_label_dict.keys():
                        if "*" in key:
                            keyword = key.replace("*", "")
                            if len(keyword) == 0 or keyword in label:
                                label = replace_label_dict[key]
                                break

            yolo_text_item.append(f"{label} {x} {y} {w} {h}")

        yolo_text = "\n".join(yolo_text_item).strip() + "\n"

        return yolo_text

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

        data = {}
        data.update(self.ori_dict)

        self.version = data.get("version", "")
        self.flags = data.get("flags", {})

        self.image_path = data.get("imagePath", "")
        self.image_data = data.get("imageData", None)
        self.image_height = data.get("imageHeight", 0)
        self.image_width = data.get("imageWidth", 0)

        shapes_list: List[dict] = data.get("shapes", [])

        # Clear Old Data
        self.rect_annotation_list.clear()

        for shape_item in shapes_list:
            item_label = shape_item.get("label", "")
            item_text = shape_item.get("text", "")
            item_points = shape_item.get("points", [])
            item_group_id = shape_item.get("group_id", "")
            item_shape_type = shape_item.get("shape_type", "")
            item_flags = shape_item.get("flags", {})
            item_description = shape_item.get("description", "")

            if item_shape_type == "rectangle":
                current_rect_annotation = XAnyLabelingRect(item_label)

                data.update(shape_item)

                current_rect_annotation.text = item_text

                current_rect_annotation.set_by_rect_two_point(
                    item_points[0][0], item_points[0][1],
                    item_points[1][0], item_points[1][1]
                )

                current_rect_annotation.group_id = item_group_id
                current_rect_annotation.shape_type = item_shape_type
                current_rect_annotation.flags = item_flags
                current_rect_annotation.description = item_description

                current_rect_annotation.picture_width = self.image_width
                current_rect_annotation.picture_height = self.image_height

                self.rect_annotation_list.append(
                    current_rect_annotation
                )
            else:
                self.other_shape_dict_list.append(shape_item)
                logger.info(f"Unknown shape type: {item_label}({item_shape_type}) in {self.file_path}")

        self.is_modified = False
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

        self.rect_annotation_list.append(rect_item.copy())

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

    def get_cv_mat(self) -> np.ndarray | None:
        if len(self.pic_path) == 0:
            return None

        if not os.path.exists(self.pic_path):
            return None

        img_np = cv2.imread(self.pic_path, cv2.IMREAD_COLOR)

        return img_np

    def get_cv_mat_with_box(
            self,
            with_text=True,
            color: tuple | QColor = (0, 255, 0),
            text_color: tuple | QColor = (0, 0, 255),
            thickness: int = 2,
            center_point_trajectory: dict = None,
            draw_trajectory: bool = False,
            trajectory_line_mode: bool = True,
            selection_label: str = "",
            selection_color: tuple | QColor = (0, 255, 255),
            not_found_return_none: bool = False,
            only_selection_box: bool = False,
            crop_selection: bool = False,
            crop_x1: int = 0, crop_y1: int = 0,
            crop_x2: int = 0, crop_y2: int = 0,
            crop_padding: int = 50,
            crop_min_size: int = 1000,
            color_dict: dict = None
    ) -> np.ndarray | None:
        if center_point_trajectory is None:
            center_point_trajectory = {}
        if color_dict is None:
            color_dict = {}
        img_np = self.get_cv_mat()
        if img_np is None:
            return None

        new_image = img_np.copy()

        def rgb2bgr(rgb: object) -> tuple:
            return rgb[2], rgb[1], rgb[0]

        if isinstance(color, QColor):
            color = rgb2bgr(color.getRgb())
        if isinstance(text_color, QColor):
            text_color = rgb2bgr(text_color.getRgb())
        if isinstance(selection_color, QColor):
            selection_color = rgb2bgr(selection_color.getRgb())

        selection_x1, selection_y1, selection_x2, selection_y2 = 0, 0, 0, 0
        found_selection = False

        for rect_item in self.rect_annotation_list:
            x1, y1, x2, y2 = rect_item.get_rect_two_point_tuple_int()
            center_x, center_y = rect_item.center_x, rect_item.center_y
            label = rect_item.label.strip()

            if label != "":
                if label not in center_point_trajectory.keys():
                    center_point_trajectory[label] = []

                center_point_trajectory[label].append((center_x, center_y))

            current_color = color

            found_color = False
            if label in color_dict.keys():
                found_color_obj: QColor = color_dict[label]
                current_color = rgb2bgr(found_color_obj.getRgb())
                found_color = True

            if len(selection_label) > 0:
                # Find Selection
                if rect_item.label == selection_label:
                    if not found_color:
                        current_color = selection_color

                    (
                        selection_x1,
                        selection_y1,
                        selection_x2,
                        selection_y2
                    ) = x1, y1, x2, y2
                    found_selection = True
                else:
                    if only_selection_box:
                        continue

            new_image = \
                cv2.rectangle(
                    new_image,
                    (x1, y1),
                    (x2, y2),
                    current_color,
                    thickness
                )

            # Draw Trajectory
            if (
                    draw_trajectory and
                    len(center_point_trajectory.keys()) > 0 and
                    label and
                    label in center_point_trajectory.keys()
            ):
                if trajectory_line_mode:
                    # Draw line between points
                    last_point = None
                    for point in center_point_trajectory[label]:
                        center_x, center_y = point
                        if last_point is not None:
                            new_image = cv2.line(
                                new_image,
                                last_point,
                                (int(center_x), int(center_y)),
                                current_color,
                                thickness
                            )
                        last_point = (int(center_x), int(center_y))
                else:
                    for point in center_point_trajectory[label]:
                        center_x, center_y = point
                        new_image = cv2.circle(
                            new_image,
                            (int(center_x), int(center_y)),
                            3,
                            current_color,
                            -1
                        )

            if with_text:
                text = f"{label}"

                cv2.putText(
                    new_image,
                    text,
                    (x1, y1 + 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    text_color,
                    2
                )

        if (
                not_found_return_none and
                len(selection_label) > 0 and
                not found_selection
        ):
            return None

        crop_selection = crop_selection and found_selection

        if (
                (not crop_selection) and
                (
                        crop_x1 == 0 and
                        crop_y1 == 0 and
                        crop_x2 == 0 and
                        crop_y2 == 0
                )
        ):
            return new_image

        image_width, image_height = new_image.shape[1], new_image.shape[0]

        crop_x1 = crop_x1
        crop_y1 = crop_y1
        crop_x2 = crop_x2
        crop_y2 = crop_y2

        if crop_selection:
            crop_x1 = selection_x1
            crop_y1 = selection_y1
            crop_x2 = selection_x2
            crop_y2 = selection_y2

        # Add Padding
        crop_x1 -= crop_padding
        crop_y1 -= crop_padding
        crop_x2 += crop_padding
        crop_y2 += crop_padding

        # Fix Crop Size
        crop_x1 = max(0, crop_x1)
        crop_y1 = max(0, crop_y1)
        crop_x2 = min(image_width, crop_x2)
        crop_y2 = min(image_height, crop_y2)

        crop_image = new_image[crop_y1:crop_y2, crop_x1:crop_x2]

        crop_image_width, crop_image_height = crop_image.shape[1], crop_image.shape[0]

        if crop_min_size > 0:
            if crop_image_width < crop_min_size or crop_image_height < crop_min_size:
                scale_factor = crop_min_size / max(crop_image_width, crop_image_height)
                crop_image = cv2.resize(crop_image, (0, 0), fx=scale_factor, fy=scale_factor)

        return crop_image


def parse_xanylabeling_json(
        json_path: str,
        index: int = -1
) -> XAnyLabelingAnnotation:
    data: dict = parse_json_to_dict(json_path)

    current_annotation_obj: XAnyLabelingAnnotation = \
        XAnyLabelingAnnotation()
    current_annotation_obj.index = index

    file_name = os.path.basename(json_path)
    file_name_no_ext = os.path.splitext(file_name)[0]
    try:
        current_annotation_obj.mot_index = int(file_name_no_ext)
    except ValueError:
        current_annotation_obj.mot_index = -1

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

        only_digit = len(label_list) > 0
        for label in label_list:
            if not label.isdigit():
                only_digit = False
                break
        if only_digit:
            label_list.sort(key=lambda x: int(x))

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

    def export_yolo_annotation(
            self,
            output_dir: str = "",
            name_front: str = "",
            replace_label_dict: dict = None
    ) -> bool:
        if len(output_dir) == 0:
            output_dir = os.path.join(self.dir_path, "labels")

        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        for annotation_obj in self.annotation_file:
            yolo_text = annotation_obj.to_yolo_format(
                replace_label_dict=replace_label_dict
            ).strip() + "\n"
            yolo_file_path = \
                os.path.join(
                    output_dir,
                    name_front + annotation_obj.file_name_no_extension + ".txt"
                )

            with open(yolo_file_path, "w") as f:
                f.write(yolo_text)

        return True

    def to_mot_gt_txt(self) -> str:
        class_list = self.update_label_list()
        if len(class_list) == 0:
            return ""

        class_list_int = [int(i) for i in class_list if i.isdigit()]
        if len(class_list_int) != len(class_list):
            print(f"Error: Class Name Not All Integer({self.dir_path})")
            return ""
        class_list_int.sort()
        class_list = [str(i) for i in class_list_int]

        final_text = ""

        for class_name in class_list:

            class_annotation_obj_list: List[XAnyLabelingAnnotation] = \
                self.label_obj_list_dict[class_name].copy()
            class_annotation_obj_list.sort(key=lambda x: x.mot_index)

            for annotation_obj in class_annotation_obj_list:
                for rect_annotation in annotation_obj.rect_annotation_list:
                    if rect_annotation.label == class_name:
                        frame = annotation_obj.mot_index
                        label = class_name

                        x = rect_annotation.x1
                        y = rect_annotation.y1
                        w = rect_annotation.width
                        h = rect_annotation.height

                        x, y, w, h = (
                            int(x),
                            int(y),
                            int(w),
                            int(h)
                        )

                        final_text += f"{frame},{label},{x},{y},{w},{h},1,1,1\n"

                        break

            # for annotation_file in self.annotation_file:
            #     for rect_annotation in annotation_file.rect_annotation_list:
            #         if rect_annotation.label == class_name:
            #             frame = int(annotation_file.file_name_no_extension)
            #             label = class_name
            #
            #             x = rect_annotation.x1
            #             y = rect_annotation.y1
            #             w = rect_annotation.width
            #             h = rect_annotation.height
            #
            #             x, y, w, h = (
            #                 int(x),
            #                 int(y),
            #                 int(w),
            #                 int(h)
            #             )
            #
            #             final_text += f"{frame},{label},{x},{y},{w},{h},1,1,1\n"

        return final_text

    def to_mot_seq_info_ini(self) -> str:
        video_name = os.path.basename(os.path.dirname(self.dir_path))
        sequence_name = os.path.basename(self.dir_path)

        name = f"{video_name}-{sequence_name}"
        im_dir = "img1"
        frame_rate = self.frame_rate
        seq_length = len(self.annotation_file)
        if len(self.annotation_file) == 0:
            return ""
        im_width = self.annotation_file[0].image_width
        im_height = self.annotation_file[0].image_height
        im_ext = self.annotation_file[0].pic_file_extension

        ini_text = (
            f"[Sequence]\n"
            f"name={name}\n"
            f"imDir={im_dir}\n"
            f"frameRate={frame_rate}\n"
            f"seqLength={seq_length}\n"
            f"imWidth={im_width}\n"
            f"imHeight={im_height}\n"
            f"imExt={im_ext}\n"
        )

        return ini_text.strip() + "\n"


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
