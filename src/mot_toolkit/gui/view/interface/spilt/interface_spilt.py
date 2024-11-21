from typing import List
import os

from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget, QApplication, QGroupBox

from mot_toolkit.dataset.dataset_dir import get_dataset_dir_list
from mot_toolkit.datatype.dataset.dataset_spilt import DatasetSpilt
from mot_toolkit.gui.view.components.widget.list.list_with_title_widget import ListWithTitleWidget
from mot_toolkit.gui.view.components. \
    window.base_interface_window import BaseWorkInterfaceWindow
from mot_toolkit.utils.logs import get_logger

logger = get_logger()


class InterFaceSmooth(BaseWorkInterfaceWindow):
    all_dir: List[str]
    json_dict: dict = {
        "dataset_list": [

        ]
    }

    dataset_dir_list: List[DatasetSpilt]

    def __init__(self, work_directory_path: str, parent=None):
        super().__init__(work_directory_path, parent=parent)
        logger.info(f"Spilt Work Directory: {work_directory_path}")

        self.all_dir = []
        self.dataset_dir_list = []

        self.__setup_properties()
        self.__init_ui()

    def __setup_properties(self):
        # Set Title
        self.setWindowTitle("Spilt Datasets")

    def __init_ui(self):
        self.work_directory_label = \
            QLabel("Work Directory: " + self.work_directory_path)
        self.v_layout.addWidget(self.work_directory_label)

        self.h_widget = QGroupBox(parent=self)
        self.h_widget.setTitle("Dataset Spilt")
        self.h_layout = QHBoxLayout()
        self.h_widget.setLayout(self.h_layout)
        self.v_layout.addWidget(self.h_widget)

        # Train
        self.dataset_train_list_widget = \
            ListWithTitleWidget(parent=self.h_widget)
        self.dataset_train_list_widget.title = "Train"
        self.h_layout.addWidget(self.dataset_train_list_widget)

        # Val
        self.dataset_val_list_widget = \
            ListWithTitleWidget(parent=self.h_widget)
        self.dataset_val_list_widget.title = "Val"
        self.h_layout.addWidget(self.dataset_val_list_widget)

        # Test
        self.dataset_test_list_widget = \
            ListWithTitleWidget(parent=self.h_widget)
        self.dataset_test_list_widget.title = "Test"
        self.h_layout.addWidget(self.dataset_test_list_widget)

        # Other
        self.dataset_other_list_widget = \
            ListWithTitleWidget(parent=self.h_widget)
        self.dataset_other_list_widget.title = "Other"
        self.h_layout.addWidget(self.dataset_other_list_widget)

    @property
    def settings_json_path(self) -> str:
        path = os.path.join(self.work_directory_path, "settings.json")

        if not os.path.exists(self.work_directory_path):
            try:
                os.makedirs(self.work_directory_path)
            except Exception as e:
                logger.error(f"Create Directory Error: {e}")

        return path

    def reload(self):
        dir_list = get_dataset_dir_list(
            dataset_dir_path=self.work_directory_path,
            black_list=["Task"]
        )


if __name__ == "__main__":
    app = QApplication([])

    window = InterFaceSmooth(r"/mnt/h/Datasets/TrackShipOnlineVideo/LabelMe")
    window.show()

    app.exec()
