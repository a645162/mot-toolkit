"""
导出SAM任务

Info List:
- Dataset名称/视频名称(一级目录)
- 序列名称(二级目录)

- 任务类型(SAM模型选择)

- 当前帧序号(img文件名)
- 需要操作的目标的Label(ID)

"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel, QPushButton, QMessageBox,
)

from mot_toolkit.gui.view.components.widget.combination.file_save_widget import FileSaveWidget
from mot_toolkit.utils.logs import get_logger

logger = get_logger()


class ExportSamTaskWindow(QDialog):
    def __init__(
            self,
            dataset_name: str,
            sequence_name: str,
            json_name: str,
            target_label: str,
            task_type: str = "FastSAM",
            parent=None,
    ):
        super().__init__(parent)

        self.dataset_name = dataset_name
        self.sequence_name = sequence_name
        self.task_type = task_type
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

        layout.addWidget(QLabel(f"Annotation Json: {self.json_name}"))

        layout.addWidget(QLabel(f"Object Label: {self.target_label}"))

        layout.addWidget(QLabel(f"Task Type: {self.task_type}"))

        self.file_path_widget = FileSaveWidget(
            title="Please select the save path",
            parent=self
        )
        self.file_path_widget.filter = "JSON Files (*.json)"
        layout.addWidget(self.file_path_widget)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_task)
        layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

    def save_task(self):
        save_path = self.file_path_widget.get_file_path()

        if save_path:
            print(f"Save: {save_path}")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Please select a valid save path.")


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    window = ExportSamTaskWindow(
        dataset_name="Dataset1",
        sequence_name="Sequence1",
        json_name="Frame001",
        target_label="Label1",
        task_type="SAM Model 1",
    )
    window.show()

    app.exec()
