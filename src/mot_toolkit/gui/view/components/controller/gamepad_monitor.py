import platform
import threading
from enum import Enum
from typing import List
import os
import sys

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame

from time import sleep as time_sleep

from PySide6.QtCore import Signal, QTimer
from PySide6.QtWidgets import QWidget

interval_input_check = 100


def get_pygame_version() -> str:
    return pygame.__version__


def get_pygame_version_info() -> str:
    from pygame import ver as pygame_ver
    from pygame import get_sdl_version as pygame_get_sdl_version
    # pylint: disable=consider-using-f-string
    return "pygame {} (SDL {}.{}.{}, Python {}.{}.{})".format(
        pygame_ver, *pygame_get_sdl_version() + sys.version_info[0:3]
    )


class GamepadStatusDirection:
    direction_none: bool = True

    direction_up: bool = False
    direction_down: bool = False
    direction_left: bool = False
    direction_right: bool = False

    __last_state: tuple = (False, False, False, False)

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

    @staticmethod
    def parse_direction_state(state: tuple) -> tuple:
        x, y = state

        if x == -1:
            left = True
            right = False
        elif x == 1:
            left = False
            right = True
        else:
            left = False
            right = False

        if y == -1:
            up = False
            down = True
        elif y == 1:
            up = True
            down = False
        else:
            up = False
            down = False

        return up, down, left, right

    def update_direction_state(self, state: tuple) -> "GamepadStatusDirection":
        self.__last_state = (
            self.direction_up,
            self.direction_down,
            self.direction_left,
            self.direction_right
        )

        (
            self.direction_up,
            self.direction_down,
            self.direction_left,
            self.direction_right
        ) = self.parse_direction_state(state=state)

        self.direction_none = self.is_have_direction()

        return self

    def get_last_direction_state(self) -> tuple:
        return self.__last_state

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


class GamepadStatusTrigger:
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


class GamepadStatusButton:
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
    button_logo: bool = False


class GamepadStatusJoystick:
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


class GamepadButtonKey(Enum):
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

    LOGO = 8

    DIRECTION_UP = 11
    DIRECTION_DOWN = 12
    DIRECTION_LEFT = 13
    DIRECTION_RIGHT = 14

    LEFT_JOYSTICK_X_AXIS = 0
    LEFT_JOYSTICK_Y_AXIS = 1

    RIGHT_JOYSTICK_X_AXIS = 3
    RIGHT_JOYSTICK_Y_AXIS = 4


class GamepadAxisKey():
    LEFT_JOYSTICK_X_AXIS = 0
    LEFT_JOYSTICK_Y_AXIS = 1

    RIGHT_JOYSTICK_X_AXIS: int
    RIGHT_JOYSTICK_Y_AXIS: int

    LEFT_TRIGGER: int
    RIGHT_TRIGGER: int

    @property
    def RIGHT_JOYSTICK_X_AXIS(self):
        if platform.system() == 'Windows':
            return 2

        return 3

    @property
    def RIGHT_JOYSTICK_Y_AXIS(self):
        if platform.system() == 'Windows':
            return 3

        return 4

    @property
    def LEFT_TRIGGER(self):
        if platform.system() == 'Windows':
            return 4

        return 2

    @property
    def RIGHT_TRIGGER(self):
        return 5

    def is_joystick_axis(self, axis: int) -> bool:
        return axis in (
            self.LEFT_JOYSTICK_X_AXIS,
            self.LEFT_JOYSTICK_Y_AXIS,
            self.RIGHT_JOYSTICK_X_AXIS,
            self.RIGHT_JOYSTICK_Y_AXIS
        )

    def is_joystick_left_axis(self, axis: int) -> bool:
        return axis in (
            self.LEFT_JOYSTICK_X_AXIS,
            self.LEFT_JOYSTICK_Y_AXIS
        )

    def is_joystick_right_axis(self, axis: int) -> bool:
        return axis in (
            self.RIGHT_JOYSTICK_X_AXIS,
            self.RIGHT_JOYSTICK_Y_AXIS
        )

    def is_trigger_axis(self, axis: int) -> bool:
        return axis in (
            self.LEFT_TRIGGER,
            self.RIGHT_TRIGGER
        )


