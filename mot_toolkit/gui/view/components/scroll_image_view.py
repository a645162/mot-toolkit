from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QScrollArea,
)

from mot_toolkit.gui.view. \
    components.base_image_view_graphics import ImageViewGraphics
from mot_toolkit.gui.view. \
    components.base_image_view_label import ImageViewLabel


class ScrollImageView(QWidget):
    ctrl_pressing: bool = False

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
        # self.image_view = ImageViewLabel(parent=self.scroll_area)

        self.scroll_area.setWidget(self.image_view)
        self.v_layout.addWidget(self.scroll_area)

        # No Scroll Area
        # self.image_view = ImageViewGraphics(parent=self)
        # self.v_layout.addWidget(self.image_view)

    def keyPressEvent(self, event):
        key = event.key()
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.ctrl_pressing = True
            if key == Qt.Key.Key_PageUp:
                return
            elif key == Qt.Key.Key_PageDown:
                return

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        # key = event.key()
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.ctrl_pressing = False

        super().keyReleaseEvent(event)

    def wheelEvent(self, event):
        if not self.ctrl_pressing:
            super().wheelEvent(event)
            return

        angle = event.angleDelta()

        if angle.y() > 0:
            print("Wheel Up")
        else:
            print("Wheel Down")
