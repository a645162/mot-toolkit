import PySide6
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel
)

from mot_toolkit.gui.view.components. \
    base_q_main_window import BaseQMainWindow
from mot_toolkit.gui.view.components. \
    link_label import LinkLabel


class InterFaceAbout(BaseQMainWindow):
    basic_window_title: str = "About"

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__setup_window_properties()

        self.__init_widgets()

    def __setup_window_properties(self):
        self.setWindowTitle(self.basic_window_title)

        # self.setMinimumSize(QSize(640, 320))
        # self.setMinimumSize(QSize(800, 600))
        # self.setBaseSize(QSize(800, 600))

    def add_label(self, text: str) -> QLabel:
        q_label = QLabel(text, parent=self.v_layout_widget)
        self.v_layout.addWidget(q_label)

        return q_label

    def __init_widgets(self):
        self.v_layout_widget = QWidget(parent=self)
        self.v_layout = QVBoxLayout()
        self.v_layout_widget.setLayout(self.v_layout)
        self.setCentralWidget(self.v_layout_widget)

        self.add_label("MOT-Toolkit")
        self.add_label("Multiple Object Tracking Toolkit")

        qt_version = PySide6.__version__
        self.add_label(f"Qt Version: PySide6({qt_version})")

        self.add_label("")
        self.add_label("Author: Haomin Kong")
        self.add_label("2024 Shanghai Maritime University")
        self.add_label("")

        github_link = LinkLabel(
            url="https://github.com/a645162/mot-toolkit",
        )
        self.v_layout.addWidget(github_link)