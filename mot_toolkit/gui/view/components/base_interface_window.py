from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
)

from mot_toolkit.gui.view. \
    components.base_q_main_window import BaseQMainWindow


class BaseInterfaceWindow(BaseQMainWindow):

    def __init__(self, work_directory_path: str):
        super().__init__()

        self.work_directory_path = work_directory_path

        self.__setup_window_properties()

        self.__init_widgets()

    def __setup_window_properties(self):
        self.setWindowTitle("Base Interface Window")

    def __init_widgets(self):
        self.central_widget = QWidget(parent=self)
        self.setCentralWidget(self.central_widget)
        self.v_layout = QVBoxLayout()
        self.v_layout.setSpacing(0)
        self.central_widget.setLayout(self.v_layout)
