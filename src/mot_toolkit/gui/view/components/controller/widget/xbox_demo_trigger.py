import sys
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QBrush, QColor


class XBoxDemoTrigger(QWidget):
    __value = -1

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumSize(20, 100)

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        if -1 <= value <= 1:
            self.__value = value
            self.update()  # 触发重绘

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 获取组件大小
        width = self.width()
        height = self.height()

        # 计算进度条的高度
        # 将-1到1映射到0到height
        bar_height = int((self.value + 1) / 2 * height)

        # 绘制背景
        # 背景颜色
        background_brush = QBrush(QColor(200, 200, 200))
        painter.fillRect(QRect(0, 0, width, height), background_brush)

        # 绘制进度
        if bar_height > 0:
            # 进度颜色
            progress_brush = QBrush(QColor(0, 255, 0))
            painter.fillRect(QRect(0, height - bar_height, width, bar_height), progress_brush)


if __name__ == '__main__':
    # 创建应用程序实例
    app = QApplication(sys.argv)

    # 创建并显示进度条
    progress_bar = XBoxDemoTrigger()
    progress_bar.value = 0.5
    progress_bar.show()

    # 运行应用程序
    sys.exit(app.exec())
