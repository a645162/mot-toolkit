from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
from PySide6.QtCore import Slot


class FileSaveWidget(QWidget):
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)

        if not title:
            title = "Select File Save Path"

        # 创建布局
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # 创建标题标签
        self.label = QLabel(title)
        self.main_layout.addWidget(self.label)

        # 创建水平布局以放置文本框和按钮
        self.hbox_layout = QHBoxLayout()

        # 创建文本框
        self.text_edit = QLineEdit()
        self.hbox_layout.addWidget(self.text_edit)

        # 创建按钮
        self.button = QPushButton("...")
        self.button.setFixedWidth(30)  # 设置按钮宽度
        self.hbox_layout.addWidget(self.button)

        # 将水平布局添加到主布局
        self.main_layout.addLayout(self.hbox_layout)

        # 连接按钮点击事件到槽函数
        self.button.clicked.connect(self.select_save_path)

        # 默认的文件过滤器
        self._file_filter = "All Files (*);;Text Files (*.txt)"

    @Slot()
    def select_save_path(self):
        # 打开文件对话框，选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", "", self._file_filter
        )
        if file_path:
            # 如果选择了文件路径，则更新文本框内容
            self.text_edit.setText(file_path)

    # Getter for the file path
    def get_file_path(self) -> str:
        """
        Get the current file path from the text edit.

        :return: str, the current file path.
        """
        return self.text_edit.text()

    # Setter for the file path
    def set_file_path(self, file_path: str):
        """
        Set the file path in the text edit.

        :param file_path: str, the file path to set.
        """
        self.text_edit.setText(file_path)

    # Getter for the file filter
    def get_file_filter(self) -> str:
        """
        Get the current file filter used in the file dialog.

        :return: str, the current file filter.
        """
        return self._file_filter

    # Setter for the file filter
    def set_file_filter(self, file_filter: str):
        """
        Set the file filter to be used in the file dialog.

        :param file_filter: str, the file filter to set.
        """
        self._file_filter = file_filter

    @property
    def file_path(self) -> str:
        return self.get_file_path()

    @file_path.setter
    def file_path(self, file_path: str):
        self.set_file_path(file_path)

    @property
    def filter(self) -> str:
        return self.get_file_filter()

    @filter.setter
    def filter(self, file_filter: str):
        self.set_file_filter(file_filter)


# 示例：创建应用程序并显示窗口
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # 创建并显示自定义窗口
    widget = FileSaveWidget()
    widget.show()

    widget.file_path = "output.mp4"
    widget.filter = "MP4 Video (*.mp4);;AVI Video (*.avi);;All Files (*)"

    # 运行应用程序主循环
    sys.exit(app.exec())
