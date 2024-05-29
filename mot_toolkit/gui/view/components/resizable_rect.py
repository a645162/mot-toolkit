import sys
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QGraphicsOpacityEffect
from PySide6.QtGui import QPainter, QPen, QBrush, QPixmap
from PySide6.QtCore import Qt, QRect, Signal


class ResizableRect(QWidget):
    scale_factor: float

    __modified: bool = False

    slot_modified: Signal = Signal(QWidget)

    label: str = ""

    def __init__(self, parent=None):
        super().__init__(parent)

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

            # print("Modified!")
            self.__modified = True
            self.slot_modified.emit(self)

    def is_modified(self) -> bool:
        return self.__modified

    def __str__(self):
        return f"{self.label} {self.x_original} {self.y_original} {self.width_original} {self.height_original}"

    @property
    def scale_factor(self):
        return self.__scale_factor

    @scale_factor.setter
    def scale_factor(self, value: float):
        self.__scale_factor = value

        self.setGeometry(
            int(self.x() * value), int(self.y() * value),
            int(self.width() * value), int(self.height() * value)
        )

        self.update()

    @property
    def x_original(self):
        return round(self.x() / self.scale_factor, 1)

    @x_original.setter
    def x_original(self, value: float):
        self.move(int(value * self.scale_factor), self.y())

    @property
    def y_original(self):
        return round(self.y() / self.scale_factor, 1)

    @y_original.setter
    def y_original(self, value: float):
        self.move(self.x(), int(value * self.scale_factor))

    @property
    def width_original(self):
        return round(self.width() / self.scale_factor, 1)

    @width_original.setter
    def width_original(self, value: float):
        self.resize(int(value * self.scale_factor), self.height())

    @property
    def height_original(self):
        return round(self.height() / self.scale_factor, 1)

    @height_original.setter
    def height_original(self, value: float):
        self.resize(self.width(), int(value * self.scale_factor))

    @property
    def x1(self):
        return self.x_original

    @x1.setter
    def x1(self, value: float):
        self.x_original = value

    @property
    def y1(self):
        return self.y_original

    @y1.setter
    def y1(self, value: float):
        self.y_original = value

    @property
    def x2(self):
        return self.x_original + self.width_original

    @x2.setter
    def x2(self, value: float):
        self.width_original = value - self.x_original

    @property
    def y2(self):
        return self.y_original + self.height_original

    @y2.setter
    def y2(self, value: float):
        self.height_original = value - self.y_original


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
