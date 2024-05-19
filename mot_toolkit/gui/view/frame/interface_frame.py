from mot_toolkit.gui.view.interface.base_interface import BaseInterface


class InterfaceFrame(BaseInterface):

    def __init__(self, work_directory_path: str):
        super().__init__(work_directory_path=work_directory_path)

        self.work_directory_path = work_directory_path

        self.__setup_window_properties()

        self.__init_widgets()

    def __setup_window_properties(self):
        self.setWindowTitle("Frame Operations")

    def __init_widgets(self):
        pass
