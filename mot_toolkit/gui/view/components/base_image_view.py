from PySide6.QtCore import Signal
from PySide6.QtGui import QPixmap

from PySide6.QtWidgets import (
    QLabel
)


class ImageView(QLabel):
    slot_image_changed: Signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.image = None
        self.__setup_widget_properties()

    def __setup_widget_properties(self):
        pass

    def set_image_by_path(self, image_path: str):
        q_pixmap = QPixmap(image_path)
        self.set_image(q_pixmap)

    def set_image(self, image: QPixmap):
        self.image = image
        self.setPixmap(image)
        self.slot_image_changed.emit()

    def get_image(self) -> QPixmap:
        return self.image
