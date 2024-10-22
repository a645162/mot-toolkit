from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QApplication

# Load Settings
from mot_toolkit.gui.common.global_settings import program_settings
from mot_toolkit.gui.utils.screen import get_activate_screen


class BaseQMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__setup_window_properties()

        self.__init_widgets()

    def __setup_window_properties(self):
        # Set Logo
        # https://stackoverflow.com/questions/78354598/setting-the-window-icon-using-a-system-theme-icon
        # https://github.com/OpenShot/openshot-qt/issues/1112

        # icon = QIcon()
        # icon.addPixmap(QPixmap(":/general/logo"), QIcon.Selected, QIcon.On)
        # self.setWindowIcon(icon)

        self.setWindowIcon(QIcon(":/general/logo"))

    def __init_widgets(self):
        pass

    def closeEvent(self, event):
        program_settings.save()
        super().closeEvent(event)

    def move_to_center(self):
        window_handle = self.windowHandle()
        if window_handle is None:
            # Get Activate Screen
            screen = get_activate_screen()
        else:
            # Get the screen where the window currently resides
            screen = window_handle.screen()

        # Get the center point of the current screen
        center = screen.availableGeometry().center()

        # Get the geometry of the window's frame
        geo = self.frameGeometry()

        # Move the center of the window's frame to the center of the screen
        geo.moveCenter(center)

        # Move the window to the new position calculated by the geometry
        self.move(geo.topLeft())


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    window = BaseQMainWindow()
    window.show()

    window.move_to_center()

    sys.exit(app.exec())
