from typing import List

from mot_toolkit.datatype.rect_data_annotation import (
    RectDataAnnotation
)


class XAnyLabelingRect(RectDataAnnotation):
    group_id: str = ""
    shape_type: str = ""
    flags: dict = {}

    def __init__(self, label: str = ""):
        super().__init__(label)


class XAnyLabelingAnnotation:
    json_path: str = ""

    version: str = ""
    flags: dict = {}

    rect_annotation: List[XAnyLabelingRect] = []

    def __init__(self, label: str = ""):
        super().__init__()

        self.label = label

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
