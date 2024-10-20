import sys

from PySide6.QtCore import Qt
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
from mot_toolkit.gui.view.components.controller.gamepad_monitor import (
    GamepadMonitor, GamepadButtonKey,
    GamepadStatusTrigger, GamepadStatusDirection, GamepadStatusJoystick
)


class XboxControllerDemoMainWindow(QMainWindow):
    gamepad_index: int = 0

    def __init__(self, gamepad_index: int = 0, parent=None):
        super().__init__(parent=parent)

        self.gamepad_index = gamepad_index

        self.setWindowTitle("Xbox Controller")

        self.__init_base_ui()

    def __init_base_ui(self):
        self.widget = QWidget(parent=self)
        self.setCentralWidget(self.widget)
        self.layout = QVBoxLayout()
        self.widget.setLayout(self.layout)

        self.label_status = QLabel("Hello World!", parent=self.widget)
        self.layout.addWidget(self.label_status)

        self.button_vibration = XBoxDemoColorButton(text="Vibration")
        self.button_vibration.clicked.connect(self.controller_vibration)
        self.layout.addWidget(self.button_vibration)

        self.grid_widget = QWidget(parent=self.widget)
        self.grid_layout = QGridLayout()
        self.grid_widget.setLayout(self.grid_layout)
        self.layout.addWidget(self.grid_widget)

        self.gamepad_monitor = GamepadMonitor(target_index=self.gamepad_index)
        self.gamepad_monitor.debug_mode = True

        self.__init_widget()

        self.__init_slot()

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
        self.controller_left_stick.point_color = Qt.GlobalColor.red
        self.controller_right_stick = XBoxDemoJoystick()
        self.controller_right_stick.point_color = Qt.GlobalColor.blue

        self.controller_back = XBoxDemoColorButton(
            text="Back",
            parent=self.grid_widget
        )
        self.controller_start = XBoxDemoColorButton(
            text="Start",
            parent=self.grid_widget
        )

        self.controller_logo = XBoxDemoColorButton(
            text="Logo",
            parent=self.grid_widget
        )

        self.controller_direction = XBoxDemoDirection()
        self.controller_button = XBoxDemoButton()

        self.grid_layout.addWidget(self.controller_lt, 0, 0)
        self.grid_layout.addWidget(self.controller_rt, 0, 3)

        self.grid_layout.addWidget(self.controller_lb, 1, 0)
        self.grid_layout.addWidget(self.controller_logo, 1, 1, 1, 2)
        self.grid_layout.addWidget(self.controller_rb, 1, 3)

        self.grid_layout.addWidget(self.controller_left_stick, 2, 0)
        self.grid_layout.addWidget(self.controller_back, 2, 1)
        self.grid_layout.addWidget(self.controller_start, 2, 2)
        self.grid_layout.addWidget(self.controller_button, 2, 3)

        self.grid_layout.addWidget(self.controller_direction, 3, 1)
        self.grid_layout.addWidget(self.controller_right_stick, 3, 2)

    def __init_slot(self):
        self.gamepad_monitor.slot_button_changed.connect(self.on_button_changed)

        self.gamepad_monitor.slot_trigger_left_changed.connect(self.on_trigger_left_changed)
        self.gamepad_monitor.slot_trigger_right_changed.connect(self.on_trigger_right_changed)

        self.gamepad_monitor.slot_joystick_left_changed.connect(self.on_joystick_left_changed)
        self.gamepad_monitor.slot_joystick_right_changed.connect(self.on_joystick_right_changed)

        self.gamepad_monitor.slot_direction_changed.connect(self.on_direction_changed)

        self.gamepad_monitor.slot_status_changed.connect(self.on_status_changed)

    def on_status_changed(self, status):
        self.label_status.setText(status)

    def controller_vibration(self):
        self.gamepad_monitor.vibration(500)

    def on_button_changed(self, button: GamepadButtonKey, is_pressed: bool):
        if button == GamepadButtonKey.LB:
            self.controller_lb.is_pressed = is_pressed
        elif button == GamepadButtonKey.RB:
            self.controller_rb.is_pressed = is_pressed
        elif button == GamepadButtonKey.BACK:
            self.controller_back.is_pressed = is_pressed
        elif button == GamepadButtonKey.START:
            self.controller_start.is_pressed = is_pressed
        elif button == GamepadButtonKey.A:
            self.controller_button.button_a.is_pressed = is_pressed
        elif button == GamepadButtonKey.B:
            self.controller_button.button_b.is_pressed = is_pressed
        elif button == GamepadButtonKey.X:
            self.controller_button.button_x.is_pressed = is_pressed
        elif button == GamepadButtonKey.Y:
            self.controller_button.button_y.is_pressed = is_pressed
        elif button == GamepadButtonKey.LOGO:
            self.controller_logo.is_pressed = is_pressed

    def on_trigger_left_changed(self, status: GamepadStatusTrigger):
        self.controller_lt.value = status.value

    def on_trigger_right_changed(self, status: GamepadStatusTrigger):
        self.controller_rt.value = status.value

    def on_joystick_left_changed(self, status: GamepadStatusJoystick):
        self.controller_left_stick.x = status.x
        self.controller_left_stick.y = status.y

    def on_joystick_right_changed(self, status: GamepadStatusJoystick):
        self.controller_right_stick.x = status.x
        self.controller_right_stick.y = status.y

    def on_direction_changed(self, status: GamepadStatusDirection):
        self.controller_direction.button_top.is_pressed = status.direction_up
        self.controller_direction.button_bottom.is_pressed = status.direction_down
        self.controller_direction.button_left.is_pressed = status.direction_left
        self.controller_direction.button_right.is_pressed = status.direction_right


def main(gamepad_index: int):
    app = QApplication(sys.argv)

    gamepad_windows_1 = XboxControllerDemoMainWindow(gamepad_index=gamepad_index)
    gamepad_windows_1.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    gamepad_count = 1

    if gamepad_count > 1:
        # Multi Process
        from multiprocessing import Process

        processes = []
        for i in range(gamepad_count):
            process = Process(target=main, args=(i,))
            processes.append(process)
            process.start()
    else:
        main(gamepad_index=0)
