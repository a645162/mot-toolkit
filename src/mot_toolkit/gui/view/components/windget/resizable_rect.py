import sys
import uuid

from PySide6.QtWidgets import QApplication, QLabel, QWidget, QGraphicsOpacityEffect
from PySide6.QtGui import QPainter, QPen, QBrush, QPixmap
from PySide6.QtCore import Qt, QRect, Signal

from mot_toolkit.utils.qt.q_application import getQApplication
from mot_toolkit.utils.system.dpi_ratio import q_rect_by_factor


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

    __effect: QGraphicsOpacityEffect

    def __init__(
            self,
            parent=None,
            x: int = 0,
            y: int = 0,
            width: int = 10,
            height: int = 10,
    ):
        super().__init__(parent=parent)

        self.uuid = str(uuid.uuid4())

        self.setMouseTracking(True)

        self.__global_opacity = 1.0

        self.__effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.__effect)
        self.__effect.setOpacity(self.__global_opacity)

        self.lastPos = None
        self.resizing = False
        self.resizeMargin = 5

        self.__border_color = Qt.GlobalColor.red
        self.__border_width = 2
        # Define the opacity for the border
        # 100% opaque border
        self.__border_opacity = 1.0

        self.__fill_color = Qt.GlobalColor.transparent
        # Define the opacity for the fill area
        # 50% opaque fill
        self.__fill_opacity = 0.5

        # Initialize with an empty rectangle
        self.__boundary = QRect()

        self.__scale_factor: float = 1.0

        # Default Size
        self.now_x = x
        self.now_y = y
        self.now_width = width
        self.now_height = height

    def __eq__(self, other):
        return len(self.uuid.strip()) > 0 and self.uuid == other.uuid

    @property
    def border_color(self):
        return self.__border_color

    @border_color.setter
    def border_color(self, color):
        self.__border_color = color

        self.update()

    @property
    def border_width(self):
        return self.__border_width

    @border_width.setter
    def border_width(self, width):
        self.__border_width = width

        self.update()

    @property
    def border_opacity(self):
        return self.__border_opacity

    @border_opacity.setter
    def border_opacity(self, opacity):
        self.__border_opacity = opacity

        self.update()

    @property
    def fill_color(self):
        return self.__fill_color

    @fill_color.setter
    def fill_color(self, color):
        self.__fill_color = color

        self.update()

    @property
    def fill_opacity(self):
        return self.__fill_opacity

    @fill_opacity.setter
    def fill_opacity(self, opacity):
        self.__fill_opacity = opacity

        self.update()

    def paintEvent(self, event):
        area = self.rect()

        qp = QPainter(self)

        # Filling
        pen = QPen(self.border_color, self.border_width)
        brush = QBrush(self.fill_color)

        qp.setPen(pen)
        qp.setBrush(brush)
        qp.setOpacity(self.fill_opacity)
        qp.drawRect(area)

        # Border
        pen = QPen(self.border_color, self.border_width)
        brush = QBrush(Qt.GlobalColor.transparent)

        qp.setPen(pen)
        qp.setBrush(brush)
        qp.setOpacity(self.border_opacity)

        # Draw the border rectangle
        qp.drawRect(area)

        # End the QPainter object, committing all the drawing operations
        qp.end()

    @property
    def min_width(self):
        return self.border_width * 2

    @property
    def min_height(self):
        return self.border_width * 2

    @property
    def global_opacity(self):
        return self.__global_opacity

    @global_opacity.setter
    def global_opacity(self, opacity):
        self.__global_opacity = opacity

        if hasattr(self, "__effect") and self.__effect is not None:
            self.__effect.setOpacity(opacity)

        self.update()

    @property
    def boundary(self):
        return self.__boundary

    @boundary.setter
    def boundary(self, boundary_rect: QRect):
        self.__boundary = boundary_rect

    def set_boundary_with_dpi(self, boundary_rect: QRect):
        app: QApplication = getQApplication()

        dpi_factor = app.devicePixelRatio()

        # Windows
        if sys.platform == "win32":
            dpi_factor = 1.0

        new_rect = q_rect_by_factor(boundary_rect, dpi_factor)

        self.boundary = new_rect

    def check_boundary_is_available(self):
        return self.__boundary.width() > 0 and self.__boundary.height() > 0

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
            delta_x = event.position().x() - self.lastPos.x()
            delta_y = event.position().y() - self.lastPos.y()

            if self.resizing:
                # Resize Mode
                # Resize the rectangle within the boundary

                if self.check_boundary_is_available():
                    new_width = min(self.width() + delta_x, self.__boundary.width() - self.x())
                    new_height = min(self.height() + delta_y, self.__boundary.height() - self.y())
                else:
                    new_width = self.width() + delta_x
                    new_height = self.height() + delta_y

                if new_width < self.min_width:
                    new_width = self.min_width

                if new_height < self.min_height:
                    new_height = self.min_height

                self.resize(new_width, new_height)
            else:
                # Move Mode
                # Move the rectangle within the boundary
                new_x = self.x() + delta_x
                new_y = self.y() + delta_y

                if self.check_boundary_is_available():
                    new_x = max(self.__boundary.left(), min(new_x, self.__boundary.right() - self.width()))
                    new_y = max(self.__boundary.top(), min(new_y, self.__boundary.bottom() - self.height()))

                self.move(new_x, new_y)
                # print(
                #     "Boundary:",
                #     self.boundary.top(), self.boundary.bottom(),
                #     self.boundary.left(), self.boundary.right()
                # )

            # Update the last position
            self.lastPos = event.position().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.lastPos = None
            self.resizing = False

            self.ori_x = int(self.x() / self.scale_factor)
            self.ori_y = int(self.y() / self.scale_factor)
            self.ori_w = int(self.width() / self.scale_factor)
            self.ori_h = int(self.height() / self.scale_factor)

            self.modify()

    @property
    def now_x(self) -> int:
        return self.x()

    @now_x.setter
    def now_x(self, value):
        self.ori_x = int(value / self.scale_factor)

        self.update()

    @property
    def now_y(self) -> int:
        return self.y()

    @now_y.setter
    def now_y(self, value):
        self.ori_y = int(value / self.scale_factor)

        self.update()

    @property
    def now_width(self) -> int:
        return self.width()

    @now_width.setter
    def now_width(self, value):
        self.ori_w = int(value / self.scale_factor)

        self.update()

    @property
    def now_height(self) -> int:
        return self.height()

    @now_height.setter
    def now_height(self, value):
        self.ori_h = int(value / self.scale_factor)

        self.update()

    def modify(self) -> None:
        self.slot_resized.emit(self)

        # print("Modified!")
        self.__modified = True
        self.slot_modified.emit(self)

    def is_modified(self) -> bool:
        return self.__modified

    def __str__(self):
        return f"{self.label} {self.ori_x}, {self.ori_y}, {self.ori_w}, {self.ori_h}"

    @property
    def scale_factor(self) -> float:
        return self.__scale_factor

    @scale_factor.setter
    def scale_factor(self, value: float):
        self.__scale_factor = value

        self.update()

    @property
    def x1_original(self) -> int:
        return self.ori_x

    @x1_original.setter
    def x1_original(self, value: int):
        self.ori_x = value

        self.update()

    @property
    def y1_original(self) -> int:
        return self.ori_y

    @y1_original.setter
    def y1_original(self, value: int):
        self.ori_y = value

        self.update()

    @property
    def width_original(self) -> int:
        return self.ori_w

    @width_original.setter
    def width_original(self, value: int):
        self.ori_w = value

        self.update()

    @property
    def height_original(self) -> int:
        return self.ori_h

    @height_original.setter
    def height_original(self, value: int):
        self.ori_h = value

        self.update()

    @property
    def x2_original(self) -> int:
        return self.ori_x + self.ori_w

    @property
    def y2_original(self) -> int:
        return self.ori_y + self.ori_h

    @property
    def center_x(self) -> int:
        return self.now_x + self.now_width // 2

    @center_x.setter
    def center_x(self, value: int):
        self.now_x = value - self.now_width // 2

    @property
    def center_y(self) -> int:
        return self.now_y + self.now_height // 2

    @center_y.setter
    def center_y(self, value: int):
        self.now_y = value - self.now_height // 2

    @property
    def center_x_original(self) -> int:
        return self.ori_x + self.ori_w // 2

    @center_x_original.setter
    def center_x_original(self, value: int):
        self.ori_x = value - self.ori_w // 2

        self.update()

    @property
    def center_y_original(self) -> int:
        return self.ori_y + self.ori_h // 2

    @center_y_original.setter
    def center_y_original(self, value: int):
        self.ori_y = value - self.ori_h // 2

        self.update()

    def get_rect_two_point_2dim_array(self):
        return [
            [self.x1_original, self.y1_original],
            [self.x2_original, self.y2_original]
        ]

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
    label = QLabel(parent=window)
    label.setPixmap(QPixmap('../../../../../../Test/00000000.jpg'))

    rect = ResizableRect(parent=label)

    rect.now_x = 4
    rect.now_y = 4
    rect.now_width = 100
    rect.now_height = 100

    rect.border_color = Qt.GlobalColor.blue
    rect.border_width = 8
    rect.fill_color = Qt.GlobalColor.green
    rect.fill_opacity = 0.3

    # Set the boundary for the rectangle
    rect.boundary = QRect(0, 0, 600, 800)

    window.setGeometry(100, 100, 400, 300)
    window.show()

    sys.exit(app.exec())
