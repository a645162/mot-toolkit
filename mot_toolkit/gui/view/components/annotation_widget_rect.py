from mot_toolkit.datatype.common.rect_data_annotation import RectDataAnnotation
from mot_toolkit.gui.view.components.resizable_rect import ResizableRect


class AnnotationWidgetRect(ResizableRect):

    def __init__(self, parent=None):
        super().__init__(parent)

    def set_rect_data_annotation(self, rect_data: RectDataAnnotation):
        x1, y1 = int(rect_data.x1), int(rect_data.y1)
        width, height = int(rect_data.width), int(rect_data.height)

        # print(
        #     x1, y1,
        #     width, height
        # )

        self.setGeometry(
            x1, y1,
            width, height
        )

        # Print current position
        # print(
        #     self.x(), self.y(),
        #     self.width(), self.height()
        # )
