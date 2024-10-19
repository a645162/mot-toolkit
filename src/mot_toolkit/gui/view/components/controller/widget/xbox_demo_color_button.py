from PySide6.QtWidgets import QPushButton


class XBoxDemoColorButton(QPushButton):
    __is_pressed = False

    color_default = "white"
    color_pressed = "red"

    def __init__(self, text="", parent=None):
        super().__init__(parent)

        self.setText(text)

    @property
    def is_pressed(self):
        return self.__is_pressed

    @is_pressed.setter
    def is_pressed(self, value: bool):
        self.__is_pressed = value

        color = self.color_pressed if value else self.color_default
        self.setStyleSheet(f"background-color: {color};")


if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication, QWidget, QGridLayout

    app = QApplication(sys.argv)

    widget = QWidget()
    layout = QGridLayout()
    widget.setLayout(layout)

    button1 = XBoxDemoColorButton("Press me")
    button1.is_pressed = False
    layout.addWidget(button1)

    button2 = XBoxDemoColorButton("Press me")
    button2.is_pressed = True
    layout.addWidget(button2)

    widget.show()

    sys.exit(app.exec())
