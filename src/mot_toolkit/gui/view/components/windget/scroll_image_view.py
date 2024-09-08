from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
)

from mot_toolkit.gui.view.components. \
    windget.base_image_view_graphics import ImageViewGraphics


class ScrollImageView(QWidget):
    slot_try_to_zoom: Signal = Signal(float)

    ctrl_pressing: bool = False

    scale_factor_coefficient: float = 0.1

    __prevent_scroll: bool = False

    # Developing
    auto_prevent_scroll: bool = False

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__setup_widget_properties()

        self.__init_widgets()

    def __setup_widget_properties(self):
        pass

    def __init_widgets(self):
        self.v_layout = QVBoxLayout()
        self.setLayout(self.v_layout)

        # Normal Mode
        self.scroll_area = QScrollArea(parent=self)
        self.image_view = ImageViewGraphics(parent=self.scroll_area)
        self.image_view.pinch_triggered.connect(self.__pinch_triggered)
        # self.image_view = ImageViewLabel(parent=self.scroll_area)

        self.scroll_area.setWidget(self.image_view)
        self.v_layout.addWidget(self.scroll_area)

        # No Scroll Area
        # self.image_view = ImageViewGraphics(parent=self)
        # self.v_layout.addWidget(self.image_view)

    def set_prevent_scroll(self):
        # Disable wheel event
        def __disable_wheel_event(event):
            # Block wheel event
            if self.__prevent_scroll:
                event.ignore()

        self.scroll_area.wheelEvent = __disable_wheel_event

    @property
    def prevent_scroll(self) -> bool:
        return self.__prevent_scroll

    @prevent_scroll.setter
    def prevent_scroll(self, value: bool):
        self.__prevent_scroll = value

        if not self.auto_prevent_scroll:
            return

        if value:
            # Disable horizontal scroll bar
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

            # Disable vertical scroll bar
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        else:
            # Restore horizontal scroll bar
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

            # Restore vertical scroll bar
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

    def zoom_in(self, float_value: float = 0):
        if self.image_view.image is None:
            return

        if float_value == 0:
            float_value = 0.1

        float_value = abs(float_value)

        self.__zoom_delta(float_value)

    def zoom_out(self, float_value: float = 0):
        if self.image_view.image is None:
            return

        if float_value == 0.0:
            float_value = -0.1

        float_value = abs(float_value)

        self.__zoom_delta(-float_value)

    def zoom_restore(self):
        if self.image_view.image is None:
            return

        self.slot_try_to_zoom.emit(1.0)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)

        modifiers = event.modifiers()
        key = event.key()

        match key:
            case Qt.Key.Key_Control:
                self.ctrl_pressing = True
                self.prevent_scroll = True

        match modifiers:
            case Qt.KeyboardModifier.ControlModifier:
                self.ctrl_pressing = True
                self.prevent_scroll = True

                match key:
                    case Qt.Key.Key_0:
                        self.zoom_restore()
                        return
                    case Qt.Key.Key_PageUp:
                        self.zoom_in()
                        return
                    case Qt.Key.Key_PageDown:
                        self.zoom_out()
                        return

    def keyReleaseEvent(self, event):
        key = event.key()
        # print("Key Released:", key)

        match key:
            case Qt.Key.Key_Control:
                self.ctrl_pressing = False
                self.prevent_scroll = False
                # print("Control Released")

        super().keyReleaseEvent(event)

    def wheelEvent(self, event):
        if not self.ctrl_pressing:
            super().wheelEvent(event)
            return

        angle = event.angleDelta()

        if angle.y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def __zoom_delta(self, float_value: float):
        if float_value != 0:

            new_value = (
                    self.image_view.scale_factor +
                    float_value * self.scale_factor_coefficient
            )

            if not self.image_view.check_new_scale_factor(new_value):
                return

            self.slot_try_to_zoom.emit(new_value)

    def __pinch_triggered(self, float_value: float):
        self.__zoom_delta(float_value)
