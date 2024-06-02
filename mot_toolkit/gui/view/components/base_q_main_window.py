from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow

# Load Settings
from mot_toolkit.gui.common.global_settings import program_settings


class BaseQMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__setup_window_properties()

        self.__init_widgets()

    def __setup_window_properties(self):
        # Set Logo
        self.setWindowIcon(QIcon(":/general/logo"))

    def __init_widgets(self):
        pass

    def closeEvent(self, event):
        program_settings.save()
        super().closeEvent(event)
