import threading
from enum import Enum

import pygame

from time import sleep as time_sleep

from PySide6.QtCore import Signal, QTimer
from PySide6.QtWidgets import QWidget

interval_input_check = 100


class XBoxControllerStatusDirection:
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

    def update_direction_state(self, state: tuple) -> "XBoxControllerStatusDirection":
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

    def is_have_direction(self) -> bool:
        return (
                self.direction_up or
                self.direction_down or
                self.direction_left or
                self.direction_right
        )

    def is_active(self) -> bool:
        return self.is_have_direction()

    def is_only_one_direction(self) -> bool:
        return (not self.direction_none) and self.is_have_direction()

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


class XBoxControllerStatusTrigger:
    __value: float = -1

    def __init__(self):
        pass

    @property
    def value(self) -> float:
        return self.__value

    @value.setter
    def value(self, value: float):
        if value < -1:
            value = -1
        if value > 1:
            value = 1

        self.__value = value

    @property
    def percentage(self) -> float:
        return (self.value + 1) / 2

    @percentage.setter
    def percentage(self, value: float):
        self.value = value * 2 - 1

    def is_pressed(self) -> bool:
        return self.value != -1

    def is_active(self) -> bool:
        return self.is_pressed()


class XBoxControllerStatusButton:
    button_a: bool = False
    button_b: bool = False
    button_x: bool = False
    button_y: bool = False

    button_lb: bool = False
    button_rb: bool = False

    button_lt: bool = False
    button_rt: bool = False

    button_back: bool = False
    button_start: bool = False


class XBoxControllerStatusJoystick:
    __x: float = 0
    __y: float = 0

    # direction_none: bool = True
    #
    # direction_up: bool = False
    # direction_down: bool = False
    # direction_left: bool = False
    # direction_right: bool = False

    def __init__(self):
        pass

    @property
    def x(self) -> float:
        return self.__x

    @x.setter
    def x(self, value: float):
        self.__x = value

    @property
    def y(self) -> float:
        return self.__y

    @y.setter
    def y(self, value: float):
        self.__y = value

    @property
    def direction_up(self) -> bool:
        return self.y < 0

    @property
    def direction_down(self) -> bool:
        return self.y > 0

    @property
    def direction_left(self) -> bool:
        return self.x < 0

    @property
    def direction_right(self) -> bool:
        return self.x > 0

    def is_have_direction(self) -> bool:
        return (
                self.direction_up or
                self.direction_down or
                self.direction_left or
                self.direction_right
        )

    def is_active(self) -> bool:
        return self.is_have_direction()

    @property
    def direction_none(self) -> bool:
        return not self.is_have_direction()


class XBoxButtonKey(Enum):
    A = 1
    B = 0
    X = 3
    Y = 2

    LB = 4
    RB = 5

    LT = 2
    RT = 5

    BACK = 6
    START = 7

    D_UP = 12
    D_DOWN = 13
    D_LEFT = 14
    D_RIGHT = 15

    LEFT_JOYSTICK_X_AXIS = 0
    LEFT_JOYSTICK_Y_AXIS = 1

    RIGHT_JOYSTICK_X_AXIS = 3
    RIGHT_JOYSTICK_Y_AXIS = 4


