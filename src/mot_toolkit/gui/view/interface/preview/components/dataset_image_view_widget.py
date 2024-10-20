from typing import List

from PySide6.QtCore import Signal, Qt, QPoint, QRect
from PySide6.QtGui import QPixmap, QCursor
from PySide6.QtWidgets import QMenu

from mot_toolkit.datatype.xanylabeling import (
    XAnyLabelingAnnotation, XAnyLabelingRect
)
from mot_toolkit.gui.view.components.widget. \
    rect.annotation_widget_rect import AnnotationWidgetRect
from mot_toolkit.gui.view.components.widget. \
    combination.scroll_image_view import ScrollImageView


class DatasetImageView(ScrollImageView):
    slot_previous_image: Signal = Signal()
    slot_next_image: Signal = Signal()

    slot_save: Signal = Signal()

    slot_selection_changed: Signal = Signal(int)

    slot_scroll: Signal = Signal(tuple)

    slot_property_changed: Signal = Signal()

    __annotation_obj: XAnyLabelingAnnotation
    __previous_annotation_obj: XAnyLabelingAnnotation

    __picture_file_path: str = ""

    current_q_pixmap: QPixmap = None
    __zoom_factor: float = 1.0

    annotation_widget_rect_list: List[AnnotationWidgetRect]

    __show_box: bool = True
    __show_box_label: bool = True
    __only_show_selected: bool = False

    object_menu: QMenu = None
    __reverse_color: bool = False
    __theme_name: str = "light"

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.annotation_widget_rect_list = []

        self.__setup_widget_properties()

        self.__init_widgets()

        self.__init_shortcut()

    def __setup_widget_properties(self):
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def __init_widgets(self):
        self.slot_try_to_zoom.connect(self.__zoom_triggered)

        self.image_view.slot_image_scale_factor_changed_and_displayed.connect(
            self.__image_scale_factor_changed
        )

        # Listen Scroll Bar Value Changed
        self.scroll_area.verticalScrollBar().valueChanged \
            .connect(self.__scroll_value_changed)
        self.scroll_area.horizontalScrollBar().valueChanged \
            .connect(self.__scroll_value_changed)

    def __init_shortcut(self):
        pass

    def get_mouse_image_position(self) -> QPoint:
        # Get Mouse
        mouse_pos = QCursor.pos()

        # Get relative position of self.image_view
        mouse_pos = mouse_pos - self.image_view.mapToGlobal(QPoint(0, 0))

        return mouse_pos

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
                    case Qt.Key.Key_Up:
                        print("Up")
                        return

            case Qt.KeyboardModifier.ControlModifier:
                match key:
                    case Qt.Key.Key_S:
                        self.slot_save.emit()
                        return

            case Qt.KeyboardModifier.AltModifier:
                # Alt
                match key:
                    case Qt.Key.Key_R:
                        self.resize_annotation_by_previous(move=True)
                        return
                    case Qt.Key.Key_C:
                        self.__move_annotation_to_mouse_position()
                        return
                    case Qt.Key.Key_V:
                        self.resize_annotation_by_previous(move=False)
                        self.__move_annotation_to_mouse_position()
                        return
                    case Qt.Key.Key_H:
                        self.show_box = not self.show_box
                        self.slot_property_changed.emit()
                        return
                    case Qt.Key.Key_L:
                        self.show_box_label = not self.show_box_label
                        self.slot_property_changed.emit()
                        return

        if (
                modifiers & Qt.KeyboardModifier.AltModifier and
                modifiers & Qt.KeyboardModifier.ShiftModifier
        ):
            target_pos: QPoint = self.get_mouse_image_position()
            selected_obj: AnnotationWidgetRect | None = None

            for rect_widget_obj in self.annotation_widget_rect_list:
                if rect_widget_obj.selecting:
                    selected_obj = rect_widget_obj
                    break

            if selected_obj is not None:
                match key:
                    case Qt.Key.Key_W:
                        # Top
                        selected_obj.rect_top = target_pos.y()
                        return
                    case Qt.Key.Key_A:
                        # Left
                        selected_obj.rect_left = target_pos.x()
                        return
                    case Qt.Key.Key_S:
                        # Bottom
                        selected_obj.rect_bottom = target_pos.y()
                        return
                    case Qt.Key.Key_D:
                        # Right
                        selected_obj.rect_right = target_pos.x()
                        return

                    case Qt.Key.Key_Q:
                        # Top + Left
                        selected_obj.rect_left = target_pos.x()
                        selected_obj.rect_top = target_pos.y()
                        return
                    case Qt.Key.Key_E:
                        # Top + Right
                        selected_obj.rect_right = target_pos.x()
                        selected_obj.rect_top = target_pos.y()
                        return
                    case Qt.Key.Key_Z:
                        # Bottom + Left
                        selected_obj.rect_left = target_pos.x()
                        selected_obj.rect_bottom = target_pos.y()
                        return
                    case Qt.Key.Key_C:
                        # Bottom + Right
                        selected_obj.rect_right = target_pos.x()
                        selected_obj.rect_bottom = target_pos.y()
                        return

                return
        super().keyPressEvent(event)

        if self.parent() is not None:
            self.parent().keyPressEvent(event)

    def update_dataset_annotation_path(
            self,
            annotation_obj: XAnyLabelingAnnotation,
            previous_annotation_obj: XAnyLabelingAnnotation = None
    ):
        self.__annotation_obj = annotation_obj
        self.__previous_annotation_obj = previous_annotation_obj

        # print(annotation_obj.file_path)
        # print(annotation_obj.pic_path)

        try:
            self.current_q_pixmap = QPixmap(annotation_obj.pic_path)
            self.image_view.set_image(self.current_q_pixmap)
            self.init_annotation_widget()
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
            for i, rect_widget_obj in enumerate(self.annotation_widget_rect_list):
                if obj == rect_widget_obj:
                    index = i
                    break

            if index != -1:
                self.slot_selection_changed.emit(index)

        for rect_item in self.__annotation_obj.rect_annotation_list:
            # print(rect_item)
            rect_widget = AnnotationWidgetRect(parent=self.image_view)

            rect_widget.source = rect_item

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
            rect_widget.label_text = rect_widget.label

            # Set Rect Scale Factor when the image is changed
            rect_widget.scale_factor = self.image_view.scale_factor

            rect_widget.set_rect_data_annotation(rect_item)

            # Set the boundary for the rectangle
            rect_widget.boundary = self.image_view.image_display.rect()

            # rect_widget.show()

            # Set Show Status
            rect_widget.only_show_selected = self.only_show_selected
            rect_widget.show_box = self.show_box
            rect_widget.show_box_label = self.show_box_label

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

    def __image_scale_factor_changed(self):
        self.update_all_rect_widget_boundary()

    def update_all_rect_widget_boundary(self):
        boundary = None

        # if self.current_q_pixmap is not None:
        #     boundary = self.current_q_pixmap.rect()

        if self.image_view.image_display is not None:
            boundary = self.image_view.image_display.rect()

        if boundary is None:
            return

        for rect_widget in self.annotation_widget_rect_list:
            if (
                    rect_widget is not None and
                    rect_widget.parent() is not None
            ):
                rect_widget.boundary = boundary

    def __rect_widget_try_to_show_menu(self):
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

        theme_name = "light"
        if value:
            theme_name = "dark"
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

    @property
    def show_box(self) -> bool:
        return self.__show_box

    @show_box.setter
    def show_box(self, value: bool):
        self.__show_box = value

        for rect_widget in self.annotation_widget_rect_list:
            rect_widget.show_box = value

    @property
    def show_box_label(self) -> bool:
        return self.__show_box_label

    @show_box_label.setter
    def show_box_label(self, value: bool):
        self.__show_box_label = value

        for rect_widget in self.annotation_widget_rect_list:
            rect_widget.show_box_label = value

    @property
    def only_show_selected(self) -> bool:
        return self.__only_show_selected

    @only_show_selected.setter
    def only_show_selected(self, value: bool):
        self.__only_show_selected = value

        for rect_widget in self.annotation_widget_rect_list:
            rect_widget.only_show_selected = value

    def __move_annotation_to_mouse_position(self):
        # Get Mouse Position
        mouse_pos = self.image_view.mapFromGlobal(QCursor.pos())

        # print(mouse_pos.x(), mouse_pos.y())

        # Set Activated Annotation Center Position
        for rect_widget in self.annotation_widget_rect_list:
            if (
                    rect_widget is not None and
                    rect_widget.selecting
            ):
                # print("Found Selection Rect")

                rect_widget.center_x = mouse_pos.x()
                rect_widget.center_y = mouse_pos.y()

                rect_widget.modify()

    def resize_annotation_by_previous(self, move: bool = True):
        selected_rect_widget = None
        for rect_widget in self.annotation_widget_rect_list:
            if (
                    rect_widget is not None and
                    rect_widget.selecting
            ):
                selected_rect_widget = rect_widget
                break
        if (
                selected_rect_widget is None or
                self.__previous_annotation_obj is None or
                self.__previous_annotation_obj.rect_annotation_list is None or
                len(self.__previous_annotation_obj.rect_annotation_list) == 0
        ):
            return

        previous_rect_obj: XAnyLabelingRect | None = None
        for pre_annotation in self.__previous_annotation_obj.rect_annotation_list:
            if selected_rect_widget.label == pre_annotation.label:
                previous_rect_obj = pre_annotation
                break

        if previous_rect_obj is None:
            return

        selected_rect_widget.width_original = previous_rect_obj.width
        selected_rect_widget.height_original = previous_rect_obj.height

        if move:
            selected_rect_widget.center_x_original = previous_rect_obj.center_x
            selected_rect_widget.center_y_original = previous_rect_obj.center_y

        selected_rect_widget.modify()

    def update(self):
        super().update()

        self.image_view.update()

    @property
    def vertical_pos(self) -> int:
        return self.scroll_area.verticalScrollBar().value()

    @vertical_pos.setter
    def vertical_pos(self, value: int):
        if value < 0:
            value = 0
        if value > self.scroll_area.verticalScrollBar().maximum():
            value = self.scroll_area.verticalScrollBar().maximum()

        self.scroll_area.verticalScrollBar().setValue(value)

    @property
    def horizontal_pos(self) -> int:
        return self.scroll_area.horizontalScrollBar().value()

    @horizontal_pos.setter
    def horizontal_pos(self, value: int):
        if value < 0:
            value = 0
        if value > self.scroll_area.horizontalScrollBar().maximum():
            value = self.scroll_area.horizontalScrollBar().maximum()

        self.scroll_area.horizontalScrollBar().setValue(value)

    def display_area(self) -> tuple:
        x1, y1 = self.horizontal_pos, self.vertical_pos
        x2, y2 = (
            x1 + self.scroll_area.width(),
            y1 + self.scroll_area.height()
        )

        return x1, y1, x2, y2

    def display_q_rect(self) -> QRect:
        x1, y1, x2, y2 = self.display_area()

        return QRect(x1, y1, x2, y2)

    def __scroll_value_changed(self):
        self.slot_scroll.emit(self.display_area())

    @property
    def selection_widget(self) -> AnnotationWidgetRect | None:
        for rect_widget in self.annotation_widget_rect_list:
            if rect_widget.selecting:
                return rect_widget
        return None
