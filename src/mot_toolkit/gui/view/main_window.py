import os.path
import sys
from typing import Optional

from mot_toolkit.gui.view.components.widget. \
    basic.link_label import LinkLabel
from mot_toolkit.utils.logs import get_logger

logger = get_logger()

logger.info("mot-toolkit")

from mot_toolkit.utils.system.system import SystemType
from mot_toolkit.utils.system.linux.system import is_linux
from mot_toolkit.utils.system.linux.display import LinuxWindowSystem

system_type = SystemType.get_system_type()
logger.info(f"System Platform: {system_type.value}")
if is_linux():
    window_system = LinuxWindowSystem.detect()
    logger.info(f"Linux Graphic System: {window_system.value}")

logger.info(f"Python " + sys.version)

logger.info("Start To Load MainWindow Package")

logger.info("Start To Load PySide6")
from PySide6 import __version__ as PySide6Version
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow, QWidget,
    QVBoxLayout, QPushButton, QLabel,
)

logger.info(f"PySide6({PySide6Version}) Load Success")

from mot_toolkit.gui.common.system_wide_menu import (
    init_system_menu, get_system_menu
)

from mot_toolkit.gui.view.components.widget.combination.select_directory_path import (
    SelectDirectoryPathWidget
)

from mot_toolkit.gui.view.interface. \
    multi_level.interface_multi_level import WorkInterfaceMultiLevel
from mot_toolkit.gui.view.interface. \
    preview.interface_preview import InterFacePreview
from mot_toolkit.gui.view.interface. \
    statistics.interface_statistics import WorkInterfaceStatistics
from mot_toolkit.gui.view.interface. \
    smooth.interface_smooth import InterFaceSmooth

from mot_toolkit.utils.system_info import is_macos

# Load Settings
from mot_toolkit.gui.common.global_settings import program_settings

logger.info("Start To Load Qt Resource")

# Load Program Resources

logger.info("Load Qt Resource Success")

from mot_toolkit.gui.resources.resources import qInitResources

qInitResources()

logger.info("Load Package Finished!")


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
        default_path = program_settings.last_work_directory
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
        self.__button_preview.setStyleSheet("color: blue;")
        self.__button_preview.clicked.connect(self.__button_preview_clicked)
        self.v_layout.addWidget(self.__button_preview)

        self.__button_smooth = QPushButton(parent=self)
        self.__button_smooth.setText("Smooth")
        self.__button_smooth.clicked.connect(self.__button_smooth_clicked)
        self.v_layout.addWidget(self.__button_smooth)

        author_label = QLabel(parent=self)
        author_label.setText("Author: Haomin Kong")
        self.v_layout.addWidget(author_label)

        github_link_label = LinkLabel(
            url="https://github.com/a645162/mot-toolkit",
            parent=self
        )
        self.v_layout.addWidget(github_link_label)

        # MenuBar
        system_menu = get_system_menu()
        if system_menu is not None:
            system_menu.file_menu_open_dir.triggered.connect(
                lambda _: self.__select_directory_path_widget.open_dir_select_dialog()
            )

    def __button_interface_multi_level_clicked(self):
        path = self.__select_directory_path_widget.get_absolute_path()
        program_settings.last_work_directory = path

        self.interface_multi_level = WorkInterfaceMultiLevel(
            work_directory_path=path,
            parent=self
        )
        self.interface_multi_level.show()

    def __button_stats_clicked(self):
        path = self.__select_directory_path_widget.get_absolute_path()
        program_settings.last_work_directory = path

        self.interface_statistics = WorkInterfaceStatistics(
            work_directory_path=path
        )
        self.interface_statistics.show()

    def __button_preview_clicked(self):
        path = self.__select_directory_path_widget.get_absolute_path()
        program_settings.last_work_directory = path

        self.interface_preview = InterFacePreview(
            work_directory_path=path,
            parent=self
        )
        self.interface_preview.show()

    def __button_smooth_clicked(self):
        path = self.__select_directory_path_widget.get_absolute_path()
        program_settings.last_work_directory = path

        self.interface_smooth = InterFaceSmooth(
            work_directory_path=path
        )
        self.interface_smooth.show()


def init_main_window():
    app = QApplication(sys.argv)

    # app.setDesktopFileName("mot-toolkit")

    dpi_ratio = app.devicePixelRatio()
    logger.info(f"The current DPI ratio is: {dpi_ratio}")

    program_settings.load()

    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    init_main_window()
