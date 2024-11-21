import json
from typing import List, Tuple, Optional
import os

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton
)

from mot_toolkit.dataset.dataset_dir import get_dataset_dir_list
from mot_toolkit.datatype.dataset.dataset_spilt import DatasetSpilt, SpiltType
from mot_toolkit.gui.view.components. \
    window.base_interface_window import BaseWorkInterfaceWindow
from mot_toolkit.gui.view.interface.spilt.components.spilt_list_widget import SpiltListWidget
from mot_toolkit.utils.logs import get_logger

logger = get_logger()


class InterFaceSmooth(BaseWorkInterfaceWindow):
    all_dir: List[str]

    json_dict: dict = {
        "all": {
            "dataset_list": [],
            "path_str_list": []
        },
        "train": {
            "dataset_list": [],
            "path_str_list": []
        },
        "val": {
            "dataset_list": [],
            "path_str_list": []
        },
        "test": {
            "dataset_list": [],
            "path_str_list": []
        },
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
            SpiltListWidget(
                spilt_type=SpiltType.TRAIN,
                parent=self.h_widget
            )
        self.h_layout.addWidget(self.dataset_train_list_widget)

        # Val
        self.dataset_val_list_widget = \
            SpiltListWidget(
                spilt_type=SpiltType.VAL,
                parent=self.h_widget
            )
        self.h_layout.addWidget(self.dataset_val_list_widget)

        # Test
        self.dataset_test_list_widget = \
            SpiltListWidget(
                spilt_type=SpiltType.TEST,
                parent=self.h_widget
            )
        self.h_layout.addWidget(self.dataset_test_list_widget)

        # Other
        self.dataset_other_list_widget = \
            SpiltListWidget(
                spilt_type=SpiltType.NONE,
                parent=self.h_widget
            )
        self.h_layout.addWidget(self.dataset_other_list_widget)

        # Control Button
        self.control_widget = QWidget(parent=self)
        self.control_layout = QHBoxLayout()
        self.control_widget.setLayout(self.control_layout)
        self.v_layout.addWidget(self.control_widget)

        reload_button = QPushButton(
            "Reload",
            parent=self.control_widget
        )
        reload_button.clicked.connect(self.reload)
        self.control_layout.addWidget(reload_button)

        save_button = QPushButton(
            "Save",
            parent=self.control_widget
        )
        save_button.clicked.connect(self.save)
        self.control_layout.addWidget(save_button)

        # Setting
        self.v_layout.addWidget(QLabel("Level:"))
        self.dir_level_lineedit = QLineEdit(parent=self)
        self.dir_level_lineedit.setText("2")
        self.v_layout.addWidget(self.dir_level_lineedit)

    @property
    def settings_json_path(self) -> str:
        path = os.path.join(self.work_directory_path, "settings.json")

        if not os.path.exists(self.work_directory_path):
            try:
                os.makedirs(self.work_directory_path, exist_ok=True)
            except Exception as e:
                logger.error(f"Create Directory Error: {e}")

        return path

    def reload(self):
        self.reload_data()
        self.update_spilt_list_widget()

    def reload_data(self):
        if os.path.exists(self.settings_json_path):
            with open(self.settings_json_path, "r") as f:
                json_dict: dict = json.load(f)

            if len(json_dict.keys()) > 0:
                self.json_dict.update(json_dict)

        dir_level = 2
        try:
            dir_level = int(self.dir_level_lineedit.text())
        except Exception as e:
            logger.error(f"Dir Level Error: {e}")

        dir_list = get_dataset_dir_list(
            dataset_dir_path=self.work_directory_path,
            level=dir_level,
            black_list=["Task"]
        )

        all_dataset_obj_list: List[DatasetSpilt] = []

        for dir_path in dir_list:
            current_obj = DatasetSpilt(
                path=dir_path,
                base_dir_path=self.work_directory_path
            )
            all_dataset_obj_list.append(current_obj)

        train_str_list = []
        val_str_list = []
        test_str_list = []
        try:
            if "train" in self.json_dict.keys():
                if "path_str_list" in self.json_dict["train"].keys():
                    train_str_list = self.json_dict["train"]["path_str_list"]
            if "val" in self.json_dict.keys():
                if "path_str_list" in self.json_dict["val"].keys():
                    val_str_list = self.json_dict["val"]["path_str_list"]
            if "test" in self.json_dict.keys():
                if "path_str_list" in self.json_dict["test"].keys():
                    test_str_list = self.json_dict["test"]["path_str_list"]
        except Exception as e:
            logger.error(f"Load Dict Spilt Error: {e}")

        all_path_str_list: List[str] = []
        for dataset_obj in all_dataset_obj_list:
            rel_path = dataset_obj.rel_path

            all_path_str_list.append(rel_path)

            if rel_path in train_str_list:
                dataset_obj.spilt_type = SpiltType.TRAIN
            elif rel_path in val_str_list:
                dataset_obj.spilt_type = SpiltType.VAL
            elif rel_path in test_str_list:
                dataset_obj.spilt_type = SpiltType.TEST

        new_dict = {
            "all": {
                "path_str_list": all_path_str_list
            }
        }
        self.json_dict.update(new_dict)

        self.dataset_dir_list.clear()
        self.dataset_dir_list.extend(all_dataset_obj_list)

    def __get_spilt_dict(
            self,
            dataset_obj_list: List[DatasetSpilt]
    ) -> dict:
        final_dict: dict = {
            "dataset_list": [],
            "path_str_list": []
        }

        dataset_dict_list: List[dict] = []
        rel_path_str_list: List[str] = []

        for dataset_obj in dataset_obj_list:
            if dataset_obj.is_valid():
                dataset_dict_list.append(dataset_obj.to_dict())
                rel_path_str_list.append(dataset_obj.rel_path)

        final_dict["dataset_list"] = dataset_dict_list
        final_dict["path_str_list"] = rel_path_str_list

        return final_dict

    def __get_spilt_list(
            self,
            dataset_dir_list: Optional[List[DatasetSpilt]] = None
    ) -> Tuple[
        List[DatasetSpilt],
        List[DatasetSpilt],
        List[DatasetSpilt],
        List[DatasetSpilt]
    ]:
        if dataset_dir_list is None:
            dataset_dir_list = self.dataset_dir_list

        dataset_obj_list_train: List[DatasetSpilt] = []
        dataset_obj_list_val: List[DatasetSpilt] = []
        dataset_obj_list_test: List[DatasetSpilt] = []
        dataset_obj_list_other: List[DatasetSpilt] = []

        for dataset_obj in dataset_dir_list:
            if dataset_obj.spilt_type == SpiltType.TRAIN:
                dataset_obj_list_train.append(dataset_obj)
            elif dataset_obj.spilt_type == SpiltType.VAL:
                dataset_obj_list_val.append(dataset_obj)
            elif dataset_obj.spilt_type == SpiltType.TEST:
                dataset_obj_list_test.append(dataset_obj)
            else:
                dataset_obj_list_other.append(dataset_obj)

        return (
            dataset_obj_list_train,
            dataset_obj_list_val,
            dataset_obj_list_test,
            dataset_obj_list_other
        )

    def save(self):
        (
            dataset_obj_list_train,
            dataset_obj_list_val,
            dataset_obj_list_test,
            _
        ) = self.__get_spilt_list()

        train_dict = self.__get_spilt_dict(dataset_obj_list_train)
        val_dict = self.__get_spilt_dict(dataset_obj_list_val)
        test_dict = self.__get_spilt_dict(dataset_obj_list_test)

        self.json_dict["train"].update(train_dict)
        self.json_dict["val"].update(val_dict)
        self.json_dict["test"].update(test_dict)

    def __update_list_widget_with_list(
            self,
            list_widget: SpiltListWidget,
            dataset_obj_list: List[DatasetSpilt],
    ):
        selection_text = list_widget.selection_text
        list_widget.list_widget.clear()

        for dataset_obj in dataset_obj_list:
            text = dataset_obj.rel_path
            list_widget.list_widget.addItem(text)

        list_widget.try_to_select_text(selection_text)

    def update_spilt_list_widget(self):
        (
            dataset_obj_list_train,
            dataset_obj_list_val,
            dataset_obj_list_test,
            dataset_obj_list_other
        ) = self.__get_spilt_list()

        self.__update_list_widget_with_list(
            list_widget=self.dataset_train_list_widget,
            dataset_obj_list=dataset_obj_list_train
        )
        self.__update_list_widget_with_list(
            list_widget=self.dataset_val_list_widget,
            dataset_obj_list=dataset_obj_list_val
        )
        self.__update_list_widget_with_list(
            list_widget=self.dataset_test_list_widget,
            dataset_obj_list=dataset_obj_list_test
        )
        self.__update_list_widget_with_list(
            list_widget=self.dataset_other_list_widget,
            dataset_obj_list=dataset_obj_list_other
        )


if __name__ == "__main__":
    app = QApplication([])

    window = InterFaceSmooth(r"/mnt/h/Datasets/TrackShipOnlineVideo/LabelMe")
    window.show()

    app.exec()
