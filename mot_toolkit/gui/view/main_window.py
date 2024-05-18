import sys
from typing import Optional

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow
)

from gui.view.components.select_directory_path import SelectDirectoryPathWidget


class MainWindow(QMainWindow):
    __select_directory_path_widget: Optional[
        SelectDirectoryPathWidget
    ] = None

    def __init__(self):
        super().__init__()

        self.__setup_window_properties()

    def __setup_window_properties(self):
        self.setWindowTitle("MOT-Tools")

    def __init_widgets(self):
        self.__select_directory_path_widget = SelectDirectoryPathWidget()


def init_main_window():
    app = QApplication(sys.argv)

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec())
