from typing import List
import json

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

        result_dict["version"] = self.version
        result_dict["flags"] = self.flags
        result_dict["shapes"] = []
        for rect_item in self.rect_annotation_list:
            result_dict["shapes"].append({
                "label": rect_item.label,
                "text": rect_item.text,
                "points": rect_item.get_rect_two_point(),
                "group_id": rect_item.group_id,
                "shape_type": rect_item.shape_type,
                "flags": rect_item.flags
            })
        result_dict["imagePath"] = self.image_path
        result_dict["imageData"] = self.image_data
        result_dict["imageHeight"] = self.image_height
        result_dict["imageWidth"] = self.image_width

        return result_dict

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

    def fix_bugs(self):
        for rect_item in self.rect_annotation_list:
            rect_item.fix_bugs()


def parse_xanylabeling_json(json_path: str) -> XAnyLabelingAnnotation:
    data: dict = parse_json_to_dict(json_path)

    current_annotation_obj: XAnyLabelingAnnotation = \
        XAnyLabelingAnnotation()

    current_annotation_obj.version = data.get("version", "")
    current_annotation_obj.flags = data.get("flags", {})

    current_annotation_obj.file_path = json_path

    shapes_list: List[dict] = data.get("shapes", [])
    for shape_item in shapes_list:
        item_label = shape_item.get("label", "")
        item_text = shape_item.get("text", "")
        item_points = shape_item.get("points", [])
        item_group_id = shape_item.get("group_id", "")
        item_shape_type = shape_item.get("shape_type", "")
        item_flags = shape_item.get("flags", {})

        if item_shape_type == "rectangle":
            current_rect_annotation = XAnyLabelingRect(item_label)

            current_rect_annotation.text = item_text

            current_rect_annotation.set_by_rect_two_point(
                item_points[0][0], item_points[0][1],
                item_points[1][0], item_points[1][1]
            )

            current_rect_annotation.group_id = item_group_id
            current_rect_annotation.shape_type = item_shape_type
            current_rect_annotation.flags = item_flags

            current_annotation_obj.rect_annotation_list.append(
                current_rect_annotation
            )
        else:
            print(f"Unknown shape type: {item_shape_type} in {json_path}")

    current_annotation_obj.image_path = data.get("imagePath", "")
    current_annotation_obj.image_data = data.get("imageData", None)
    current_annotation_obj.image_height = data.get("imageHeight", 0)
    current_annotation_obj.image_width = data.get("imageWidth", 0)

    return current_annotation_obj


class XAnyLabelingAnnotationDirectory(AnnotationDirectory):
    annotation_file: List[XAnyLabelingAnnotation] = []

    def __init__(self):
        super().__init__()

    def load_json_files(self):
        if self.is_empty():
            return

        self.annotation_file.clear()

        for json_file in self.file_list:
            annotation = \
                parse_xanylabeling_json(json_file)

            self.annotation_file.append(annotation)

    def save_json_files(self):
        for annotation_obj in self.annotation_file:
            if annotation_obj.is_modified:
                annotation_obj.save()


if __name__ == '__main__':
    # Single File Test
    result = parse_xanylabeling_json(
        r"../../Test/00000000.json"
    )
    print(result.version)
    print()
    for rect_item in result.rect_annotation_list:
        print(str(rect_item))

    # Directory Test
    annotation_directory = XAnyLabelingAnnotationDirectory()
    annotation_directory.dir_path = r"../../Test"
    annotation_directory.walk_dir(recursive=True)
    annotation_directory.sort_path(group_directory=True)
    annotation_directory.load_json_files()

    print()
