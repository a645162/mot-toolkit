import os
from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout, QHBoxLayout,
    QGroupBox,
    QLabel, QLineEdit, QPushButton
)

from mot_toolkit.datatype.dataset.object_classfication import ObjectClassConfigure, ObjectClass
from mot_toolkit.gui.view.components.widget.list.list_with_title_widget import ListWithTitleWidget
from mot_toolkit.gui.view.components.window.base_interface_window import BaseWorkInterfaceWindow
from mot_toolkit.utils.logs import get_logger

logger = get_logger()


class InterFaceClassify(BaseWorkInterfaceWindow):
    __configure_path: str = ""
    class_config: ObjectClassConfigure
    current_object_class: Optional[ObjectClass] = None

    def __init__(self, work_directory_path: str, parent=None):
        super().__init__(work_directory_path, parent=parent)
        logger.info(f"Classify Directory: {work_directory_path}")

        self.__setup_properties()
        self.__init_ui()

        logger.info("Classify Configure Path: " + self.configure_path)
        self.reload()

        logger.info("Classify Interface Initialized")

    def __setup_properties(self):
        # Set Title
        self.setWindowTitle("Spilt Datasets")

    def __init_ui(self):
        self.work_directory_label = \
            QLabel("Work Directory: " + self.work_directory_path)
        self.v_layout.addWidget(self.work_directory_label)

        self.h_widget = QWidget(parent=self)
        self.h_layout = QHBoxLayout()
        self.h_widget.setLayout(self.h_layout)
        self.v_layout.addWidget(self.h_widget)

        # Left Layout
        left_group = QWidget(parent=self)
        left_layout = QVBoxLayout()
        left_group.setLayout(left_layout)
        self.h_layout.addWidget(left_group)

        self.class_list_widget = \
            ListWithTitleWidget(parent=self)
        self.class_list_widget.title = "Class List"
        self.class_list_widget.list_widget.itemSelectionChanged.connect(
            self.__on_class_list_selection_changed
        )
        left_layout.addWidget(self.class_list_widget)

        # ListWidget Control Button
        list_control_widget = QWidget(parent=self)
        list_control_layout = QHBoxLayout()
        list_control_widget.setLayout(list_control_layout)
        left_layout.addWidget(list_control_widget)

        self.add_button = QPushButton("+", parent=self)
        self.add_button.clicked.connect(self.__add_button_clicked)
        list_control_layout.addWidget(self.add_button)

        self.remove_button = QPushButton("-", parent=self)
        self.remove_button.clicked.connect(self.__remove_button_clicked)
        list_control_layout.addWidget(self.remove_button)

        # Right Group
        right_group = QGroupBox("Detail")
        self.h_layout.addWidget(right_group)
        group_layout = QVBoxLayout()
        right_group.setLayout(group_layout)

        group_layout.addWidget(QLabel("ID:"))
        self.detail_id_line_edit = QLineEdit(parent=self)
        group_layout.addWidget(self.detail_id_line_edit)

        group_layout.addWidget(QLabel("Name:"))
        self.detail_name_line_edit = QLineEdit(parent=self)
        group_layout.addWidget(self.detail_name_line_edit)

        group_layout.addStretch()

        apply_button = QPushButton("Apply", parent=self)
        apply_button.clicked.connect(self.__apply_button_clicked)
        group_layout.addWidget(apply_button)

        # Control Button
        control_widget = QWidget(parent=self)
        control_layout = QHBoxLayout()
        control_widget.setLayout(control_layout)
        self.v_layout.addWidget(control_widget)

        self.reload_button = QPushButton("Reload", parent=self)
        self.reload_button.clicked.connect(self.reload)
        control_layout.addWidget(self.reload_button)

        self.save_button = QPushButton("Save", parent=self)
        self.save_button.clicked.connect(self.save)
        control_layout.addWidget(self.save_button)

    def reload(self):
        if not os.path.exists(self.work_directory_path):
            return

        self.class_config = \
            ObjectClassConfigure.create_by_configure_file(self.configure_path)
        if self.class_config is None:
            self.class_config = ObjectClassConfigure()

        self.update()

    @property
    def configure_path(self):
        if self.__configure_path:
            return self.__configure_path

        return os.path.join(
            self.work_directory_path,
            "class_config.json"
        )

    @configure_path.setter
    def configure_path(self, configure_path: str):
        base_name = os.path.basename(configure_path)
        if not base_name.endswith(".json"):
            return

        self.__configure_path = \
            os.path.join(
                self.work_directory_path,
                base_name
            )

    def __apply_button_clicked(self):
        if self.current_object_class is None:
            return

        self.current_object_class.class_id = self.detail_id_line_edit.text()
        self.current_object_class.class_name = self.detail_name_line_edit.text()

        self.update()

    def save(self):
        self.class_config.save_configure_file(self.configure_path)

    def update(self):
        super().update()

        list_widget = self.class_list_widget.list_widget

        def get_item_text(index: int, class_obj: ObjectClass) -> str:
            # 填充2位数
            index_str = str(index + 1).zfill(2)

            return f"[{index_str}] ID: {class_obj.class_id} | Name: {class_obj.class_name}"

        if list_widget.count() != len(self.class_config.object_classes):
            list_widget.clear()

            for i, class_obj in enumerate(self.class_config.object_classes):
                list_widget.addItem(get_item_text(i, class_obj))
        else:
            for i, class_obj in enumerate(self.class_config.object_classes):
                list_widget.item(i).setText(get_item_text(i, class_obj))

        self.class_list_widget.update()

        if self.current_object_class is not None:
            self.detail_id_line_edit.setText(self.current_object_class.class_id)
            self.detail_name_line_edit.setText(self.current_object_class.class_name)

    def __on_class_list_selection_changed(self):
        index = self.class_list_widget.list_widget.selection_index
        if not (-1 < index < len(self.class_config.object_classes)):
            return

        self.current_object_class = self.class_config.object_classes[index]

        self.update()

    def __add_button_clicked(self):
        self.class_config.object_classes.append(
            ObjectClass()
        )

        self.update()

    def __remove_button_clicked(self):
        index = self.class_list_widget.selection_index

        if -1 < index < len(self.class_config.object_classes):
            self.class_config.object_classes.pop(index)

        self.update()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication([])

    window = InterFaceClassify(
        r"/mnt/h/Datasets/TrackShipOnlineVideo/LabelMe",
    )
    window.show()

    app.exec()
