from typing import List

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap

from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotation
from mot_toolkit.gui.view. \
    components.annotation_widget_rect import AnnotationWidgetRect
from mot_toolkit.gui.view. \
    components.scroll_image_view import ScrollImageView


class DatasetImageView(ScrollImageView):
    slot_previous_image: Signal = Signal()
    slot_next_image: Signal = Signal()

    slot_selection_changed: Signal = Signal(int)

    __annotation_obj: XAnyLabelingAnnotation
    __picture_file_path: str = ""

    current_q_pixmap: QPixmap = None

    annotation_widget_rect_list: List[AnnotationWidgetRect] = []

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__setup_widget_properties()

        self.__init_widgets()

        self.__init_shortcut()

    def __setup_widget_properties(self):
        pass

    def __init_widgets(self):
        self.slot_try_to_zoom.connect(self.__zoom_triggered)

    def __init_shortcut(self):
        pass

    def keyPressEvent(self, event):
        modifiers = event.modifiers()
        key = event.key()

        match modifiers:
            case Qt.KeyboardModifier.NoModifier:
                match key:
                    case Qt.Key.Key_Up:
                        self.slot_previous_image.emit()
                        return
                    case Qt.Key.Key_Down:
                        self.slot_next_image.emit()
                        return
                    case Qt.Key.Key_Left:
                        self.slot_previous_image.emit()
                        return
                    case Qt.Key.Key_Right:
                        self.slot_next_image.emit()
                        return
                    case Qt.Key.Key_A:
                        self.slot_previous_image.emit()
                        return
                    case Qt.Key.Key_D:
                        self.slot_next_image.emit()
                        return

            case Qt.KeyboardModifier.ControlModifier:
                match key:
                    case Qt.Key.Key_S:
                        self.__annotation_obj.is_modified = True
                        self.__annotation_obj.save()
                        return

        super().keyPressEvent(event)

    def update_dataset_annotation_path(
            self,
            annotation_obj: XAnyLabelingAnnotation
    ):
        self.__annotation_obj = annotation_obj

        # print(annotation_obj.file_path)
        # print(annotation_obj.pic_path)

        self.current_q_pixmap = QPixmap(annotation_obj.pic_path)
        self.init_annotation_widget()
        self.image_view.set_image(self.current_q_pixmap)

    def init_annotation_widget(self):
        # Remove All Old Widget
        for rect_widget in self.annotation_widget_rect_list:
            if (
                    rect_widget is not None and
                    rect_widget.parent() is not None
            ):
                rect_widget.deleteLater()

        self.annotation_widget_rect_list.clear()

        def try_to_select(obj: AnnotationWidgetRect):
            index = -1
            for i, rect_widget in enumerate(self.annotation_widget_rect_list):
                if obj == rect_widget:
                    index = i
                    break

            if index != -1:
                self.slot_selection_changed.emit(index)

        for rect_item in self.__annotation_obj.rect_annotation_list:
            # print(rect_item)
            rect_widget = AnnotationWidgetRect(parent=self.image_view)
            rect_widget.slot_try_to_select.connect(try_to_select)
            rect_widget.slot_resized.connect(self.__rect_widget_resized)

            rect_widget.label = rect_item.label

            # Set Rect Scale Factor when the image is changed
            rect_widget.scale_factor = self.image_view.scale_factor

            rect_widget.set_rect_data_annotation(rect_item)

            # Set the boundary for the rectangle
            rect_widget.setBoundary(self.current_q_pixmap.rect())

            rect_widget.show()

            self.annotation_widget_rect_list.append(rect_widget)

    def __rect_widget_resized(self, obj: AnnotationWidgetRect):
        index = -1

        for i, rect_widget in enumerate(self.annotation_widget_rect_list):
            if obj == rect_widget:
                index = i
                break

        if index == -1:
            return

        self.__annotation_obj.rect_annotation_list[index]. \
            set_rect_two_point_2dim_array(
            obj.get_rect_two_point_2dim_array()
        )
        self.__annotation_obj.modifying()

    def set_annotation_scale_factor(self, scale_factor: float):
        for rect_widget in self.annotation_widget_rect_list:
            if (
                    rect_widget is not None and
                    rect_widget.parent() is not None
            ):
                rect_widget.scale_factor = scale_factor

    def set_selection_rect_index(self, index):
        if index < 0 or index >= len(self.annotation_widget_rect_list):
            return

        for i, rect_widget in enumerate(self.annotation_widget_rect_list):
            if i == index:
                rect_widget.selecting = True
            else:
                rect_widget.selecting = False

    def __zoom_triggered(self, float_value: float):
        # Set Image Scale Factor
        self.image_view.scale_factor = float_value

        # Set Annotation Scale Factor
        self.set_annotation_scale_factor(float_value)
