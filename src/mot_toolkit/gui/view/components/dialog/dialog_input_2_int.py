from PySide6.QtWidgets import (
    QApplication,
    QDialog, QMessageBox,
    QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QSizePolicy,
)


class DialogInput2Int(QDialog):
    input1: int = 0
    input2: int = 0

    range1: tuple[int, int] | None = None
    range2: tuple[int, int] | None = None

    def __init__(
            self,
            default_value1: int | None = None,
            default_value2: int | None = None,
            label1: str | None = "Enter first integer:",
            label2: str | None = "Enter second integer:",
            range1: tuple[int, int] | None = None,
            range2: tuple[int, int] | None = None,
            min_value: int | None = None,
            max_value: int | None = None,
            title: str | None = "",
            parent=None
    ):
        super().__init__(parent=parent)

        if title is None:
            title = ""

        if min_value is not None and max_value is not None:
            range1 = (min_value, max_value)
            range2 = (min_value, max_value)

        self.range1 = range1
        self.range2 = range2

        self.input1 = default_value1
        self.input2 = default_value2

        self.__setup_widget_properties(title=title)
        self.__init_widgets(default_value1, default_value2, label1, label2)

    def __setup_widget_properties(self, title: str = ""):
        # 设置对话框的初始位置和大小
        # self.setGeometry(100, 100, 200, 150)
        self.setWindowTitle(title)

    def __init_widgets(self, default_value1, default_value2, label1, label2):
        self.main_layout = QVBoxLayout()

        self.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Minimum
        )

        self.label1 = QLabel(label1, self)
        self.label1.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Minimum
        )
        self.lineEdit1 = QLineEdit(self)
        self.lineEdit1.setText(str(default_value1) if default_value1 is not None else "")
        self.main_layout.addWidget(self.label1)
        self.main_layout.addWidget(self.lineEdit1)

        self.label2 = QLabel(label2, self)
        self.label2.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Minimum
        )
        self.lineEdit2 = QLineEdit(self)
        self.lineEdit2.setText(str(default_value2) if default_value2 is not None else "")
        self.main_layout.addWidget(self.label2)
        self.main_layout.addWidget(self.lineEdit2)

        self.control_button_widget = QWidget(parent=self)
        self.control_button_layout = QHBoxLayout()
        self.control_button_widget.setLayout(self.control_button_layout)
        self.main_layout.addWidget(self.control_button_widget)

        # 创建取消按钮
        self.cancelButton = QPushButton("Cancel", self.control_button_widget)
        self.cancelButton.clicked.connect(self.reject)
        self.control_button_layout.addWidget(self.cancelButton)

        # 创建确认按钮
        self.okButton = QPushButton("OK", self.control_button_widget)
        # Red color
        self.okButton.setStyleSheet("background-color: red")
        self.okButton.clicked.connect(self.__on_ok_clicked)
        self.control_button_layout.addWidget(self.okButton)

        self.setLayout(self.main_layout)

    def __on_ok_clicked(self):
        # 获取输入框的文本并转换为整数
        try:
            value1 = int(self.lineEdit1.text())
            value2 = int(self.lineEdit2.text())

            if self.range1 is not None:
                if not self.range1[0] <= value1 <= self.range1[1]:
                    QMessageBox.warning(
                        self,
                        "Invalid Input",
                        f"Please enter valid integers in range {self.range1}."
                    )
                    return
            if self.range2 is not None:
                if not self.range2[0] <= value2 <= self.range2[1]:
                    QMessageBox.warning(
                        self,
                        "Invalid Input",
                        f"Please enter valid integers in range {self.range2}."
                    )
                    return

            self.input1 = value1
            self.input2 = value2

            # 关闭对话框，并返回QDialog.Accepted
            self.accept()
        except ValueError:
            # 如果输入不是整数，则弹出错误消息
            QMessageBox.warning(self, "Invalid Input", "Please enter valid integers.")

    def get_integers(self):
        # 返回用户输入的两个整数
        return self.input1, self.input2


if __name__ == "__main__":
    app = QApplication([])
    dialog = DialogInput2Int(
        default_value1=10,
        default_value2=20,
        label1="First number:",
        label2="Second number:",
        min_value=0,
        max_value=100,
    )
    if dialog.exec() == QDialog.DialogCode.Accepted:
        int1, int2 = dialog.get_integers()
        print(f"Input 1: {int1}, Input 2: {int2}")
    app.quit()
