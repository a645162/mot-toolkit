import sys
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout

from mot_toolkit.gui.view.components.controller. \
    widget.xbox_demo_color_button import XBoxDemoColorButton


class XBoxDemoButton(QWidget):
    def __init__(self):
        super().__init__()

        # Create a grid layout
        grid_layout = QGridLayout()

        # Create four buttons
        self.button_a = XBoxDemoColorButton("A")
        self.button_b = XBoxDemoColorButton("B")
        self.button_x = XBoxDemoColorButton("X")
        self.button_y = XBoxDemoColorButton("Y")

        self.button_top = self.button_x
        self.button_bottom = self.button_b
        self.button_left = self.button_y
        self.button_right = self.button_a

        # Add the buttons to the grid layout
        # (0, 1) is the top center position
        # (2, 1) is the bottom center position
        # (1, 0) is the middle left position
        # (1, 2) is the middle right position
        grid_layout.addWidget(self.button_top, 0, 1)
        grid_layout.addWidget(self.button_bottom, 2, 1)
        grid_layout.addWidget(self.button_left, 1, 0)
        grid_layout.addWidget(self.button_right, 1, 2)

        # Set the main layout for the widget
        self.setLayout(grid_layout)

        # Optionally, set a fixed size for the window
        self.setFixedSize(200, 200)  # Set the window size to 200x200 pixels


# Entry point of the application
if __name__ == '__main__':
    # Create an instance of the application
    app = QApplication(sys.argv)

    # Create and show the custom widget
    cross_widget = XBoxDemoButton()
    cross_widget.show()

    # Start the application's event loop and exit when done
    sys.exit(app.exec())
