from PySide6.QtCore import Signal, QSize
from PySide6.QtGui import QPixmap

from PySide6.QtWidgets import (
    QLabel
)


class ImageViewLabel(QLabel):
    slot_image_changed: Signal = Signal()

    scale_factor: float

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__scale_factor = 1.0

        self.image = None
        self.image_display = None

        self.__setup_widget_properties()

    def __setup_widget_properties(self):
        pass

    def set_image_by_path(self, image_path: str):
        q_pixmap = QPixmap(image_path)

        self.set_image(q_pixmap)

    def set_image(self, image: QPixmap):
        self.image = image

        self.update()

        self.slot_image_changed.emit()

    def get_image(self) -> QPixmap:
        return self.image

    @property
    def scale_factor(self) -> float:
        return self.__scale_factor

    @scale_factor.setter
    def scale_factor(self, value: float):
        self.__scale_factor = value

        self.update()

    def update(self):
        super().update()

        if self.image is None:
            return

        ori_size = self.image.size()
        new_size = QSize(
            int(ori_size.width() * self.scale_factor),
            int(ori_size.height() * self.scale_factor)
        )

        self.image_display = self.image.scaled(new_size)

        self.setPixmap(self.image_display)
        self.setFixedSize(new_size)
