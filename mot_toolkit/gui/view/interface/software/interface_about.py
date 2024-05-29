from PySide6.QtWidgets import (
    QWidget
)
from PySide6.QtCore import QSize


class InterFaceAbout(QWidget):
    basic_window_title: str = "About"

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__setup_window_properties()

        self.__init_widgets()

    def __setup_window_properties(self):
        self.setWindowTitle(self.basic_window_title)

        # self.setMinimumSize(QSize(640, 320))
        self.setMinimumSize(QSize(800, 600))
        # self.setBaseSize(QSize(800, 600))

    def __init_widgets(self):
        pass
