from gui.view.components. \
    base_interface_window import BaseInterfaceWindow
from gui.view.interface.multi_level. \
    components.multi_level_finder_widget import MultiLevelFinderWidget


class InterfaceMultiLevel(BaseInterfaceWindow):

    def __init__(self, work_directory_path: str):
        super().__init__(work_directory_path=work_directory_path)

        self.__setup_window_properties()

        self.__init_widgets()

    def __setup_window_properties(self):
        self.setWindowTitle("Multi Level Finder")
        self.setMinimumSize(640, 320)

    def __init_widgets(self):
        self.multi_level_finder = \
            MultiLevelFinderWidget(
                work_directory_path=self.work_directory_path,
                parent=self
            )

        self.multi_level_finder.label_title.setVisible(True)
        self.multi_level_finder.label_current_path.setVisible(True)

        self.v_layout.addWidget(self.multi_level_finder)
