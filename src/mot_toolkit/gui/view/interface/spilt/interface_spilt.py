import json
from typing import List, Tuple, Optional
import os

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QSizePolicy,
    QVBoxLayout,
    QMessageBox,
)

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list
from mot_toolkit.datatype.dataset.dataset_spilt import DatasetSpilt, SpiltType
from mot_toolkit.gui.view.components.window.base_interface_window import (
    BaseWorkInterfaceWindow,
)
from mot_toolkit.gui.view.interface.spilt.components.spilt_list_widget import (
    SpiltListWidget,
)
from mot_toolkit.utils.logs import get_logger
from mot_toolkit.utils.statistics.stats_file import stats_file_count

logger = get_logger()


class InterFaceDatasetSpilt(BaseWorkInterfaceWindow):
    all_dir: List[str]

    json_dict: dict = {
        "all": {"dataset_list": [], "path_str_list": []},
        "train": {"dataset_list": [], "path_str_list": []},
        "val": {"dataset_list": [], "path_str_list": []},
        "test": {"dataset_list": [], "path_str_list": []},
    }

    dataset_dir_list: List[DatasetSpilt]

    depth = 1

    __json_file_name: str = "default.spilt.json"

    __last_load_file_name: str = ""

    # 添加源集合和目标集合的映射名称
    __spilt_type_name_map = {
        SpiltType.TRAIN: "Train",
        SpiltType.VAL: "Val",
        SpiltType.TEST: "Test",
        SpiltType.NONE: "Other",
    }

    def __init__(self, work_directory_path: str, parent=None):
        super().__init__(work_directory_path, parent=parent)
        logger.info(f"Spilt Work Directory: {work_directory_path}")

        self.all_dir = []
        self.dataset_dir_list = []

        self.__setup_properties()
        self.__init_ui()

        self.load_json_list()

        logger.info(f"Spilt Configure Path: {self.settings_json_path}")

    def __setup_properties(self):
        # Set Title
        self.setWindowTitle("Spilt Datasets")

    def __init_ui(self):
        self.work_directory_label = QLabel(
            "Work Directory: " + self.work_directory_path
        )
        self.v_layout.addWidget(self.work_directory_label)

        self.select_file_group = QGroupBox("Select File")
        self.select_file_layout = QHBoxLayout()
        self.select_file_group.setLayout(self.select_file_layout)
        self.v_layout.addWidget(self.select_file_group)

        # Combobox
        self.select_file_combobox = QComboBox(parent=self.select_file_group)

        # Allow edit
        self.select_file_combobox.setEditable(True)

        # When combobox value changed
        self.select_file_combobox.currentTextChanged.connect(self.__select_file_changed)

        self.select_file_combobox.setMinimumWidth(300)

        self.select_file_layout.addWidget(self.select_file_combobox)

        # Combobox Refresh Button
        self.select_file_refresh_button = QPushButton(
            "Refresh", parent=self.select_file_group
        )
        self.select_file_refresh_button.clicked.connect(self.load_json_list)
        # SizePolicy Minimum
        self.select_file_refresh_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        )
        self.select_file_layout.addWidget(self.select_file_refresh_button)

        self.select_file_layout.addStretch()

        self.h_widget = QGroupBox(parent=self)
        self.h_widget.setTitle("Dataset Spilt")
        self.h_layout = QHBoxLayout()
        self.h_widget.setLayout(self.h_layout)
        self.v_layout.addWidget(self.h_widget)

        # Train
        self.dataset_train_list_widget = SpiltListWidget(
            spilt_type=SpiltType.TRAIN, parent=self.h_widget
        )
        self.h_layout.addWidget(self.dataset_train_list_widget)

        # Val
        self.dataset_val_list_widget = SpiltListWidget(
            spilt_type=SpiltType.VAL, parent=self.h_widget
        )
        self.h_layout.addWidget(self.dataset_val_list_widget)

        # Test
        self.dataset_test_list_widget = SpiltListWidget(
            spilt_type=SpiltType.TEST, parent=self.h_widget
        )
        self.h_layout.addWidget(self.dataset_test_list_widget)

        # Other
        self.dataset_other_list_widget = SpiltListWidget(
            spilt_type=SpiltType.NONE, parent=self.h_widget
        )
        self.h_layout.addWidget(self.dataset_other_list_widget)

        # Control Button
        self.control_widget = QWidget(parent=self)
        self.control_layout = QHBoxLayout()
        self.control_widget.setLayout(self.control_layout)
        self.v_layout.addWidget(self.control_widget)

        reload_button = QPushButton("Reload", parent=self.control_widget)
        reload_button.clicked.connect(self.reload)
        # 大小尽可能小
        reload_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        )
        self.control_layout.addWidget(reload_button)

        stats_count_button = QPushButton("Stats Count", parent=self.control_widget)
        stats_count_button.clicked.connect(self.stats_count)
        # 大小尽可能小
        stats_count_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        )
        self.control_layout.addWidget(stats_count_button)

        save_button = QPushButton("Save", parent=self.control_widget)
        save_button.clicked.connect(self.save)
        # 大小尽可能小
        save_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        )
        self.control_layout.addWidget(save_button)

        # Setting
        setting_group = QGroupBox("Setting")
        setting_layout = QVBoxLayout()
        setting_group.setLayout(setting_layout)
        self.v_layout.addWidget(setting_group)

        setting_layout.addWidget(QLabel("Depth:"))
        self.dir_depth_lineedit = QLineEdit(parent=self)
        self.dir_depth_lineedit.setText(str(self.depth))
        setting_layout.addWidget(self.dir_depth_lineedit)

        setting_layout.addWidget(QLabel("File Name Depth:"))
        self.file_name_depth_lineedit = QLineEdit(parent=self)
        self.file_name_depth_lineedit.setText(str(2))
        setting_layout.addWidget(self.file_name_depth_lineedit)

        # Connect Menu
        self.__connect_menu()

    def __connect_menu(self):
        def __connect_list_menu(list_widget: SpiltListWidget):
            list_widget.menu_move_to_train.triggered.connect(
                lambda: self.item_move(list_widget.selection_text, SpiltType.TRAIN)
            )
            list_widget.menu_move_to_val.triggered.connect(
                lambda: self.item_move(list_widget.selection_text, SpiltType.VAL)
            )
            list_widget.menu_move_to_test.triggered.connect(
                lambda: self.item_move(list_widget.selection_text, SpiltType.TEST)
            )
            list_widget.menu_move_to_other.triggered.connect(
                lambda: self.item_move(list_widget.selection_text, SpiltType.NONE)
            )

            # 连接移动全部菜单项
            list_widget.menu_move_all_to_train.triggered.connect(
                lambda: self.items_move_all(list_widget.spilt_type, SpiltType.TRAIN)
            )
            list_widget.menu_move_all_to_val.triggered.connect(
                lambda: self.items_move_all(list_widget.spilt_type, SpiltType.VAL)
            )
            list_widget.menu_move_all_to_test.triggered.connect(
                lambda: self.items_move_all(list_widget.spilt_type, SpiltType.TEST)
            )
            list_widget.menu_move_all_to_other.triggered.connect(
                lambda: self.items_move_all(list_widget.spilt_type, SpiltType.NONE)
            )

        __connect_list_menu(self.dataset_train_list_widget)
        __connect_list_menu(self.dataset_val_list_widget)
        __connect_list_menu(self.dataset_test_list_widget)
        __connect_list_menu(self.dataset_other_list_widget)

    def load_json_list(self):
        if not os.path.exists(self.work_directory_path):
            return

        file_list = os.listdir(self.work_directory_path)
        file_list = [f for f in file_list if f.endswith(".spilt.json")]

        abs_path_list = [os.path.join(self.work_directory_path, f) for f in file_list]

        def sort_by_modify_time(path_list: List[str]) -> List[str]:
            return sorted(path_list, key=lambda x: os.path.getmtime(x), reverse=True)

        abs_path_list = sort_by_modify_time(abs_path_list)
        file_list = [os.path.basename(f) for f in abs_path_list]

        if len(file_list) == 0:
            file_list.append("default.spilt.json")

        self.select_file_combobox.clear()
        self.select_file_combobox.addItems(file_list)

    def __select_file_changed(self):
        self.json_file_name = self.select_file_combobox.currentText()

    @property
    def json_file_name(self):
        return self.__json_file_name

    @json_file_name.setter
    def json_file_name(self, value):
        value = str(value).strip()

        if value == "":
            return

        if not value.endswith(".spilt.json"):
            return

        self.__json_file_name = value

    @property
    def settings_json_path(self) -> str:
        path = os.path.join(self.work_directory_path, self.json_file_name)

        if not os.path.exists(self.work_directory_path):
            try:
                os.makedirs(self.work_directory_path, exist_ok=True)
            except Exception as e:
                logger.error(f"Create Directory Error: {e}")

        logger.info(f"Current json path: {path}")

        return path

    def reload(self):
        self.reload_data()
        self.update_spilt_list_widget()

    def reload_data(self):
        json_path = self.settings_json_path

        logger.info(f"Load Data From: {json_path}")

        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                json_dict: dict = json.load(f)

            self.json_dict.clear()
            self.json_dict.update(json_dict)

            # if len(json_dict.keys()) > 0:
            #     self.json_dict.update(json_dict)

        try:
            file_name_depth = json_dict.get("file_name_depth", 2)
            self.file_name_depth_lineedit.setText(str(file_name_depth))
        except Exception:
            pass

        dir_level = 2
        try:
            dir_level = int(self.dir_depth_lineedit.text())
        except Exception as e:
            logger.error(f"Dir Level Error: {e}")
        self.depth = dir_level

        dir_list = get_dataset_dir_list(
            dataset_dir_path=self.work_directory_path,
            depth=dir_level,
            black_list=["Task"],
        )

        all_dataset_obj_list: List[DatasetSpilt] = []

        for dir_path in dir_list:
            current_obj = DatasetSpilt(
                path=dir_path, base_dir_path=self.work_directory_path
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
            unique_path = dataset_obj.unique_path

            all_path_str_list.append(unique_path)

            if unique_path in train_str_list:
                dataset_obj.spilt_type = SpiltType.TRAIN
            elif unique_path in val_str_list:
                dataset_obj.spilt_type = SpiltType.VAL
            elif unique_path in test_str_list:
                dataset_obj.spilt_type = SpiltType.TEST

        new_dict = {"all": {"path_str_list": all_path_str_list}}
        self.json_dict.update(new_dict)

        self.dataset_dir_list.clear()
        self.dataset_dir_list.extend(all_dataset_obj_list)

        self.__last_load_file_name = self.json_file_name

    def __get_spilt_dict(self, dataset_obj_list: List[DatasetSpilt]) -> dict:
        final_dict: dict = {"dataset_list": [], "path_str_list": []}

        dataset_dict_list: List[dict] = []
        unique_path_str_list: List[str] = []

        for dataset_obj in dataset_obj_list:
            if dataset_obj.is_valid():
                dataset_dict_list.append(dataset_obj.to_dict())
                unique_path_str_list.append(dataset_obj.unique_path)

        final_dict["dataset_list"] = dataset_dict_list
        final_dict["path_str_list"] = unique_path_str_list

        return final_dict

    def __get_spilt_list(
        self, dataset_dir_list: Optional[List[DatasetSpilt]] = None
    ) -> Tuple[
        List[DatasetSpilt], List[DatasetSpilt], List[DatasetSpilt], List[DatasetSpilt]
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
            dataset_obj_list_other,
        )

    def save(self):
        if self.__last_load_file_name != self.json_file_name:
            ok = QMessageBox.warning(
                self,
                "Warning",
                ("Have you load the file?\n" "You really want to save???"),
                QMessageBox.StandardButton.Yes,
                QMessageBox.StandardButton.No,
            )
            if ok != QMessageBox.StandardButton.Yes:
                return

        self.__update_dataset_props()

        (dataset_obj_list_train, dataset_obj_list_val, dataset_obj_list_test, _) = (
            self.__get_spilt_list()
        )

        train_dict = self.__get_spilt_dict(dataset_obj_list_train)
        val_dict = self.__get_spilt_dict(dataset_obj_list_val)
        test_dict = self.__get_spilt_dict(dataset_obj_list_test)

        self.json_dict["train"].update(train_dict)
        self.json_dict["val"].update(val_dict)
        self.json_dict["test"].update(test_dict)

        self.json_dict["depth"] = self.depth

        file_name_depth = 2
        try:
            file_name_depth = int(self.file_name_depth_lineedit.text().strip())
        except Exception:
            pass
        self.json_dict["file_name_depth"] = file_name_depth

        with open(self.settings_json_path, "w", encoding="utf-8") as f:
            json.dump(obj=self.json_dict, fp=f, indent=4, ensure_ascii=False)

    def __update_dataset_props(self):
        for dataset_obj in self.dataset_dir_list:
            file_name_depth = 2
            try:
                file_name_depth = int(self.file_name_depth_lineedit.text().strip())
            except Exception:
                pass

            dataset_obj.depth = self.depth
            dataset_obj.file_name_depth = file_name_depth

    def __update_list_widget_with_list(
        self,
        list_widget: SpiltListWidget,
        dataset_obj_list: List[DatasetSpilt],
    ):
        selection_text = list_widget.selection_text
        list_widget.list_widget.clear()

        for dataset_obj in dataset_obj_list:
            text = dataset_obj.unique_path
            list_widget.list_widget.addItem(text)

        list_widget.try_to_select_text(selection_text)
        list_widget.update()

    def update_spilt_list_widget(self):
        (
            dataset_obj_list_train,
            dataset_obj_list_val,
            dataset_obj_list_test,
            dataset_obj_list_other,
        ) = self.__get_spilt_list()

        self.__update_list_widget_with_list(
            list_widget=self.dataset_train_list_widget,
            dataset_obj_list=dataset_obj_list_train,
        )
        self.__update_list_widget_with_list(
            list_widget=self.dataset_val_list_widget,
            dataset_obj_list=dataset_obj_list_val,
        )
        self.__update_list_widget_with_list(
            list_widget=self.dataset_test_list_widget,
            dataset_obj_list=dataset_obj_list_test,
        )
        self.__update_list_widget_with_list(
            list_widget=self.dataset_other_list_widget,
            dataset_obj_list=dataset_obj_list_other,
        )

    def item_move(self, unique_path: str, target_spilt_type: SpiltType):
        logger.debug(f"Unique Path: {unique_path}, Spilt Type: {target_spilt_type}")

        for dataset_obj in self.dataset_dir_list:
            if dataset_obj.unique_path == unique_path:
                dataset_obj.spilt_type = target_spilt_type
                break

        self.update_spilt_list_widget()

    def items_move_all(
        self, source_spilt_type: SpiltType, target_spilt_type: SpiltType
    ):
        logger.debug(f"Move all from {source_spilt_type} to {target_spilt_type}")

        if source_spilt_type == target_spilt_type:
            return

        # 统计要移动的数据集数量
        count = 0
        for dataset_obj in self.dataset_dir_list:
            if dataset_obj.spilt_type == source_spilt_type:
                count += 1

        if count == 0:
            return

        # 获取源和目标的显示名称
        source_name = self.__spilt_type_name_map.get(source_spilt_type, "Unknown")
        target_name = self.__spilt_type_name_map.get(target_spilt_type, "Unknown")

        # 显示确认对话框
        reply = QMessageBox.question(
            self,
            "确认批量移动",
            f"您确定要将所有 {count} 个数据集从 {source_name} 移动到 {target_name} 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # 执行移动
        for dataset_obj in self.dataset_dir_list:
            if dataset_obj.spilt_type == source_spilt_type:
                dataset_obj.spilt_type = target_spilt_type

        self.update_spilt_list_widget()

    def stats_count(self):
        (
            dataset_obj_list_train,
            dataset_obj_list_val,
            dataset_obj_list_test,
            dataset_obj_list_other,
        ) = self.__get_spilt_list()

        def get_count(dataset_obj_list: List[DatasetSpilt]):
            count = 0
            for dataset_obj in dataset_obj_list:
                count += stats_file_count(dataset_obj.abs_path, "jpg")

            return count

        train_count = get_count(dataset_obj_list_train)
        val_count = get_count(dataset_obj_list_val)
        test_count = get_count(dataset_obj_list_test)
        other_count = get_count(dataset_obj_list_other)

        used_count = train_count + val_count + test_count

        train_rate = round((train_count / used_count) * 100, 2)
        val_rate = round((val_count / used_count) * 100, 2)
        test_rate = round((test_count / used_count) * 100, 2)

        text = (
            f"Train: {train_count}({train_rate}%))\n"
            f"Val: {val_count}({val_rate}%))\n"
            f"Test: {test_count}({test_rate}%))\n"
            f"Other: {other_count}\n"
            "\n"
            f"Used: {used_count}\n"
            f"Train+Val: {train_count + val_count}\n"
            f"Total: {used_count + other_count}\n"
        ).strip()

        QMessageBox.information(self, "Stats Count", text)


if __name__ == "__main__":
    app = QApplication([])

    path = r"/mnt/h/Datasets/TrackShipOnlineVideo/LabelMe"
    # path = r"H:\Datasets\TrackShipOnlineVideo\LabelMe"

    window = InterFaceDatasetSpilt(work_directory_path=path)
    window.show()

    app.exec()
