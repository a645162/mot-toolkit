from mot_toolkit.gui.view.components.base_interface import BaseInterface
from mot_toolkit.gui.view.interface. \
    frame.make_dataset.make_dataset_group_widget import MakeDatasetGroupWidget


class InterfaceFrame(BaseInterface):

    def __init__(self, work_directory_path: str):
        super().__init__(work_directory_path=work_directory_path)

        self.work_directory_path = work_directory_path

        self.__setup_window_properties()

        self.__init_widgets()

    def __setup_window_properties(self):
        self.setWindowTitle("Frame Operations")

    def __init_widgets(self):
        # self.label_work_directory_path = QLabel(self)
        # self.label_work_directory_path.setText(
        #     f"Work Directory Path: {self.work_directory_path}"
        # )
        # self.v_layout.addWidget(self.label_work_directory_path)
        #
        # self.v_layout.addSpacing(10)

        self.make_dataset_group = MakeDatasetGroupWidget(
            work_directory_path=self.work_directory_path,
            parent=self
        )
        self.v_layout.addWidget(self.make_dataset_group)
