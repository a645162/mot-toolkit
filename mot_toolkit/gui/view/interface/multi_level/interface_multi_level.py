from gui.view.components. \
    base_interface_window import BaseInterfaceWindow


class InterfaceMultiLevel(BaseInterfaceWindow):

    def __init__(self, work_directory_path: str):
        super().__init__(work_directory_path=work_directory_path)

        self.__setup_window_properties()

        self.__init_widgets()

    def __setup_window_properties(self):
        self.setWindowTitle("Multi Level Interface")

    def __init_widgets(self):
        pass
