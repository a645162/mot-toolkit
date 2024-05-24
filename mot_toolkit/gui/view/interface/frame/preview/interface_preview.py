import os.path

from PySide6.QtCore import QSize

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout, QVBoxLayout,
    QLabel,
)

from mot_toolkit.datatype.xanylabeling import (
    XAnyLabelingAnnotationDirectory,
    XAnyLabelingAnnotation
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
    annotation_directory: XAnyLabelingAnnotationDirectory = \
        XAnyLabelingAnnotationDirectory()

    current_annotation_object: XAnyLabelingAnnotation
    current_file_path: str = ""

    def __init__(self, work_directory_path: str):
        super().__init__(work_directory_path)

        self.__setup_window_properties()

        self.__init_widgets()

        self.__auto_load_directory()

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
        self.r_file_list_widget. \
            list_widget.itemSelectionChanged.connect(self.__file_list_item_selection_changed)
        self.right_v_layout.addWidget(self.r_file_list_widget)

        self.r_object_list_widget = ObjectListWidget(parent=self)
        self.right_v_layout.addWidget(self.r_object_list_widget)

        # self.right_widget.setFixedWidth(200)
        self.main_h_layout.addWidget(self.right_widget)

        self.main_h_layout.setStretch(0, 0)
        self.main_h_layout.setStretch(1, 4)
        self.main_h_layout.setStretch(2, 1)

    def load_directory(self):
        self.annotation_directory.dir_path = self.work_directory_path
        self.annotation_directory.walk_dir()
        self.annotation_directory.sort_path(group_directory=True)
        self.annotation_directory.load_json_files()

        for annotation in self.annotation_directory.annotation_file:
            self.r_file_list_widget.list_widget.addItem(annotation.file_path)

    def __auto_load_directory(self):
        if not os.path.isdir(self.work_directory_path):
            return

        self.load_directory()

    def __file_list_item_selection_changed(self):
        selected_items = self.r_file_list_widget.list_widget.selectedItems()
        if len(selected_items) == 0:
            return

        selected_item = selected_items[0]
        index = self.r_file_list_widget.list_widget.row(selected_item)

        self.current_annotation_object = self.annotation_directory.annotation_file[index]
        self.current_file_path = self.current_annotation_object.file_path

        self.main_image_view.image_view.set_image_by_path(self.current_file_path)

        self.r_object_list_widget.list_widget.clear()
        for rect_item in self.current_annotation_object.rect_annotation_list:
            self.r_object_list_widget.list_widget.addItem(f"{rect_item.label}({rect_item.group_id})")
