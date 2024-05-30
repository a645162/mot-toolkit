import sys
import uuid

from PySide6.QtWidgets import QApplication, QLabel, QWidget, QGraphicsOpacityEffect
from PySide6.QtGui import QPainter, QPen, QBrush, QPixmap
from PySide6.QtCore import Qt, QRect, Signal


class ResizableRect(QWidget):
    scale_factor: float

    __modified: bool = False

    slot_modified: Signal = Signal(QWidget)
    slot_resized: Signal = Signal(QWidget)

    label: str = ""

    ori_x: int = 0
    ori_y: int = 0
    ori_w: int = 0
    ori_h: int = 0

    uuid: str = ""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.uuid = str(uuid.uuid4())

        self.setMouseTracking(True)

        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.effect.setOpacity(0.5)

        self.lastPos = None
        self.resizing = False
        self.resizeMargin = 5

        self.borderColor = Qt.GlobalColor.red
        self.borderWidth = 2

        self.fillColor = Qt.GlobalColor.transparent
        self.fillOpacity = 0.5

        self.boundary = QRect()  # Initialize with an empty rectangle

        self.__scale_factor: float = 1.0

    def __eq__(self, other):
        return len(self.uuid.strip()) > 0 and self.uuid == other.uuid

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setPen(QPen(self.borderColor, self.borderWidth))
        brush = QBrush(self.fillColor)
        qp.setBrush(brush)
        qp.drawRect(self.rect())

    def setBorderColor(self, color):
        self.borderColor = color
        self.update()

    def setBorderWidth(self, width):
        self.borderWidth = width
        self.update()

    def setFillColor(self, color):
        self.fillColor = color
        self.update()

    def setFillOpacity(self, opacity):
        self.fillOpacity = opacity
        self.effect.setOpacity(opacity)
        self.update()

    def setBoundary(self, rect):
        self.boundary = rect

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.lastPos = event.position().toPoint()
            # Check if the click is within the resize margin
            self.resizing = (
                    event.position().x() > self.width() - self.resizeMargin or
                    event.position().y() > self.height() - self.resizeMargin
            )

    def mouseMoveEvent(self, event):
        if self.lastPos:
            if self.resizing:
                # Resize the rectangle within the boundary
                new_width = min(self.width() + event.position().x() - self.lastPos.x(), self.boundary.width())
                new_height = min(self.height() + event.position().y() - self.lastPos.y(), self.boundary.height())
                self.resize(new_width, new_height)
            else:
                # Move the rectangle within the boundary
                new_x = self.x() + event.position().x() - self.lastPos.x()
                new_y = self.y() + event.position().y() - self.lastPos.y()
                new_x = max(self.boundary.left(), min(new_x, self.boundary.right() - self.width()))
                new_y = max(self.boundary.top(), min(new_y, self.boundary.bottom() - self.height()))
                self.move(new_x, new_y)
            self.lastPos = event.position().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.lastPos = None
            self.resizing = False

            self.ori_x = int(self.x() / self.scale_factor)
            self.ori_y = int(self.y() / self.scale_factor)
            self.ori_w = int(self.width() / self.scale_factor)
            self.ori_h = int(self.height() / self.scale_factor)

            self.slot_resized.emit(self)

            # print("Modified!")
            self.__modified = True
            self.slot_modified.emit(self)

    def is_modified(self) -> bool:
        return self.__modified

    def __str__(self):
        return f"{self.label} {self.ori_x}, {self.ori_y}, {self.ori_w}, {self.ori_h}"

    @property
    def scale_factor(self):
        return self.__scale_factor

    @scale_factor.setter
    def scale_factor(self, value: float):
        self.__scale_factor = value

        self.update()

    @property
    def x1_original(self):
        return self.ori_x

    @x1_original.setter
    def x1_original(self, value: int):
        self.ori_x = value
        self.update()

    @property
    def y1_original(self):
        return self.ori_y

    @y1_original.setter
    def y1_original(self, value: int):
        self.ori_y = value
        self.update()

    @property
    def width_original(self):
        return self.ori_w

    @width_original.setter
    def width_original(self, value: int):
        self.ori_w = value
        self.update()

    @property
    def height_original(self):
        return self.ori_h

    @height_original.setter
    def height_original(self, value: int):
        self.ori_h = value
        self.update()

    @property
    def x2_original(self):
        return self.ori_x + self.ori_w

    @property
    def y2_original(self):
        return self.ori_y + self.ori_h

    def calc_new_size(self, scale_factor: float = 0) -> QRect:
        if scale_factor == 0:
            scale_factor = self.scale_factor

        new_x = int(self.ori_x * scale_factor)
        new_y = int(self.ori_y * scale_factor)
        new_w = int(self.ori_w * scale_factor)
        new_h = int(self.ori_h * scale_factor)

        return QRect(new_x, new_y, new_w, new_h)

    def update(self):
        self.setGeometry(
            self.calc_new_size(scale_factor=self.scale_factor)
        )

        super().update()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = QWidget()
    label = QLabel(window)
    label.setPixmap(QPixmap('../../../../Test/00000000.jpg'))

    rect = ResizableRect(window)
    rect.setGeometry(50, 50, 100, 100)

    rect.setBorderColor(Qt.GlobalColor.blue)
    rect.setBorderWidth(8)
    rect.setFillColor(Qt.GlobalColor.green)
    rect.setFillOpacity(0.3)

    # Set the boundary for the rectangle
    rect.setBoundary(QRect(0, 0, 600, 800))

    window.setGeometry(100, 100, 400, 300)
    window.show()
    sys.exit(app.exec())
