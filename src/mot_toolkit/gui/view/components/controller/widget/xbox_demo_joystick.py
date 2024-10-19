import sys
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtGui import QPainter, QPen, QColor


class XBoxDemoJoystick(QWidget):
    __outline_color = Qt.GlobalColor.black
    __point_color = QColor(0, 0, 255)  # 蓝色

    def __init__(self, parent=None):
        super().__init__(parent)

        # 设置初始位置
        self.__x = 0.0
        self.__y = 0.0

        # 设置固定大小
        self.setFixedSize(200, 200)

        # 设置背景颜色
        self.setStyleSheet("background-color: white;")

    @property
    def outline_color(self):
        return self.__outline_color

    @outline_color.setter
    def outline_color(self, color):
        self.__outline_color = color
        self.update()

    @property
    def point_color(self):
        return self.__point_color

    @point_color.setter
    def point_color(self, color):
        self.__point_color = color
        self.update()

    @property
    def x(self):
        return self.__x

    @x.setter
    def x(self, value):
        # 限制 x 值在 -1 到 1 之间
        if -1 <= value <= 1:
            self.__x = value
            self.update()
        else:
            raise ValueError("x must be between -1 and 1")

    @property
    def y(self):
        return self.__y

    @y.setter
    def y(self, value):
        # 限制 y 值在 -1 到 1 之间
        if -1 <= value <= 1:
            self.__y = value
            self.update()
        else:
            raise ValueError("y must be between -1 and 1")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制外圈
        pen = QPen(self.outline_color)
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawEllipse(QRect(10, 10, 180, 180))

        # 计算圆点的位置
        center = self.rect().center()
        radius = 85  # 圆圈半径的一半减去一些边距
        point_x = int(center.x() + self.__x * radius)
        point_y = int(center.y() + self.__y * radius)

        # 绘制圆点
        painter.setBrush(self.point_color)  # 蓝色
        painter.drawEllipse(QPoint(point_x, point_y), 10, 10)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.update_position(event.position())

    def mouseMoveEvent(self, event):
        self.update_position(event.position())
        self.update()

    def update_position(self, position):
        # 将鼠标位置转换为相对于中心的坐标
        center = self.rect().center()
        x_diff = position.x() - center.x()
        y_diff = position.y() - center.y()

        # 计算距离
        distance = (x_diff ** 2 + y_diff ** 2) ** 0.5
        max_distance = 90  # 最大允许的距离

        if distance > max_distance:
            # 如果超出最大距离，则将位置限制在最大距离上
            scale = max_distance / distance
            x_diff *= scale
            y_diff *= scale

        # 更新 x 和 y 的值
        self.__x = x_diff / max_distance
        self.__y = y_diff / max_distance

        self.update()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    joystick = XBoxDemoJoystick()
    joystick.show()

    sys.exit(app.exec())
