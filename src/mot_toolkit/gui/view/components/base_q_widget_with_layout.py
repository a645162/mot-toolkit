from PySide6.QtWidgets import QVBoxLayout

from mot_toolkit.gui.view.components.base_q_widget import BaseQWidget


class BaseQWidgetWithLayout(BaseQWidget):

    def __init__(self, work_directory_path: str = "", parent=None):
        super().__init__(parent=parent)

        self.work_directory_path = work_directory_path

        self.__init_widgets()

        self.__setup_widget_properties()

    def __init_widgets(self):
        self.v_layout = QVBoxLayout()
        self.v_layout.setSpacing(0)
        self.setLayout(self.v_layout)

    def __setup_widget_properties(self):
        self.setWindowTitle("Base QWidget with Layout")
