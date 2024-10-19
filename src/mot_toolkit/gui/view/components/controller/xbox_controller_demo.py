import sys
from PySide6.QtWidgets import QApplication, QWidget, QGridLayout
from PySide6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QLabel
)

from mot_toolkit.gui.view.components.controller.widget.xbox_demo_button import XBoxDemoButton
from mot_toolkit.gui.view.components.controller.widget.xbox_demo_color_button import XBoxDemoColorButton
from mot_toolkit.gui.view.components.controller.widget.xbox_demo_direction import XBoxDemoDirection
from mot_toolkit.gui.view.components.controller.widget.xbox_demo_joystick import XBoxDemoJoystick
from mot_toolkit.gui.view.components.controller.widget.xbox_demo_trigger import XBoxDemoTrigger
from mot_toolkit.gui.view.components.controller.xbox_controller import XboxController


class XboxControllerDemoMainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Xbox Controller")

        self.__init_base_ui()

    def __init_base_ui(self):
        self.widget = QWidget(parent=self)
        self.setCentralWidget(self.widget)
        self.layout = QVBoxLayout()
        self.widget.setLayout(self.layout)

        self.layout.addWidget(QLabel("Hello World!"))

        self.button_vibration = XBoxDemoColorButton(text="Vibration")
        self.layout.addWidget(self.button_vibration)

        self.grid_widget = QWidget(parent=self.widget)
        self.grid_layout = QGridLayout()
        self.grid_widget.setLayout(self.grid_layout)
        self.layout.addWidget(self.grid_widget)

        self.controller = XboxController()
        self.controller.debug_mode = True

        self.__init_widget()

    def __init_widget(self):
        self.controller_lt = XBoxDemoTrigger()
        self.controller_rt = XBoxDemoTrigger()

        self.controller_lb = XBoxDemoColorButton(
            text="LB",
            parent=self.grid_widget
        )
        self.controller_rb = XBoxDemoColorButton(
            text="RB",
            parent=self.grid_widget
        )

        self.controller_left_stick = XBoxDemoJoystick()
        self.controller_right_stick = XBoxDemoJoystick()

        self.controller_back = XBoxDemoColorButton(
            text="Back",
            parent=self.grid_widget
        )
        self.controller_start = XBoxDemoColorButton(
            text="Start",
            parent=self.grid_widget
        )

        self.controller_direction = XBoxDemoDirection()
        self.controller_button = XBoxDemoButton()

        self.grid_layout.addWidget(self.controller_lt, 0, 0)
        self.grid_layout.addWidget(self.controller_rt, 0, 3)

        self.grid_layout.addWidget(self.controller_lb, 1, 0)
        self.grid_layout.addWidget(self.controller_rb, 1, 3)

        self.grid_layout.addWidget(self.controller_left_stick, 2, 0)
        self.grid_layout.addWidget(self.controller_back, 2, 1)
        self.grid_layout.addWidget(self.controller_start, 2, 2)
        self.grid_layout.addWidget(self.controller_button, 2, 3)

        self.grid_layout.addWidget(self.controller_direction, 3, 1)
        self.grid_layout.addWidget(self.controller_right_stick, 3, 2)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    main_window = XboxControllerDemoMainWindow()
    main_window.show()

    sys.exit(app.exec())
