from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget

from mot_toolkit.datatype.common. \
    rect_data_annotation import RectDataAnnotation
from mot_toolkit.gui.view. \
    components.resizable_rect import ResizableRect


class AnnotationWidgetRect(ResizableRect):
    slot_selected_object: Signal = Signal(QWidget)

    slot_try_to_select: Signal = Signal(QWidget)
    slot_try_to_show_menu: Signal = Signal(QWidget)

    selecting: bool
    __selecting: bool = False

    final_theme_color: dict = {
        "light_default": {
            "border": Qt.GlobalColor.blue,
            "fill": Qt.GlobalColor.transparent,
            "opacity": 0.3,

            "border_selected": Qt.GlobalColor.red,
            "fill_selected": Qt.GlobalColor.green,
            "opacity_selected": 0.5,
        },
        "dark_default": {
            "border": Qt.GlobalColor.green,
            "fill": Qt.GlobalColor.transparent,
            "opacity": 0.3,

            "border_selected": Qt.GlobalColor.red,
            "fill_selected": Qt.GlobalColor.green,
            "opacity_selected": 0.5,
        }
    }
    theme_color: dict = {}

    activate_theme_name: str = "light_default"

    def __init__(self, parent=None):
        super().__init__(parent)

        self.__init_widget_props()

        self.set_appearance()

    def __init_widget_props(self):
        self.setBorderWidth(8)

    def set_rect_data_annotation(self, rect_data: RectDataAnnotation):
        x1, y1 = int(rect_data.x1), int(rect_data.y1)
        width, height = int(rect_data.width), int(rect_data.height)

        self.ori_x = x1
        self.ori_y = y1
        self.ori_w = width
        self.ori_h = height

        self.update()

        # self.x_original = rect_data.x1
        # self.y_original = rect_data.y1
        # self.width_original = rect_data.width
        # self.height_original = rect_data.height

        # print(
        #     x1, y1,
        #     width, height
        # )

        # self.setGeometry(
        #     x1, y1,
        #     width, height
        # )

        # Print current position
        # print(
        #     self.x(), self.y(),
        #     self.width(), self.height()
        # )

    def is_responsible(self) -> bool:
        if not self.__selecting:
            return False

        return True

    def mousePressEvent(self, event):
        match event.button():
            case Qt.MouseButton.LeftButton:
                if not self.is_responsible():
                    return
            case Qt.MouseButton.RightButton:
                if self.is_responsible():
                    self.slot_try_to_show_menu.emit(self)
                    return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            if not self.is_responsible():
                return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.is_responsible():
                # Try to select
                if not self.__selecting:
                    self.slot_try_to_select.emit(self)

                return

        super().mouseReleaseEvent(event)

    @property
    def selecting(self) -> bool:
        return self.__selecting

    @selecting.setter
    def selecting(self, value: bool):
        self.__selecting = value

        self.set_appearance()

    def set_appearance(self):
        theme_name = self.activate_theme_name
        if theme_name not in self.final_theme_color.keys():
            theme_name = "light_default"

        theme: dict = self.final_theme_color[theme_name]

        if not self.selecting:
            # Not Select
            self.setBorderColor(theme["border"])
            self.setFillColor(theme["fill"])
            self.setFillOpacity(theme["opacity"])
        else:
            # Selecting
            self.setBorderColor(theme["border_selected"])
            self.setFillColor(theme["fill_selected"])
            self.setFillOpacity(theme["opacity_selected"])

    def keyPressEvent(self, event):
        modifiers = event.modifiers()
        key = event.key()
        match modifiers:
            case Qt.KeyboardModifier.NoModifier:
                match key:
                    case Qt.Key.Key_Left:
                        return
                    case Qt.Key.Key_Right:
                        return
            case Qt.KeyboardModifier.ControlModifier:
                pass

        super().keyPressEvent(event)
