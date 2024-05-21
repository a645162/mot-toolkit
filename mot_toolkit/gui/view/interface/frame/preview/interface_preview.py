from PySide6.QtCore import QSize

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout, QVBoxLayout,
    QLabel,
)

from mot_toolkit.gui.view. \
    components.base_interface_window import BaseInterfaceWindow

from mot_toolkit.gui.view.interface. \
    frame.preview.components.toolkit_widget import ToolkitWidget
from mot_toolkit.gui.view.interface. \
    frame.preview.components.dataset_image_view_widget import DatasetImageView
from mot_toolkit.gui.view.interface. \
    frame.preview.components.file_list_widget import FileListWidget
from mot_toolkit.gui.view.interface. \
    frame.preview.components.object_list_widget import ObjectListWidget


class InterFacePreview(BaseInterfaceWindow):

    def __init__(self, work_directory_path: str):
        super().__init__(work_directory_path)

        self.__setup_window_properties()

        self.__init_widgets()

    def __setup_window_properties(self):
        self.setWindowTitle("Preview Interface")

        # self.setMinimumSize(QSize(640, 320))
        self.setMinimumSize(QSize(800, 600))
        # self.setBaseSize(QSize(800, 600))

    def __init_widgets(self):
        self.label_work_path = QLabel(parent=self)
        self.label_work_path.setText("Work Directory: " + self.work_directory_path)
        self.v_layout.addWidget(self.label_work_path)

        self.main_h_widget = QWidget(parent=self)
        self.main_h_layout = QHBoxLayout()
        self.main_h_widget.setLayout(self.main_h_layout)
        self.v_layout.addWidget(self.main_h_widget)

        self.toolkit_widget = ToolkitWidget(parent=self)
        self.main_h_layout.addWidget(self.toolkit_widget)

        self.main_image_view = DatasetImageView(parent=self)
        self.main_h_layout.addWidget(self.main_image_view)

        self.right_widget = QWidget(parent=self)
        self.right_v_layout = QVBoxLayout()
        self.right_widget.setLayout(self.right_v_layout)

        self.r_file_list_widget = FileListWidget(parent=self)
        self.right_v_layout.addWidget(self.r_file_list_widget)
        self.r_object_list_widget = ObjectListWidget(parent=self)
        self.right_v_layout.addWidget(self.r_object_list_widget)

        # self.right_widget.setFixedWidth(200)
        self.main_h_layout.addWidget(self.right_widget)

        self.main_h_layout.setStretch(0, 0)
        self.main_h_layout.setStretch(1, 4)
        self.main_h_layout.setStretch(2, 1)
