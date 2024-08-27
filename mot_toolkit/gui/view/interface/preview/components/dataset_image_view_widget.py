from typing import List

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap, QCursor
from PySide6.QtWidgets import QMenu

from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotation
from mot_toolkit.gui.view. \
    components.annotation_widget_rect import AnnotationWidgetRect
from mot_toolkit.gui.view. \
    components.scroll_image_view import ScrollImageView


class DatasetImageView(ScrollImageView):
    slot_previous_image: Signal = Signal()
    slot_next_image: Signal = Signal()

    slot_save: Signal = Signal()

    slot_selection_changed: Signal = Signal(int)

    __annotation_obj: XAnyLabelingAnnotation
    __picture_file_path: str = ""

    current_q_pixmap: QPixmap = None
    __zoom_factor: float = 1.0

    annotation_widget_rect_list: List[AnnotationWidgetRect]

    object_menu: QMenu = None
    __reverse_color: bool = False
    __theme_name: str = "light_default"

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.annotation_widget_rect_list = []

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
                    case Qt.Key.Key_A:
                        self.slot_previous_image.emit()
                        return
                    case Qt.Key.Key_D:
                        self.slot_next_image.emit()
                        return

            case Qt.KeyboardModifier.ControlModifier:
                match key:
                    case Qt.Key.Key_S:
                        self.slot_save.emit()
                        return

        super().keyPressEvent(event)

    def update_dataset_annotation_path(
            self,
            annotation_obj: XAnyLabelingAnnotation
    ):
        self.__annotation_obj = annotation_obj

        # print(annotation_obj.file_path)
        # print(annotation_obj.pic_path)

        try:
            self.current_q_pixmap = QPixmap(annotation_obj.pic_path)
            self.init_annotation_widget()
            self.image_view.set_image(self.current_q_pixmap)
        except Exception as e:
            print(e)
            self.image_view.set_image(None)

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
            rect_widget.slot_try_to_show_menu.connect(
                self.__rect_widget_try_to_show_menu
            )

            # Set Theme
            rect_widget.activate_theme_name = self.__theme_name
            rect_widget.set_appearance()

            # Set Label
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
        if index < -1 or index >= len(self.annotation_widget_rect_list):
            return

        for i, rect_widget in enumerate(self.annotation_widget_rect_list):
            if i == index:
                rect_widget.selecting = True
            else:
                rect_widget.selecting = False

    @property
    def zoom_factor(self) -> float:
        return self.__zoom_factor

    @zoom_factor.setter
    def zoom_factor(self, value: float):
        self.__zoom_factor = value
        self.slot_try_to_zoom.emit(value)

    def __zoom_triggered(self, float_value: float):
        if self.image_view.image is None:
            return

        # Set Image Scale Factor
        self.image_view.scale_factor = float_value

        # Set Annotation Scale Factor
        self.set_annotation_scale_factor(float_value)

    def __rect_widget_try_to_show_menu(self, widget_obj: AnnotationWidgetRect):
        if self.object_menu is None:
            return
        # Get Mouse Position
        # Show Menu
        self.object_menu.exec_(QCursor.pos())

    def get_fit_scale_factor(self) -> float:
        if self.image_view.image is None:
            return 1.0

        max_width = self.scroll_area.width() - 5
        max_height = self.scroll_area.height() - 5

        ori_width = self.image_view.image.width()
        ori_height = self.image_view.image.height()

        factor = max_width / ori_width
        if ori_height * factor > max_height:
            factor = max_height / ori_height

        return factor

    def set_to_fit_scale_factor(self):
        factor = self.get_fit_scale_factor()
        self.slot_try_to_zoom.emit(factor)
        # self.image_view.scale_factor = factor

    def try_to_reverse_color(self):
        self.reverse_color = not self.reverse_color

    @property
    def reverse_color(self) -> bool:
        return self.__reverse_color

    @reverse_color.setter
    def reverse_color(self, value: bool):
        self.__reverse_color = value

        theme_name = "light_default"
        if value:
            theme_name = "dark_default"
        self.__theme_name = theme_name

        self.update_theme()

    def update_theme(self, theme_name: str = ""):
        theme_name = theme_name.strip()

        if len(theme_name) == 0:
            theme_name = self.__theme_name
        else:
            self.__theme_name = theme_name

        for rect_widget in self.annotation_widget_rect_list:
            rect_widget.activate_theme_name = theme_name
            rect_widget.set_appearance()