class GamepadStatusCode(Enum):
    NONE = 0
    WAITING = 1
    READY = 2
    DISCONNECTED = 3


class GamepadMonitor(QWidget):
    slot_status_changed: Signal = Signal(str)

    slot_direction_changed: Signal = Signal(GamepadStatusDirection)
    slot_direction_pressed: Signal = Signal(list)
    slot_direction_released: Signal = Signal(list)

    slot_trigger_left_changed: Signal = Signal(GamepadStatusTrigger)
    slot_trigger_right_changed: Signal = Signal(GamepadStatusTrigger)

    slot_joystick_left_changed: Signal = Signal(GamepadStatusJoystick)
    slot_joystick_right_changed: Signal = Signal(GamepadStatusJoystick)

    slot_button_pressed: Signal = Signal(GamepadButtonKey)
    slot_button_released: Signal = Signal(GamepadButtonKey)
    slot_button_triggered: Signal = Signal(GamepadButtonKey)
    slot_button_changed: Signal = Signal(GamepadButtonKey, bool)

    status_direction: GamepadStatusDirection

    status_button: GamepadStatusButton

    status_trigger_left: GamepadStatusTrigger
    status_trigger_right: GamepadStatusTrigger

    status_joystick_left: GamepadStatusJoystick
    status_joystick_right: GamepadStatusJoystick

    joystick: pygame.joystick.Joystick = None

    gamepad_index: int = 0
    gamepad_name: str = ""
    status: GamepadStatusCode = GamepadStatusCode.NONE
    status_str = ""

    __timer_monitor: QTimer
    __timer_tick: QTimer
    __tick_time_interval = 1000

    __is_ready: bool = False
    __wait_thread: threading.Thread | None = None
    # Check the controller status (when the controller is disconnected)
    __status_check_thread: threading.Thread | None = None

    __auto_connect: bool = True

    debug_mode = False

    target_index = 0

    def __init__(self, target_index=0, auto_connect=True, parent=None):
        super().__init__(parent=parent)

        self.__init_properties()

        self.__init_ui()

        self.__init_objects()

        if target_index < 0:
            target_index = 0
        self.target_index = target_index
        self.__auto_connect = auto_connect

        if self.__auto_connect:
            self.start_to_init()

    def start_to_init(self):
        if self.__wait_thread is not None:
            return

        # Create a new thread to initialize the controller
        self.__wait_thread = threading.Thread(target=self.__init_controller_thread)
        self.__wait_thread.start()

    def update_status(self, status_str):
        self.status_str = status_str
        print(status_str)
        self.slot_status_changed.emit(status_str)

    def __init_controller_thread(self):
        self.update_status("Checking controller...")

        # try:
        #     pygame.quit()
        #     pygame.joystick.quit()
        # except Exception:
        #     pass

        pygame.init()
        pygame.joystick.init()
        device_count = pygame.joystick.get_count()

        target_index = self.target_index
        target_count = target_index + 1
        if device_count < target_count:
            self.status = GamepadStatusCode.WAITING
            self.update_status(f"Waiting for controller {target_index}...")

        while device_count < target_count:
            self.joystick = None
            self.__is_ready = False

            # pygame.quit()
            pygame.joystick.quit()

            time_sleep(1)

            pygame.init()
            pygame.joystick.init()

            try:
                device_count = pygame.joystick.get_count()
            except Exception:
                device_count = 0

        # if device_count > 1:
        #     self.update_status("Multiple controllers detected. Using the first one.")

        self.joystick = pygame.joystick.Joystick(target_index)
        self.joystick.init()

        self.__is_ready = True

        self.gamepad_index = target_index
        self.gamepad_name = self.joystick.get_name()
        self.status = GamepadStatusCode.READY

        __status_check_thread = threading.Thread(target=self.__controller_monitor_thread)
        __status_check_thread.start()

        self.update_status(f"Used controller: [{self.gamepad_index}] {self.gamepad_name}")

    def __controller_monitor_thread(self):
        # Monitor the controller status
        # Check if the controller is disconnected
        while self.__is_ready:
            time_sleep(1)

            count = self.target_index + 1
            try:
                count = pygame.joystick.get_count()
            except Exception:
                pass

            if count == 0:
                self.joystick = None
                self.__is_ready = False
                self.status = GamepadStatusCode.DISCONNECTED
                self.update_status("Controller disconnected.")

                if self.__auto_connect:
                    self.__wait_thread = None
                    self.start_to_init()

                break

    def __init_properties(self):
        self.setMinimumWidth(0)
        self.setMaximumWidth(0)

        self.setMinimumHeight(0)
        self.setMaximumHeight(0)

    def __init_ui(self):
        pass

    def __init_objects(self):
        self.status_direction = GamepadStatusDirection()
        self.slot_direction_changed.connect(self.__slot_direction_changed)

        self.status_button = GamepadStatusButton()
        self.slot_button_changed.connect(self.__slot_button_changed)

        self.status_trigger_left = GamepadStatusTrigger()
        self.status_trigger_right = GamepadStatusTrigger()

        self.status_joystick_left = GamepadStatusJoystick()
        self.status_joystick_right = GamepadStatusJoystick()

        self.__timer_monitor = QTimer(self)
        self.__timer_monitor.timeout.connect(self.__update_controller_input)
        self.__timer_monitor.setInterval(interval_input_check)
        self.__timer_monitor.start(interval_input_check)

        self.__timer_tick = QTimer(self)
        self.__timer_tick.timeout.connect(self.__tick_timer)
        self.__timer_tick.setInterval(self.__tick_time_interval)
        self.__timer_tick.start(self.__tick_time_interval)

    def __slot_direction_changed(self, direction: GamepadStatusDirection):
        button_list: List[GamepadButtonKey] = list()

        if not direction.is_have_direction():
            up, down, left, right = self.status_direction.get_last_direction_state()
            if up:
                button_list.append(GamepadButtonKey.DIRECTION_UP)
            if down:
                button_list.append(GamepadButtonKey.DIRECTION_DOWN)
            if left:
                button_list.append(GamepadButtonKey.DIRECTION_LEFT)
            if right:
                button_list.append(GamepadButtonKey.DIRECTION_RIGHT)

            self.slot_direction_released.emit(button_list)
            return

        if direction.direction_up:
            button_list.append(GamepadButtonKey.DIRECTION_UP)
        elif direction.direction_down:
            button_list.append(GamepadButtonKey.DIRECTION_DOWN)
        elif direction.direction_left:
            button_list.append(GamepadButtonKey.DIRECTION_LEFT)
        elif direction.direction_right:
            button_list.append(GamepadButtonKey.DIRECTION_RIGHT)
        self.slot_direction_pressed.emit(button_list)

    def __slot_button_changed(self, button: GamepadButtonKey, is_pressed: bool):
        if is_pressed:
            self.slot_button_pressed.emit(button)
        else:
            self.slot_button_released.emit(button)
            self.slot_button_triggered.emit(button)

        if button == GamepadButtonKey.A:
            self.status_button.button_a = is_pressed
        elif button == GamepadButtonKey.B:
            self.status_button.button_b = is_pressed
        elif button == GamepadButtonKey.X:
            self.status_button.button_x = is_pressed
        elif button == GamepadButtonKey.Y:
            self.status_button.button_y = is_pressed
        elif button == GamepadButtonKey.LB:
            self.status_button.button_lb = is_pressed
        elif button == GamepadButtonKey.RB:
            self.status_button.button_rb = is_pressed
        elif button == GamepadButtonKey.BACK:
            self.status_button.button_back = is_pressed
        elif button == GamepadButtonKey.START:
            self.status_button.button_start = is_pressed
        elif button == GamepadButtonKey.LOGO:
            self.status_button.button_logo = is_pressed

    def is_ready(self) -> bool:
        return self.__is_ready

    @property
    def ready(self) -> bool:
        return self.is_ready()

    def __update_controller_input(self):
        if not self.ready:
            return

        event_list = pygame.event.get()

        # for event in event_list:
        #     if event.type == pygame.JOYAXISMOTION:
        #         axis = event.axis
        #         value = event.value
        #         print(f"轴 {axis} 值: {value:.2f}")
        #     elif event.type == pygame.JOYBUTTONDOWN:
        #         button = event.button
        #         print(f"按钮 {button} 被按下")
        #     elif event.type == pygame.JOYBUTTONUP:
        #         button = event.button
        #         print(f"按钮 {button} 被释放")
        #     elif event.type == pygame.JOYHATMOTION:
        #         hat = event.hat
        #         value = event.value
        #         print(f"方向键 {hat} 值: {value}")

        gamepad_axis_key = GamepadAxisKey()

        # Handle pygame events
        for event in event_list:
            if event.type == pygame.JOYAXISMOTION:
                axis = event.axis
                value = event.value

                if self.debug_mode:
                    self.print_state(f"轴 {axis} 值: {value:.2f}")

                # Triggers
                if gamepad_axis_key.is_trigger_axis(axis):
                    # Left Trigger
                    if axis == gamepad_axis_key.LEFT_TRIGGER:
                        self.status_trigger_left.value = value
                        self.status_button.button_lt = self.status_trigger_left.is_pressed()
                        self.slot_trigger_left_changed.emit(self.status_trigger_left)

                    # Right Trigger
                    if axis == gamepad_axis_key.RIGHT_TRIGGER:
                        self.status_trigger_right.value = value
                        self.status_button.button_rt = self.status_trigger_right.is_pressed()
                        self.slot_trigger_right_changed.emit(self.status_trigger_right)

                # Joysticks
                if gamepad_axis_key.is_joystick_axis(axis):
                    # Left JoyStick
                    if gamepad_axis_key.is_joystick_left_axis(axis):
                        if axis == gamepad_axis_key.LEFT_JOYSTICK_X_AXIS:
                            self.status_joystick_left.x = value
                        if axis == gamepad_axis_key.LEFT_JOYSTICK_Y_AXIS:
                            self.status_joystick_left.y = value
                        self.slot_joystick_left_changed.emit(self.status_joystick_left)

                    # Right JoyStick
                    if gamepad_axis_key.is_joystick_right_axis(axis):
                        if axis == gamepad_axis_key.RIGHT_JOYSTICK_X_AXIS:
                            self.status_joystick_right.x = value
                        if axis == gamepad_axis_key.RIGHT_JOYSTICK_Y_AXIS:
                            self.status_joystick_right.y = value
                        self.slot_joystick_right_changed.emit(self.status_joystick_right)
            elif event.type == pygame.JOYBUTTONDOWN:
                button = event.button

                if button == 10 and platform.system() == 'Windows':
                    button = GamepadButtonKey.LOGO

                if self.debug_mode:
                    self.print_state(f"按钮 {button} 被按下")

                self.slot_button_changed.emit(GamepadButtonKey(button), True)
            elif event.type == pygame.JOYBUTTONUP:
                button = event.button

                if self.debug_mode:
                    self.print_state(f"按钮 {button} 被释放")

                self.slot_button_changed.emit(GamepadButtonKey(button), False)
            elif event.type == pygame.JOYHATMOTION:
                hat = event.hat
                value = event.value

                if self.debug_mode:
                    self.print_state(
                        f"方向键 {hat} 值: {value} " +
                        self.status_direction.get_human_direction()
                    )

                self.status_direction.update_direction_state(value)

                self.slot_direction_changed.emit(self.status_direction)

    def print_state(self, text):
        print(text)

    def vibration(
            self,
            duration: int = 500,
            low_frequency: float = 0.5,
            high_frequency: float = 0.5
    ):
        if self.joystick is not None:
            self.joystick.rumble(
                low_frequency=low_frequency,
                high_frequency=high_frequency,
                duration=duration
            )

    def vibration_stop(self):
        if self.joystick is not None:
            self.joystick.rumble(0.0, 0.0, 0)

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

    label_status = QLabel("Hello World!")
    layout.addWidget(label_status)

    gamepad_monitor = GamepadMonitor()
    gamepad_monitor.debug_mode = True
    gamepad_monitor.slot_status_changed.connect(
        lambda status: label_status.setText(status)
    )

    main_window.show()
    sys.exit(app.exec())
