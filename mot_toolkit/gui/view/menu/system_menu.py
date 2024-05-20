from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenuBar

from mot_toolkit.utils.system_info import is_macos


class MenuAction(QAction):

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)


class SystemMenu:
    def __init__(self, parent=None, current_menubar: QMenuBar = None):
        if current_menubar is not None:
            self.menu_bar = current_menubar
        else:
            self.menu_bar = QMenuBar(parent=parent)

        self.__init_macos_program_menu()

        self.__init_children()

    def __init_macos_program_menu(self):
        # Check is macOS
        if not is_macos():
            return

        print("macOS detected.")
        print("Try to init macOS program menu.")

    def __init_children(self):
        # File Menu
        self.file_menu = self.menu_bar.addMenu("File")

        self.file_menu_open_dir = \
            MenuAction("Open Directory", self.file_menu)
        self.file_menu.addAction(self.file_menu_open_dir)

        # Help Menu
        self.help_menu = self.menu_bar.addMenu("Help")

        self.help_menu_about = MenuAction("About", self.help_menu)
        self.help_menu_about.setMenuRole(QAction.MenuRole.AboutRole)
        self.help_menu.addAction(self.help_menu_about)
