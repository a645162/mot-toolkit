import sys
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QGraphicsOpacityEffect
from PySide6.QtGui import QPainter, QPen, QBrush, QMouseEvent, QPixmap
from PySide6.QtCore import Qt, QRect, QPoint


class ResizableRect(QWidget):
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

    def set_rect_data_annotation(self, rect_data):
        print(
            rect_data.x1, rect_data.y1,
            rect_data.x2, rect_data.y2
        )
        self.setGeometry(
            rect_data.x1,
            rect_data.y1,
            rect_data.x2 - rect_data.x1,
            rect_data.y2 - rect_data.y1
        )
        # Print current position
        print(
            self.x(), self.y(),
            self.width(), self.height()
        )


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
