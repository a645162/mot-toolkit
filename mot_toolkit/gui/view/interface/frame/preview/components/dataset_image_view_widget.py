from typing import List

from PySide6.QtCore import Signal, Qt

from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotation
from mot_toolkit.gui.view. \
    components.annotation_widget_rect import AnnotationWidgetRect
from mot_toolkit.gui.view. \
    components.scroll_image_view import ScrollImageView


class DatasetImageView(ScrollImageView):
    slot_previous_image: Signal = Signal()
    slot_next_image: Signal = Signal()

    __annotation_obj: XAnyLabelingAnnotation
    __picture_file_path: str = ""

    annotation_widget_rect_list: List[AnnotationWidgetRect] = []

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__setup_widget_properties()

    def __setup_widget_properties(self):
        pass

    def __init_shortcut(self):
        pass

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.NoModifier:
            if event.key() == Qt.Key.Key_A:
                self.slot_previous_image.emit()
                return
            elif event.key() == Qt.Key.Key_D:
                self.slot_next_image.emit()
                return

        super().keyPressEvent(event)

    def update_dataset_annotation_path(
            self,
            annotation_obj: XAnyLabelingAnnotation
    ):
        self.__annotation_obj = annotation_obj

        print(annotation_obj.file_path)
        print(annotation_obj.pic_path)

        self.image_view.set_image_by_path(annotation_obj.pic_path)
        self.init_annotation()

    def init_annotation(self):
        # Remove All Old Widget
        for rect_widget in self.annotation_widget_rect_list:
            if rect_widget is not None:
                rect_widget.deleteLater()

        self.annotation_widget_rect_list.clear()

        for rect_item in self.__annotation_obj.rect_annotation_list:
            rect_widget = AnnotationWidgetRect(parent=self.image_view)
            # print(rect_item)
            rect_widget.set_rect_data_annotation(rect_item)

            rect_widget.setBorderColor(Qt.GlobalColor.blue)
            rect_widget.setBorderWidth(8)
            rect_widget.setFillColor(Qt.GlobalColor.green)
            rect_widget.setFillOpacity(0.3)

            # Set the boundary for the rectangle
            rect_widget.setBoundary(self.image_view.get_image().rect())

            rect_widget.show()

            self.annotation_widget_rect_list.append(rect_widget)
