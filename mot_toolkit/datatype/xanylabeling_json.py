from datatype.rect_data_annotation import RectDataAnnotation


class XAnyLabelingRect(RectDataAnnotation):
    def __init__(self, x, y, width, height, label):
        super().__init__(x, y, width, height)
        self.label = label
