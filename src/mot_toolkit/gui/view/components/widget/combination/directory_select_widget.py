from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
from PySide6.QtCore import Slot


class DirectorySelectWidget(QWidget):
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)

        if not title:
            title = "Select Directory"

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
        self.button.clicked.connect(self.select_directory)

    @Slot()
    def select_directory(self):
        # 打开文件对话框，选择目录
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            # 如果选择了目录，则更新文本框内容
            self.text_edit.setText(directory)

    # Getter for the directory path
    def get_directory_path(self) -> str:
        """
        Get the current directory path from the text edit.

        :return: str, the current directory path.
        """
        return self.text_edit.text()

    # Setter for the directory path
    def set_directory_path(self, directory_path: str):
        """
        Set the directory path in the text edit.

        :param directory_path: str, the directory path to set.
        """
        self.text_edit.setText(directory_path)

    @property
    def directory_path(self) -> str:
        return self.get_directory_path()

    @directory_path.setter
    def directory_path(self, directory_path: str):
        self.set_directory_path(directory_path)


# 示例：创建应用程序并显示窗口
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    widget = DirectorySelectWidget()

    widget.directory_path = r"C:\\"

    widget.show()

    # 运行应用程序主循环
    sys.exit(app.exec())
