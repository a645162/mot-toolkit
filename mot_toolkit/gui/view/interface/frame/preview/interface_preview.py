from typing import List
import os.path

from PySide6.QtCore import QSize
from PySide6.QtGui import QColor

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
    frame.preview.components.toolbox_widget import ToolboxWidget
from mot_toolkit.gui.view.interface. \
    frame.preview.components.dataset_image_view_widget import DatasetImageView
from mot_toolkit.gui.view.interface. \
    frame.preview.components.file_list_widget import FileListWidget
from mot_toolkit.gui.view.interface. \
    frame.preview.components.object_list_widget import ObjectListWidget


class InterFacePreview(BaseInterfaceWindow):
    annotation_directory: XAnyLabelingAnnotationDirectory = None

    file_str_list: List[str]

    current_annotation_object: XAnyLabelingAnnotation = None
    current_file_path: str = ""

    basic_window_title: str = "Preview Interface"

    def __init__(self, work_directory_path: str):
        super().__init__(work_directory_path)

        self.file_str_list = []

        self.annotation_directory = \
            XAnyLabelingAnnotationDirectory()
        self.annotation_directory.slot_modified.connect(
            self.__slot_annotation_directory_modified
        )

        self.__setup_window_properties()

        self.__init_widgets()

        self.__auto_load_directory()

        self.update()

    def __setup_window_properties(self):
        self.setWindowTitle(self.basic_window_title)

        # self.setMinimumSize(QSize(640, 320))
        self.setMinimumSize(QSize(800, 600))
        # self.setBaseSize(QSize(800, 600))

    def __init_widgets(self):
        self.label_work_path = QLabel(parent=self)
        self.v_layout.addWidget(self.label_work_path)

        self.main_h_widget = QWidget(parent=self)
        self.main_h_layout = QHBoxLayout()
        self.main_h_layout.setSpacing(0)
        self.main_h_widget.setLayout(self.main_h_layout)
        self.v_layout.addWidget(self.main_h_widget)

        self.toolkit_widget = ToolboxWidget(parent=self)
        self.main_h_layout.addWidget(self.toolkit_widget)

        self.main_image_view = DatasetImageView(parent=self)
        self.main_image_view.slot_previous_image.connect(self.__slot_previous_image)
        self.main_image_view.slot_next_image.connect(self.__slot_next_image)
        self.main_image_view.slot_selection_changed.connect(self.__slot_selection_changed)
        self.main_h_layout.addWidget(self.main_image_view)

        self.right_widget = QWidget(parent=self)
        self.right_v_layout = QVBoxLayout()
        self.right_widget.setLayout(self.right_v_layout)

        self.r_file_list_widget = FileListWidget(parent=self)
        self.r_file_list_widget. \
            list_widget.itemSelectionChanged.connect(self.__file_list_item_selection_changed)
        self.right_v_layout.addWidget(self.r_file_list_widget)

        self.r_object_list_widget = ObjectListWidget(parent=self)
        self.r_object_list_widget. \
            list_widget.itemSelectionChanged.connect(self.__object_list_item_selection_changed)
        self.right_v_layout.addWidget(self.r_object_list_widget)

        # self.right_widget.setFixedWidth(200)
        self.main_h_layout.addWidget(self.right_widget)

        self.main_image_view.object_menu = \
            self.r_object_list_widget.list_widget.menu

        self.main_h_layout.setStretch(0, 0)
        self.main_h_layout.setStretch(1, 8)
        self.main_h_layout.setStretch(2, 1)

    def update(self):
        super().update()

        self.setWindowTitle(
            self.basic_window_title + " - " + self.work_directory_path
        )
        self.label_work_path.setText(
            "Work Directory: " + self.work_directory_path
        )

    def load_directory(self):
        self.annotation_directory.dir_path = self.work_directory_path
        self.annotation_directory.walk_dir()
        self.annotation_directory.sort_path(group_directory=True)
        self.annotation_directory.load_json_files()

        directory_list = []
        ext_list = []
        for annotation in self.annotation_directory.annotation_file:
            file_path = annotation.file_path
            directory_path = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[1]
            if (
                    directory_path not in directory_list and
                    os.path.isdir(directory_path)
            ):
                directory_list.append(directory_path)
            if file_ext not in ext_list:
                ext_list.append(file_ext)

        only_file_name = (
                len(directory_list) == 1 and
                len(ext_list) == 1
        )

        for annotation in self.annotation_directory.annotation_file:
            path = annotation.file_path
            if only_file_name:
                path = os.path.basename(path)
                path = os.path.splitext(path)[0]

            self.file_str_list.append(path)
            self.r_file_list_widget.list_widget.addItem(path)

        self.r_file_list_widget.update()

    def __slot_annotation_directory_modified(self):
        self.update_file_list_widget()

    def update_file_list_widget(self):
        annotation_obj_list: List[XAnyLabelingAnnotation] = \
            self.annotation_directory.annotation_file

        for i, current_annotation_obj in enumerate(annotation_obj_list):
            current_item = self.r_file_list_widget.list_widget.item(i)

            base_text = self.file_str_list[i]
            if current_annotation_obj.is_modified:
                current_item.setForeground(QColor(255, 0, 0))
                base_text = f"* {base_text}"
            else:
                current_item.setForeground(QColor(0, 0, 0))

            current_item.setText(base_text)

    def __auto_load_directory(self):
        if not os.path.isdir(self.work_directory_path):
            return

        self.load_directory()

    def __file_list_item_selection_changed(self):
        self.save_current_opened()

        index = self.r_file_list_widget.selection_index

        self.current_annotation_object = \
            self.annotation_directory.annotation_file[index]
        self.current_file_path = self.current_annotation_object.file_path

        self.main_image_view.update_dataset_annotation_path(
            self.current_annotation_object
        )

        self.r_object_list_widget.list_widget.clear()
        for rect_item in self.current_annotation_object.rect_annotation_list:
            self.r_object_list_widget.list_widget.addItem(
                f"{rect_item.label}({rect_item.group_id})"
            )
        self.r_object_list_widget.update()

    def __slot_previous_image(self):
        selection_index = self.r_file_list_widget.selection_index
        selection_index -= 1
        if selection_index < 0:
            return
        self.r_file_list_widget.selection_index = selection_index

    def __slot_next_image(self):
        selection_index = self.r_file_list_widget.selection_index
        selection_index += 1
        if selection_index >= self.r_file_list_widget.count:
            return
        self.r_file_list_widget.selection_index = selection_index

    def __object_list_item_selection_changed(self):
        index = self.r_object_list_widget.selection_index

        self.main_image_view.set_selection_rect_index(index)

    def __slot_selection_changed(self, index):
        self.r_object_list_widget.selection_index = index

    def save_current_opened(self):
        if self.current_annotation_object is not None:
            self.current_annotation_object.save()
