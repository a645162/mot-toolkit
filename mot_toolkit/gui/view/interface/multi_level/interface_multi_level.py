import os.path

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton, QSizePolicy
)

from gui.view.components. \
    base_interface_window import BaseInterfaceWindow
from gui.view.interface.multi_level. \
    components.multi_level_finder_widget import MultiLevelFinderWidget

from gui.view.interface. \
    frame.preview.interface_preview import InterFacePreview
from gui.view.interface. \
    statistics.interface_statistics import InterfaceStatistics


class InterfaceMultiLevel(BaseInterfaceWindow):
    base_title = "Multi Level Finder"

    def __init__(self, work_directory_path: str):
        super().__init__(work_directory_path=work_directory_path)

        self.__setup_window_properties()

        self.__init_widgets()

        self.update()

    def __setup_window_properties(self):
        self.setWindowTitle(self.base_title)
        self.setMinimumSize(640, 320)

    def __init_widgets(self):
        self.multi_level_finder = \
            MultiLevelFinderWidget(
                work_directory_path=self.work_directory_path,
                parent=self
            )
        self.multi_level_finder.list_widget_max_width = 300
        self.multi_level_finder.label_title.setVisible(True)
        self.multi_level_finder.label_current_path.setVisible(True)
        self.multi_level_finder.slot_path_changed.connect(
            self.__finder_path_changed
        )
        self.v_layout.addWidget(self.multi_level_finder)

        self.toolbox_container = QWidget(parent=self)
        self.toolbox_layout = QHBoxLayout()
        self.toolbox_container.setLayout(self.toolbox_layout)
        self.v_layout.addWidget(self.toolbox_container)

        self.btn_toolbox_preview = QPushButton(parent=self)
        self.btn_toolbox_preview.setText("Preview")
        self.btn_toolbox_preview.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Minimum
        )
        self.btn_toolbox_preview.clicked.connect(self.__btn_toolbox_preview_clicked)
        self.toolbox_layout.addWidget(self.btn_toolbox_preview)

        self.btn_toolbox_statistics = QPushButton(parent=self)
        self.btn_toolbox_statistics.setText("Statistics")
        self.btn_toolbox_statistics.setVisible(False)
        self.btn_toolbox_statistics.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Minimum
        )
        self.btn_toolbox_statistics.clicked.connect(self.__btn_toolbox_statistics_clicked)
        self.toolbox_layout.addWidget(self.btn_toolbox_statistics)

        self.toolbox_layout.addStretch()

    def update(self):
        super().update()

        if len(self.work_directory_path) > 0:
            self.setWindowTitle(self.base_title + " - " + self.work_directory_path)
        else:
            self.setWindowTitle(self.base_title)

    def __finder_path_changed(self, path: str):
        # is_dir = os.path.isdir(path)

        dir_path = self.multi_level_finder.get_dir()
        is_dir = len(dir_path) > 0

        self.btn_toolbox_preview.setEnabled(is_dir)
        self.btn_toolbox_statistics.setEnabled(is_dir)

    def __btn_toolbox_preview_clicked(self):
        path = self.multi_level_finder.get_dir()

        path = os.path.abspath(path)

        interface_preview = InterFacePreview(
            work_directory_path=path
        )
        interface_preview.show()

    def __btn_toolbox_statistics_clicked(self):
        path = self.multi_level_finder.get_dir()

        path = os.path.abspath(path)

        interface_statistics = InterfaceStatistics(
            work_directory_path=path
        )
        interface_statistics.show()
