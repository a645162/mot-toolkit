import threading

import pygame

from time import sleep as time_sleep

from PySide6.QtCore import Signal, QTimer
from PySide6.QtWidgets import QWidget

interval_input_check = 100


class StatusDirection:
    direction_none: bool = True

    direction_up: bool = False
    direction_down: bool = False
    direction_left: bool = False
    direction_right: bool = False

    def __init__(
            self,
            direction_none: bool = True,
            direction_up: bool = False,
            direction_down: bool = False,
            direction_left: bool = False,
            direction_right: bool = False
    ):
        self.direction_none = direction_none
        self.direction_up = direction_up
        self.direction_down = direction_down
        self.direction_left = direction_left
        self.direction_right = direction_right

    def update_direction_state(self, state: tuple) -> "StatusDirection":
        x, y = state

        self.direction_none = x == 0 and y == 0

        if x == -1:
            self.direction_left = True
            self.direction_right = False
        elif x == 1:
            self.direction_left = False
            self.direction_right = True
        else:
            self.direction_left = False
            self.direction_right = False

        if y == -1:
            self.direction_up = False
            self.direction_down = True
        elif y == 1:
            self.direction_up = True
            self.direction_down = False
        else:
            self.direction_up = False
            self.direction_down = False

        return self

    def __eq__(self, other):
        return (
                self.direction_none == other.direction_none and
                self.direction_up == other.direction_up and
                self.direction_down == other.direction_down and
                self.direction_left == other.direction_left and
                self.direction_right == other.direction_right
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return (
            f"StatusDirection("
            f"direction_none={self.direction_none}, "
            f"direction_up={self.direction_up}, "
            f"direction_down={self.direction_down}, "
            f"direction_left={self.direction_left}, "
            f"direction_right={self.direction_right}"
            f")"
        )

    def is_only_one_direction(self) -> bool:
        return (
                not self.direction_none and
                (
                        self.direction_up or
                        self.direction_down or
                        self.direction_left or
                        self.direction_right
                )
        )

    def get_human_direction(self) -> str:
        if self.direction_none:
            return "无"

        if not self.is_only_one_direction():
            return "组合方向" + self.__str__()

        if self.direction_up:
            return "上"
        if self.direction_down:
            return "下"
        if self.direction_left:
            return "左"
        if self.direction_right:
            return "右"

        return "未知"


class XboxController(QWidget):
    slot_direction_changed: Signal = Signal(StatusDirection)

    status_direction: StatusDirection

    __is_ready: bool = False
    __wait_thread: threading.Thread | None = None

    debug_mode = False

    def __init__(self, auto_work=True, parent=None):
        super().__init__(parent=parent)

        self.__init_properties()

        self.__init_ui()

        self.__init_objects()

        if auto_work:
            self.start_to_init()

    def start_to_init(self):
        if self.__wait_thread is not None:
            return

        # Create a new thread to initialize the controller
        self.__wait_thread = threading.Thread(target=self.__init_controller_thread)
        self.__wait_thread.start()

    def __init_controller_thread(self):
        print("Checking controller...")

        pygame.init()
        pygame.joystick.init()
        device_count = pygame.joystick.get_count()

        if device_count == 0:
            print("Waiting for controller...")

        while device_count == 0:
            self.joystick = None
            self.__is_ready = False

            pygame.joystick.quit()

            time_sleep(1)

            pygame.init()
            pygame.joystick.init()

            device_count = pygame.joystick.get_count()

        if device_count > 1:
            print("Multiple controllers detected. Using the first one.")

        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

        self.__is_ready = True
        # self.__ready_status_changed()
        print(f"Used controller: {self.joystick.get_name()}")

    def __controller_monitor_thread(self):
        # Monitor the controller status
        # Check if the controller is disconnected
        while self.__is_ready:
            if pygame.joystick.get_count() == 0:
                self.joystick = None
                self.__is_ready = False
                # self.__ready_status_changed()

    def __init_properties(self):
        self.setMinimumWidth(0)
        self.setMaximumWidth(0)

        self.setMinimumHeight(0)
        self.setMaximumHeight(0)

    def __init_ui(self):
        pass

    def __init_objects(self):
        self.status_direction = StatusDirection()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.__update_controller_input)
        self.timer.setInterval(interval_input_check)
        self.timer.start(interval_input_check)

    def is_ready(self) -> bool:
        return self.__is_ready

    def __ready_status_changed(self):
        if self.is_ready and not self.timer.isActive():
            self.timer.start(interval_input_check)
        else:
            if self.timer.isActive():
                self.timer.stop()

    @property
    def ready(self) -> bool:
        return self.is_ready()

    def __update_controller_input(self):
        if not self.ready:
            return

        # Handle pygame events
        for event in pygame.event.get():
            if event.type == pygame.JOYAXISMOTION:
                axis = event.axis
                value = event.value
                if self.debug_mode:
                    self.update_state(f"轴 {axis} 值: {value:.2f}")
            elif event.type == pygame.JOYBUTTONDOWN:
                button = event.button
                if self.debug_mode:
                    self.update_state(f"按钮 {button} 被按下")
            elif event.type == pygame.JOYBUTTONUP:
                button = event.button
                if self.debug_mode:
                    self.update_state(f"按钮 {button} 被释放")
            elif event.type == pygame.JOYHATMOTION:
                hat = event.hat
                value = event.value
                self.status_direction.update_direction_state(value)
                if self.debug_mode:
                    self.update_state(f"方向键 {hat} 值: {value}")
                    print(self.status_direction.get_human_direction())
                self.slot_direction_changed.emit(self.status_direction)

    def update_state(self, text):
        print(text)


if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QApplication, QWidget
    from PySide6.QtWidgets import (
        QMainWindow,
        QVBoxLayout,
        QLabel
    )

    app = QApplication(sys.argv)

    main_window = QMainWindow()
    main_window.setWindowTitle("Xbox Controller")
    widget = QWidget()
    main_window.setCentralWidget(widget)
    layout = QVBoxLayout()
    widget.setLayout(layout)

    layout.addWidget(QLabel("Hello World!"))

    controller = XboxController()
    controller.debug_mode = True

    main_window.show()
    sys.exit(app.exec())
