from typing import List

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
    json_path: str = ""

    version: str = ""
    flags: dict = {}

    rect_annotation: List[XAnyLabelingRect] = []

    def __init__(self, label: str = ""):
        super().__init__(label)

    def save_json(self, save_path: str = ""):
        save_path = save_path.strip()
        if len(save_path) == 0:
            save_path = self.json_path

        save_path = save_path.strip()
        if len(save_path) == 0:
            return

        # Save to json file

    def fix_bugs(self):
        for rect_item in self.rect_annotation:
            rect_item.fix_bugs()


def parse_xanylabeling_json(json_path: str) -> XAnyLabelingAnnotation:
    data: dict = parse_json_to_dict(json_path)

    result: XAnyLabelingAnnotation = XAnyLabelingAnnotation()

    result.version = data.get("version", "")
    result.flags = data.get("flags", {})

    result.json_path = json_path
    result.file_path = json_path

    shapes_list: List[dict] = data.get("shapes", [])

    for shape_item in shapes_list:
        item_label = shape_item.get("label", "")
        item_text = shape_item.get("text", "")
        item_points = shape_item.get("points", [])
        item_group_id = shape_item.get("group_id", "")
        item_shape_type = shape_item.get("shape_type", "")
        item_flags = shape_item.get("flags", {})

        if item_shape_type == "rectangle":
            rect_annotation = XAnyLabelingRect(item_label)

            rect_annotation.text = item_text

            rect_annotation.set_by_rect_two_point(
                item_points[0][0], item_points[0][1],
                item_points[1][0], item_points[1][1]
            )

            rect_annotation.group_id = item_group_id
            rect_annotation.shape_type = item_shape_type
            rect_annotation.flags = item_flags

            result.rect_annotation.append(rect_annotation)
        else:
            print(f"Unknown shape type: {item_shape_type} in {json_path}")

    return result


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
        pass


if __name__ == '__main__':
    # Single File Test
    result = parse_xanylabeling_json(
        r"H:\LCF\mot-toolkit\Test\00000000.json"
    )
    print(result.version)
    print()
    for rect_item in result.rect_annotation:
        print(str(rect_item))

    # Directory Test
    annotation_directory = XAnyLabelingAnnotationDirectory()
    annotation_directory.dir_path = r"H:\LCF\mot-toolkit\Test"
    annotation_directory.walk_dir()
    annotation_directory.load_json_files()

    print()
