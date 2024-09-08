from typing import List

from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction

from mot_toolkit.gui.view.components. \
    windget.list_with_title_widget import ListWithTitleWidget


class FileListWidget(ListWithTitleWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__setup_widget_properties()

        self.__init_widgets()

        self.__init_menu()

    def __setup_widget_properties(self):
        self.set_title("File")

    def __init_widgets(self):
        pass

    def __init_menu(self):
        self.list_widget.have_menu = True
        q_menu: QMenu = self.list_widget.menu
        select_enable_list: List[QAction] = \
            self.list_widget.select_enable_list

        q_menu.addSeparator()

        self.menu_reload_file = \
            QAction("Reload File", self)
        q_menu.addAction(self.menu_reload_file)
        select_enable_list.append(self.menu_reload_file)

        q_menu.addSeparator()

        self.menu_copy_path_image = \
            QAction("Copy Image File Path", self)
        q_menu.addAction(self.menu_copy_path_image)
        select_enable_list.append(self.menu_copy_path_image)
        self.menu_copy_path_json = \
            QAction("Copy Json File Path", self)
        q_menu.addAction(self.menu_copy_path_json)
        select_enable_list.append(self.menu_copy_path_json)

        q_menu.addSeparator()

        self.menu_show_in_explorer = \
            QAction("Show in Explorer", self)
        q_menu.addAction(self.menu_show_in_explorer)
        select_enable_list.append(self.menu_show_in_explorer)
