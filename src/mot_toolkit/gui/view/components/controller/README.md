# Python Game XBox 360 Controller

Device: 北通阿修罗2(Xbox 360 Controller)

## 方向键

右上角为正

- 默认状态`(0, 0)`
- 上`(0, 1)`
- 下`(0, -1)`
- 左`(-1, 0)`
- 右`(1, 0)`

弹起事件为`(0, 0)`，也就是默认状态

## 按键

- START: 7
- BACK: 6
- LOGO: Windows:10, Linux:8

- A: 1
- B: 0
- X: 3
- Y: 2

肩键(LB, RB)为4, 5

## 摇杆

右下角为正

- 左摇杆-横向(x)-axis 0
- 左摇杆-纵向(y)-axis 1

### Windows下的右摇杆

- 右摇杆-横向(x)-axis 2
- 右摇杆-纵向(y)-axis 3

### Linux下的右摇杆

- 右摇杆-横向(x)-axis 3
- 右摇杆-纵向(y)-axis 4

### 左摇杆

- 左: axis 0的值为-1
- 右: axis 0的值为1
- 上: axis 1的值为-1
- 下: axis 1的值为1

### 右摇杆

以Linux为例

- 左: axis 3的值为-1
- 右: axis 3的值为1
- 上: axis 4的值为-1
- 下: axis 4的值为1

## 扳机(LT, RT)

### Windows下的扳机

- 左扳机(LT): axis 4
- 右扳机(RT): axis 5

### Linux下的扳机

- 左扳机(LT): axis 2
- 右扳机(RT): axis 5

弹起为-1，按下为1，数值在[-1, 1]之间变化

### 按下

数值从-1变化到0，再变化到1

### 弹起

数值从1变化到0，再变化到-1

## PySide6 + PyGame

```python
import sys
import pygame
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```