class XboxController(QWidget):
    slot_direction_changed: Signal = Signal(XBoxControllerStatusDirection)

    slot_trigger_left_changed: Signal = Signal(XBoxControllerStatusTrigger)
    slot_trigger_right_changed: Signal = Signal(XBoxControllerStatusTrigger)

    slot_button_pressed: Signal = Signal(XBoxButtonKey)
    slot_button_released: Signal = Signal(XBoxButtonKey)
    slot_button_triggered: Signal = Signal(XBoxButtonKey)
    slot_button_changed: Signal = Signal(XBoxButtonKey, bool)

    status_direction: XBoxControllerStatusDirection

    status_button: XBoxControllerStatusButton

    status_trigger_left: XBoxControllerStatusTrigger
    status_trigger_right: XBoxControllerStatusTrigger

    status_joystick_left: XBoxControllerStatusJoystick
    status_joystick_right: XBoxControllerStatusJoystick

    joystick: pygame.joystick.Joystick = None

    __timer_monitor: QTimer
    __timer_tick: QTimer
    __tick_time_interval = 1000

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
        self.status_direction = XBoxControllerStatusDirection()

        self.status_button = XBoxControllerStatusButton()
        self.slot_button_changed.connect(self.__slot_button_changed)

        self.status_trigger_left = XBoxControllerStatusTrigger()
        self.status_trigger_right = XBoxControllerStatusTrigger()

        self.status_joystick_left = XBoxControllerStatusJoystick()
        self.status_joystick_right = XBoxControllerStatusJoystick()

        self.__timer_monitor = QTimer(self)
        self.__timer_monitor.timeout.connect(self.__update_controller_input)
        self.__timer_monitor.setInterval(interval_input_check)
        self.__timer_monitor.start(interval_input_check)

        self.__timer_tick = QTimer(self)
        self.__timer_tick.timeout.connect(self.__tick_timer)
        self.__timer_tick.setInterval(self.__tick_time_interval)
        self.__timer_tick.start(self.__tick_time_interval)

    def __slot_button_changed(self, button: XBoxButtonKey, is_pressed: bool):
        if is_pressed:
            self.slot_button_pressed.emit(button)
        else:
            self.slot_button_released.emit(button)
            self.slot_button_triggered.emit(button)

        if button == XBoxButtonKey.A:
            self.status_button.button_a = is_pressed
        elif button == XBoxButtonKey.B:
            self.status_button.button_b = is_pressed
        elif button == XBoxButtonKey.X:
            self.status_button.button_x = is_pressed
        elif button == XBoxButtonKey.Y:
            self.status_button.button_y = is_pressed
        elif button == XBoxButtonKey.LB:
            self.status_button.button_lb = is_pressed
        elif button == XBoxButtonKey.RB:
            self.status_button.button_rb = is_pressed
        elif button == XBoxButtonKey.BACK:
            self.status_button.button_back = is_pressed
        elif button == XBoxButtonKey.START:
            self.status_button.button_start = is_pressed

    def is_ready(self) -> bool:
        return self.__is_ready

    def __ready_status_changed(self):
        if self.is_ready and not self.__timer_monitor.isActive():
            self.__timer_monitor.start(interval_input_check)
        else:
            if self.__timer_monitor.isActive():
                self.__timer_monitor.stop()

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

                # Triggers
                if axis == 2 or axis == 5:
                    # Left Trigger
                    if axis == 2:
                        self.status_trigger_left.value = value
                        self.status_button.button_lt = self.status_trigger_left.is_pressed()
                        self.slot_trigger_left_changed.emit(self.status_trigger_left)

                    # Right Trigger
                    if axis == 5:
                        self.status_trigger_right.value = value
                        self.status_button.button_rt = self.status_trigger_right.is_pressed()
                        self.slot_trigger_right_changed.emit(self.status_trigger_right)

                # Joysticks
                if axis == 0 or axis == 1 or axis == 3 or axis == 4:
                    # Left JoyStick
                    if axis == 0 or axis == 1:
                        if axis == 0:
                            self.status_joystick_left.x = value
                        if axis == 1:
                            self.status_joystick_left.y = value

                    # Right JoyStick
                    if axis == 3 or axis == 4:
                        if axis == 3:
                            self.status_joystick_right.x = value
                        if axis == 4:
                            self.status_joystick_right.y = value

                if self.debug_mode:
                    self.update_state(f"轴 {axis} 值: {value:.2f}")
            elif event.type == pygame.JOYBUTTONDOWN:
                button = event.button

                self.slot_button_changed.emit(XBoxButtonKey(button), True)

                if self.debug_mode:
                    self.update_state(f"按钮 {button} 被按下")
            elif event.type == pygame.JOYBUTTONUP:
                button = event.button

                self.slot_button_changed.emit(XBoxButtonKey(button), False)

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

    @property
    def tick_time_interval(self) -> int:
        return self.__tick_time_interval

    @tick_time_interval.setter
    def tick_time_interval(self, interval: int):
        if interval == self.__tick_time_interval:
            return

        if interval < 0:
            self.__timer_tick.stop()

        self.__tick_time_interval = interval
        self.__timer_tick.setInterval(interval)

        if not self.__timer_tick.isActive():
            self.__timer_tick.start(interval)

    def __tick_timer(self):
        pass


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
