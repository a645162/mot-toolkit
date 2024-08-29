from typing import List

from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor
from PySide6.QtWidgets import QTreeView, QWidget, QHBoxLayout, QAbstractItemView, QPushButton, QPlainTextEdit

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

    invalid_background_color: QColor

    def __init__(self, work_directory_path: str):
        super().__init__(work_directory_path)
        logger.info(f"Smooth Work Directory: {work_directory_path}")

        self.annotation_directory = \
            XAnyLabelingAnnotationDirectory()
        self.annotation_directory.slot_modified.connect(
            self.__slot_annotation_directory_modified
        )

        self.__const_value()

        self.__setup_window_properties()
        self.__init_widgets()

        self.load_directory()
        self.__show_tree_model()

    def __const_value(self):
        self.invalid_background_color = QColor(255, 0, 0)

    def __setup_window_properties(self):
        self.basic_window_title = "Smooth Annotations"

        self.setWindowTitle(self.basic_window_title)

    def __init_widgets(self):
        self.h_widget = QWidget(parent=self)
        self.h_layout = QHBoxLayout()
        self.h_widget.setLayout(self.h_layout)

        self.tree_view: QTreeView = QTreeView(parent=self.h_widget)

        # Disable Edit
        self.tree_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.__init_tree_view_menu()

        self.h_layout.addWidget(self.tree_view)

        self.v_layout.addWidget(self.h_widget)

        self.button_start = QPushButton("Start", parent=self.h_widget)
        self.button_start.clicked.connect(self.__slot_button_start_clicked)
        self.v_layout.addWidget(self.button_start)

        self.multi_line_edit = QPlainTextEdit(parent=self.h_widget)
        self.multi_line_edit.setPlaceholderText("Waiting for start...")
        self.multi_line_edit.setReadOnly(True)
        self.v_layout.addWidget(self.multi_line_edit)

    def __init_tree_view_menu(self):
        pass

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
        model.setHorizontalHeaderLabels(["Interval"])

        for index, interval in enumerate(self.interval_obj_list):
            title = interval.group_name.strip()
            if len(title) == 0:
                title = f"Interval {index + 1}"
            parent_item = QStandardItem(title)

            if not interval.is_valid:
                parent_item.setBackground(self.invalid_background_color)

            for file in interval.other_files_list:
                child_item = QStandardItem(file.file_name)

                if file.have_error:
                    child_item.setBackground(self.invalid_background_color)

                parent_item.appendRow(child_item)

            model.appendRow(parent_item)

        self.tree_view.setModel(model)

        self.tree_view.expandAll()

        self.tree_view.show()

    def __slot_annotation_directory_modified(self):
        pass

    def __slot_button_start_clicked(self):
        self.button_start.setEnabled(False)
        self.__callback_add_log("Start smoothing...")

        for interval in self.interval_obj_list:
            interval.check()

        self.__callback_add_log("End smoothing.")
        self.button_start.setEnabled(True)

    def __callback_add_log(self, log):
        self.multi_line_edit.appendPlainText(log)
