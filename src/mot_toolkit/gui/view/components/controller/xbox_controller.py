from PySide6.QtWidgets import QWidget


class XboxController(QWidget):

    def __init__(self):
        super().__init__()

        self.__init_properties()

        self.__init_ui()

        self.__init_objects()

    def __init_properties(self):
        self.setMinimumWidth(0)
        self.setMaximumWidth(0)

        self.setMinimumHeight(0)
        self.setMaximumHeight(0)

    def __init_ui(self):
        pass

    def __init_objects(self):
        pass
