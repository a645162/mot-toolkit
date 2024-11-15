from PySide6.QtWidgets import (
    QApplication,
    QWidget, QHBoxLayout, QVBoxLayout,
    QDialog, QMessageBox,
    QLabel, QLineEdit, QPushButton,
    QSizePolicy,
)


class DialogInput1Int(QDialog):
    input_value: int = 0
    range: tuple[int, int] | None = None

    def __init__(
            self,
            default_value: int | None = None,
            label: str | None = "Enter an integer:",
            range: tuple[int, int] | None = None,
            min_value: int | None = None,
            max_value: int | None = None,
            title: str | None = "",
            parent=None
    ):
        super().__init__(parent=parent)

        if title is None:
            title = ""

        if min_value is not None and max_value is not None:
            range = (min_value, max_value)

        self.range = range
        self.input_value = default_value

        self.__setup_widget_properties(title=title)
        self.__init_widgets(default_value, label)

    def __setup_widget_properties(self, title: str = ""):
        self.setWindowTitle(title)

    def __init_widgets(self, default_value, label):
        self.main_layout = QVBoxLayout()

        self.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Minimum
        )

        if self.range is not None:
            label += f" ({self.range[0]} - {self.range[1]})"
        self.label = QLabel(label, self)
        self.label.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Minimum
        )
        self.lineEdit = QLineEdit(self)
        self.lineEdit.setText(str(default_value) if default_value is not None else "")
        self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.lineEdit)

        self.control_button_widget = QWidget(parent=self)
        self.control_button_layout = QHBoxLayout()
        self.control_button_widget.setLayout(self.control_button_layout)
        self.main_layout.addWidget(self.control_button_widget)

        self.cancelButton = QPushButton("Cancel", self.control_button_widget)
        self.cancelButton.clicked.connect(self.reject)
        self.control_button_layout.addWidget(self.cancelButton)

        self.okButton = QPushButton("OK", self.control_button_widget)
        self.okButton.setStyleSheet("background-color: red")
        self.okButton.clicked.connect(self.accept)
        self.control_button_layout.addWidget(self.okButton)

        self.setLayout(self.main_layout)

    def accept(self):
        try:
            value = int(self.lineEdit.text())

            if self.range is not None:
                if not self.range[0] <= value <= self.range[1]:
                    QMessageBox.warning(
                        self,
                        "Invalid Input",
                        f"Please enter a valid integer in range {self.range}."
                    )
                    return

            self.input_value = value

            super().accept()
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid integer.")

    def get_integer(self):
        return self.input_value


if __name__ == "__main__":
    app = QApplication([])

    dialog = DialogInput1Int(
        default_value=10,
        label="Enter a number:",
        min_value=0,
        max_value=100,
    )
    if dialog.exec() == QDialog.DialogCode.Accepted:
        value = dialog.get_integer()
        print(f"Input: {value}")

    app.quit()
