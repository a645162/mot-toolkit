from typing import List

from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtWidgets import QTreeView, QWidget, QHBoxLayout

from mot_toolkit.datatype.xanylabeling \
    import XAnyLabelingAnnotationDirectory
from mot_toolkit.gui.view.interface.smooth. \
    data.smooth_interval import SmoothInterval
from mot_toolkit.gui.view.components. \
    base_interface_window import BaseWorkInterfaceWindow

from mot_toolkit.utils.logs import get_logger

logger = get_logger()


class InterFaceSmooth(BaseWorkInterfaceWindow):
    interval_obj_list: List[SmoothInterval]

    def __init__(self, work_directory_path: str):
        super().__init__(work_directory_path)
        logger.info(f"Smooth Work Directory: {work_directory_path}")

        self.annotation_directory = \
            XAnyLabelingAnnotationDirectory()
        self.annotation_directory.slot_modified.connect(
            self.__slot_annotation_directory_modified
        )

        self.__setup_window_properties()
        self.__init_widgets()

        self.load_directory()
        self.__show_tree_model()

    def __setup_window_properties(self):
        self.basic_window_title = "Smooth Annotations"

        self.setWindowTitle(self.basic_window_title)

    def __init_widgets(self):
        self.h_widget = QWidget(parent=self)
        self.h_layout = QHBoxLayout()
        self.h_widget.setLayout(self.h_layout)

        self.tree_view: QTreeView = QTreeView(parent=self.h_widget)
        self.h_layout.addWidget(self.tree_view)

        self.v_layout.addWidget(self.h_widget)

    def load_directory(self):
        self.annotation_directory.dir_path = self.work_directory_path
        self.annotation_directory.walk_dir()
        self.annotation_directory.sort_path(group_directory=True)
        self.annotation_directory.load_json_files()
        self.annotation_directory.update_label_list()

        self.interval_obj_list = \
            [
                SmoothInterval.from_parent(parent_obj=ori_obj)
                for ori_obj in self.annotation_directory.get_annotation_file_interval_list()
            ]

        logger.info(f"Loaded {len(self.interval_obj_list)} intervals")

    def __show_tree_model(self):
        model = QStandardItemModel()

        for index, interval in enumerate(self.interval_obj_list):
            parent_item = QStandardItem(f"Interval {index + 1}")

            for file in interval.other_files_list:
                child_item = QStandardItem(file.file_name)
                parent_item.appendRow(child_item)

            model.appendRow(parent_item)

        self.tree_view.setModel(model)

        self.tree_view.expandAll()

        self.tree_view.show()

    def __slot_annotation_directory_modified(self):
        pass
