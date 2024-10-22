from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QScrollArea, QLabel
from PySide6.QtCore import Qt, QPoint


class MyWidget(QWidget):
    def __init__(self):
        super().__init__()

        # 创建一个大标签列表，以便可以滚动
        self.labels = [QLabel(f'Item {i + 1}') for i in range(100)]
        for label in self.labels:
            label.setFixedHeight(50)  # 设置固定高度以便于计算

        # 创建一个 widget 来容纳所有标签
        container = QWidget()
        layout = QVBoxLayout(container)
        for label in self.labels:
            layout.addWidget(label)

        # 创建一个 QScrollArea 并设置其 widget
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(container)
        self.scroll_area.setWidgetResizable(True)

        # 创建一个按钮，点击时显示当前显示的第一个子控件
        self.button = QPushButton("Get First Visible Item")
        self.button.clicked.connect(self.get_first_visible_item)

        # 设置布局
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.scroll_area)
        main_layout.addWidget(self.button)
        self.setLayout(main_layout)

    def get_first_visible_item(self):
        # 获取垂直滚动条的位置
        vertical_pos = self.scroll_area.verticalScrollBar().value()
        print(f"Vertical scroll position: {vertical_pos}")

        # 遍历所有子控件
        for label in self.labels:
            # 计算子控件相对于容器顶部的位置
            pos = label.mapToGlobal(label.pos()).y() - self.scroll_area.viewport().mapToGlobal(QPoint(0, 0)).y()
            if pos >= vertical_pos:
                print(f"First visible item: {label.text()}")
                break
        else:
            print("No items are currently visible.")


if __name__ == "__main__":
    # 创建应用程序
    app = QApplication([])

    # 创建并显示窗口
    widget = MyWidget()
    widget.show()

    # 运行应用程序主循环
    app.exec()
