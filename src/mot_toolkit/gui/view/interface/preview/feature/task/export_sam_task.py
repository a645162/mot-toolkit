"""
导出SAM任务

Info List:
- Dataset名称/视频名称(一级目录)
- 序列名称(二级目录)

- 任务类型(SAM模型选择)

- 当前帧序号(img文件名)
- 需要操作的目标的Label(ID)

"""

import os
import json

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel, QPushButton, QComboBox, QCheckBox,
    QMessageBox
)

from mot_toolkit.dl.model.sam2 import get_sam_model_list
from mot_toolkit.gui.view.components.widget.combination.file_save_widget import FileSaveWidget
from mot_toolkit.utils.logs import get_logger

logger = get_logger()


class ExportSamTaskWindow(QDialog):
    frame_start = -1
    frame_end = -1

    def __init__(
            self,
            dataset_name: str,
            sequence_name: str,
            json_name: str,
            target_label: str,
            sam_model: str = "FastSAM-x.pt",
            parent=None,
    ):
        super().__init__(parent)

        self.dataset_name = dataset_name
        self.sequence_name = sequence_name
        self.sam_model = sam_model
        self.json_name = json_name
        self.target_label = target_label

        logger.info(f"Export SAM Task Dialog: {dataset_name}/{sequence_name} - {json_name} - {target_label}")

        self.__init_properties()

        self.__init_ui()

    def __init_properties(self):
        self.setWindowTitle("Export SAM Task")

    def __init_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel(f"Dataset Name/Video Name: {self.dataset_name}"))
        layout.addWidget(QLabel(f"Sequence Name: {self.sequence_name}"))

        layout.addWidget(QLabel(f"Annotation Json:"))
        self.line_edit_json_name = QLabel(self.json_name)
        layout.addWidget(self.line_edit_json_name)

        layout.addWidget(QLabel(f"Object Label:"))
        self.line_edit_target_label = QLabel(self.target_label)
        layout.addWidget(self.line_edit_target_label)

        layout.addWidget(QLabel(f"Frame Start:"))
        self.line_edit_frame_start = QLabel(str(self.frame_start))
        layout.addWidget(self.line_edit_frame_start)
        layout.addWidget(QLabel(f"Frame End:"))
        self.line_edit_frame_end = QLabel(str(self.frame_end))
        layout.addWidget(self.line_edit_frame_end)

        # Copy From Previous Frame
        self.checkbox_copy_previous = QCheckBox("Copy From Previous Frame")
        layout.addWidget(self.checkbox_copy_previous)

        self.checkbox_stop_early = QCheckBox("Stop Early")
        layout.addWidget(self.checkbox_stop_early)

        layout.addWidget(QLabel(f"Model Type:"))
        sam_model_list = get_sam_model_list()
        self.model_type_combobox = QComboBox()
        self.model_type_combobox.addItems(sam_model_list)
        layout.addWidget(self.model_type_combobox)
        # Set Current Text
        if self.sam_model in sam_model_list:
            self.model_type_combobox.setCurrentText(self.sam_model)
        else:
            logger.warning(f"Invalid SAM Model Type: {self.sam_model}")
            self.model_type_combobox.setCurrentText(sam_model_list[0])

        self.file_path_widget = FileSaveWidget(
            title="Please select the save path",
            parent=self
        )
        layout.addWidget(self.file_path_widget)
        self.file_path_widget.filter = "JSON Files (*.json)"
        json_name_no_ext = self.json_name.split(".")[0]
        default_file_name = (
            f"{self.dataset_name}"
            f"_{self.sequence_name}"
            f"_{json_name_no_ext}"
            f"_{self.target_label}.json"
        )
        default_path = os.path.join("Output", "task", default_file_name)
        self.file_path_widget.set_file_path(default_path)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.on_click_button_save)
        layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

    def on_click_button_save(self):
        save_path = self.file_path_widget.get_file_path()

        if save_path:
            logger.info(f"Save SAM Task: {save_path}")
            try:
                self.json_name = self.line_edit_json_name.text()
                self.target_label = self.line_edit_target_label.text()
                try:
                    self.frame_start = int(self.line_edit_frame_start.text())
                    self.frame_end = int(self.line_edit_frame_end.text())
                except ValueError:
                    raise ValueError("Frame Start and Frame End must be integers.")

                self.save_config(save_path)

                QMessageBox.information(
                    self, "Success",
                    "Save SAM Task Success.\n" + save_path
                )

                self.accept()
            except Exception as e:
                logger.error(f"Save SAM Task Error: {e}")
                QMessageBox.critical(self, "Error", f"Save SAM Task Error: {e}")
        else:
            QMessageBox.warning(self, "Error", "Please select a valid save path.")

    def save_config(self, save_path: str):
        parent_dir = os.path.dirname(save_path)
        if not os.path.exists(parent_dir):
            logger.info(f"Create Directory: {parent_dir}")
            os.makedirs(parent_dir, exist_ok=True)

        data_dict = {
            "dataset_name": self.dataset_name,
            "sequence_name": self.sequence_name,
            "json_name": self.json_name,
            "start_frame_index": self.frame_start,
            "end_frame_index": self.frame_end,
            "target_label": self.target_label,
            "sam_model": self.model_type_combobox.currentText(),
            "copy_previous": self.checkbox_copy_previous.isChecked(),
            "stop_early": self.checkbox_stop_early.isChecked(),
        }

        json_text = json.dumps(data_dict, indent=4)
        with open(save_path, "w") as f:
            f.write(json_text)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    window = ExportSamTaskWindow(
        dataset_name="Dataset1",
        sequence_name="Sequence1",
        json_name="Frame001",
        target_label="Label1",
    )
    window.show()

    app.exec()
