import os.path
import sys
from typing import Optional

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow, QWidget,
    QVBoxLayout, QPushButton, QLabel,
)

from gui.view.interface.multi_level.interface_multi_level import InterfaceMultiLevel
from mot_toolkit.gui.common.system_wide_menu import (
    init_system_menu
)

from mot_toolkit.gui.view.components.select_directory_path import (
    SelectDirectoryPathWidget
)
from mot_toolkit.gui.view.interface. \
    frame.interface_frame import InterfaceFrame
from mot_toolkit.gui.view.interface. \
    frame.preview.interface_preview import InterFacePreview
from mot_toolkit.gui.view.interface. \
    statistics.interface_statistics import InterfaceStatistics

from mot_toolkit.utils.system_info import is_macos

# Load Program Resources
from mot_toolkit.gui.resources import resources


class MainWindow(QMainWindow):
    __select_directory_path_widget: Optional[
        SelectDirectoryPathWidget
    ] = None

    def __init__(self):
        super().__init__()

        self.__setup_window_properties()

        self.__init_widgets()

    def __setup_window_properties(self):
        # Set Title
        self.setWindowTitle("MOT-Tools Author:Haomin Kong")

        # Set Logo
        self.setWindowIcon(QIcon(":/general/logo"))

        current_menubar = None

        if not is_macos():
            current_menubar = self.menuBar()

        init_system_menu(
            parent=self,
            current_menubar=current_menubar
        )

    def __init_widgets(self):
        self.central_widget = QWidget(parent=self)
        self.setCentralWidget(self.central_widget)
        self.v_layout = QVBoxLayout()
        self.central_widget.setLayout(self.v_layout)

        self.__select_directory_path_widget = SelectDirectoryPathWidget()
        default_path = "./Test"
        if not os.path.isdir(default_path):
            default_path = ""
        self.__select_directory_path_widget.path_line_edit.setText(default_path)
        self.v_layout.addWidget(self.__select_directory_path_widget)

        self.__button_interface_multi_level = QPushButton(parent=self)
        self.__button_interface_multi_level.setText("Multi Level Finder")
        self.__button_interface_multi_level.clicked.connect(self.__button_interface_multi_level_clicked)
        self.v_layout.addWidget(self.__button_interface_multi_level)

        self.__button_stats = QPushButton(parent=self)
        self.__button_stats.setText("Statistics")
        self.__button_stats.clicked.connect(self.__button_stats_clicked)
        self.v_layout.addWidget(self.__button_stats)

        self.__button_preview = QPushButton(parent=self)
        self.__button_preview.setText("Preview")
        self.__button_preview.clicked.connect(self.__button_preview_clicked)
        self.v_layout.addWidget(self.__button_preview)

        self.__button_frame_operation = QPushButton(parent=self)
        self.__button_frame_operation.setText("Frame Operation")
        self.__button_frame_operation.clicked.connect(self.__button_frame_operation_clicked)
        self.v_layout.addWidget(self.__button_frame_operation)

        author_label = QLabel(parent=self)
        author_label.setText("Author:Haomin Kong")
        self.v_layout.addWidget(author_label)

    def __button_interface_multi_level_clicked(self):
        self.interface_multi_level = InterfaceMultiLevel(
            work_directory_path=self.__select_directory_path_widget.get_absolute_path()
        )
        self.interface_multi_level.show()

    def __button_stats_clicked(self):
        self.interface_statistics = InterfaceStatistics(
            work_directory_path=self.__select_directory_path_widget.get_absolute_path()
        )
        self.interface_statistics.show()

    def __button_preview_clicked(self):
        self.interface_preview = InterFacePreview(
            work_directory_path=self.__select_directory_path_widget.get_absolute_path()
        )
        self.interface_preview.show()

    def __button_frame_operation_clicked(self):
        self.interface_frame = InterfaceFrame(
            work_directory_path=self.__select_directory_path_widget.get_absolute_path()
        )
        self.interface_frame.show()


def init_main_window():
    app = QApplication(sys.argv)

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    init_main_window()
