import sys
from typing import Optional

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow, QWidget,
    QVBoxLayout, QPushButton,
)

from mot_toolkit.gui.view.components.select_directory_path import (
    SelectDirectoryPathWidget
)
from mot_toolkit.gui.view.frame.interface_frame import InterfaceFrame
from mot_toolkit.gui.view.statistics.interface_statistics import InterfaceStatistics


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
        self.central_widget = QWidget(parent=self)
        self.setCentralWidget(self.central_widget)
        self.v_layout = QVBoxLayout()
        self.central_widget.setLayout(self.v_layout)

        self.__select_directory_path_widget = SelectDirectoryPathWidget()
        self.v_layout.addWidget(self.__select_directory_path_widget)

        self.__button_stats = QPushButton(parent=self)
        self.__button_stats.setText("Statistics")
        self.__button_stats.clicked.connect(self.__button_stats_clicked)
        self.v_layout.addWidget(self.__button_stats)

        self.__button_frame_operation = QPushButton(parent=self)
        self.__button_frame_operation.setText("Frame Operation")
        self.__button_frame_operation.clicked.connect(self.__button_frame_operation_clicked)
        self.v_layout.addWidget(self.__button_frame_operation)

    def __button_stats_clicked(self):
        self.interfaceStatistics = InterfaceStatistics(
            work_directory_path=self.__select_directory_path_widget.get_path()
        )
        self.interfaceStatistics.show()

    def __button_frame_operation_clicked(self):
        self.interfaceFrame = InterfaceFrame(
            work_directory_path=self.__select_directory_path_widget.get_path()
        )
        self.interfaceFrame.show()


def init_main_window():
    app = QApplication(sys.argv)

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec())
