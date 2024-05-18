import sys
from typing import Optional

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow, QWidget,
    QVBoxLayout,
)

from mot_toolkit.gui.view.components.select_directory_path import (
    SelectDirectoryPathWidget
)


class MainWindow(QMainWindow):
    __select_directory_path_widget: Optional[
        SelectDirectoryPathWidget
    ] = None

    def __init__(self):
        super().__init__()

        self.__setup_window_properties()

        self.__init_widgets()

    def __setup_window_properties(self):
        self.setWindowTitle("MOT-Tools")

    def __init_widgets(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.v_layout = QVBoxLayout()

        self.__select_directory_path_widget = SelectDirectoryPathWidget()
        self.v_layout.addWidget(self.__select_directory_path_widget)

        self.central_widget.setLayout(self.v_layout)


def init_main_window():
    app = QApplication(sys.argv)

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec())
