from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout

from mot_toolkit.gui.view. \
    components.base_interface_window import BaseInterfaceWindow

from mot_toolkit.gui.view.interface. \
    frame.preview.components.dataset_image_view_widget import DatasetImageView
from mot_toolkit.gui.view.interface. \
    frame.preview.components.file_list_widget import FileListWidget
from mot_toolkit.gui.view.interface. \
    frame.preview.components.object_list_widget import ObjectListWidget
from mot_toolkit.gui.view.interface. \
    frame.preview.components.toolkit_widget import ToolkitWidget


class InterFacePreview(BaseInterfaceWindow):

    def __init__(self, work_directory_path: str):
        super().__init__(work_directory_path)

        self.__setup_window_properties()

        self.__init_widgets()

    def __setup_window_properties(self):
        self.setWindowTitle("Preview Interface")

    def __init_widgets(self):
        self.main_h_layout = QHBoxLayout(parent=self)
        self.setLayout(self.main_h_layout)

        self.toolkit_widget = ToolkitWidget(parent=self)
        self.main_h_layout.addWidget(self.toolkit_widget)

        self.main_image_view = DatasetImageView(parent=self)
        self.main_h_layout.addWidget(self.main_image_view)

        self.right_v_layout = QVBoxLayout(parent=self)
        self.main_h_layout.addLayout(self.right_v_layout)

        self.r_file_list_widget = FileListWidget(parent=self)
        self.r_object_list_widget = ObjectListWidget(parent=self)
