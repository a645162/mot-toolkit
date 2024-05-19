from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout
)


class BaseInterface(QWidget):

    def __init__(self, work_directory_path: str):
        super().__init__()

        self.work_directory_path = work_directory_path

        self.__setup_window_properties()

        self.__init_widgets()

    def __setup_window_properties(self):
        self.setWindowTitle("Base Interface")

    def __init_widgets(self):
        self.v_layout = QVBoxLayout(parent=self)
        self.setLayout(self.v_layout)
