from typing import List

from mot_toolkit.parser.json_parser import parse_json_to_dict

from mot_toolkit.datatype.xanylabeling_json import (
    XAnyLabelingAnnotation,
    XAnyLabelingRect
)


def parse_xanylabeling_json(json_path) -> XAnyLabelingAnnotation:
    data: dict = parse_json_to_dict(json_path)
    result: XAnyLabelingAnnotation = XAnyLabelingAnnotation()

    result.version = data.get("version", "")
    result.flags = data.get("flags", {})

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

    return result


if __name__ == '__main__':
    result = parse_xanylabeling_json(
        r"H:\LCF\mot-toolkit\Test\00000000.json"
    )
    print(result.version)
    print()
    for rect_item in result.rect_annotation:
        print(str(rect_item))
