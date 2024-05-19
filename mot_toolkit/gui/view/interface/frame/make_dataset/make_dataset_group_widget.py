from PySide6.QtWidgets import QPushButton

from mot_toolkit.gui.view.components.base_group_widget import BaseGroupWidget


class MakeDatasetGroupWidget(BaseGroupWidget):

    def __init__(self, work_directory_path: str = "", parent=None):
        super().__init__(parent=parent, title="Make Dataset")

        self.work_directory_path = work_directory_path

        self.__setup_widget_properties()

        self.__init_widgets()

    def __setup_widget_properties(self):
        pass

    def __init_widgets(self):
        self.btn_target_disappear = QPushButton("Target Disappear")
        self.btn_target_disappear.clicked.connect(
            self.__button_target_disappear_clicked
        )
        self.v_layout.addWidget(self.btn_target_disappear)

    def __button_target_disappear_clicked(self):
        pass
