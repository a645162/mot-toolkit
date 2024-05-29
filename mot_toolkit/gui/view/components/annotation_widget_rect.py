from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget

from mot_toolkit.datatype.common. \
    rect_data_annotation import RectDataAnnotation
from mot_toolkit.gui.view. \
    components.resizable_rect import ResizableRect


class AnnotationWidgetRect(ResizableRect):
    slot_selected_object: Signal = Signal(QWidget)
    slot_try_to_select: Signal = Signal(QWidget)

    selecting: bool
    __selecting: bool = False

    def __init__(self, parent=None):
        super().__init__(parent)

        self.__init_widget_props()

        self.set_appearance()

    def __init_widget_props(self):
        self.setBorderWidth(8)

    def set_rect_data_annotation(self, rect_data: RectDataAnnotation):
        x1, y1 = int(rect_data.x1), int(rect_data.y1)
        width, height = int(rect_data.width), int(rect_data.height)

        self.x_original = rect_data.x1
        self.y_original = rect_data.y1
        self.width_original = rect_data.width
        self.height_original = rect_data.height

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
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.is_responsible():
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
        if self.selecting:
            self.setBorderColor(Qt.GlobalColor.red)
            self.setFillColor(Qt.GlobalColor.green)
            self.setFillOpacity(0.5)
        else:
            self.setBorderColor(Qt.GlobalColor.blue)
            self.setFillColor(Qt.GlobalColor.transparent)
            self.setFillOpacity(0.3)

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
