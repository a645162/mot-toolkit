import sys
import pygame
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import QTimer


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 初始化 pygame
        pygame.init()
        pygame.joystick.init()

        # 检查是否有连接的手柄
        if pygame.joystick.get_count() == 0:
            self.label = QLabel("没有检测到手柄，请连接Xbox手柄后重试。")
            self.joystick = None
        else:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            self.label = QLabel(f"检测到手柄: {self.joystick.get_name()}")

        # 设置主窗口
        self.setWindowTitle("Xbox 手柄输入示例")
        self.setGeometry(100, 100, 400, 200)

        # 创建布局和标签
        layout = QVBoxLayout()
        layout.addWidget(self.label)

        # 创建震动按钮
        self.rumble_button = QPushButton("使手柄震动")
        self.rumble_button.clicked.connect(self.rumble_controller)
        layout.addWidget(self.rumble_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # 创建定时器以定期检查手柄输入
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_controller_input)
        self.timer.start(100)  # 每100毫秒更新一次

    def update_state(self, text):
        self.label.setText(text)
        print(text)

    def update_controller_input(self):
        # 处理 pygame 事件
        for event in pygame.event.get():
            if event.type == pygame.JOYAXISMOTION:
                axis = event.axis
                value = event.value
                self.update_state(f"轴 {axis} 值: {value:.2f}")
            elif event.type == pygame.JOYBUTTONDOWN:
                button = event.button
                self.update_state(f"按钮 {button} 被按下")
            elif event.type == pygame.JOYBUTTONUP:
                button = event.button
                self.update_state(f"按钮 {button} 被释放")
            elif event.type == pygame.JOYHATMOTION:
                hat = event.hat
                value = event.value
                self.update_state(f"方向键 {hat} 值: {value}")

    def rumble_controller(self):
        if self.joystick is not None:
            # 使手柄震动 0.5 秒
            self.joystick.rumble(0.5, 0.5, 500)
            # 等待一段时间，以便看到震动效果
            QTimer.singleShot(500, self.stop_rumble)

    def stop_rumble(self):
        if self.joystick is not None:
            # 停止震动
            self.joystick.rumble(0.0, 0.0, 0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
