from typing import List

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu

from mot_toolkit.gui.view. \
    components.list_with_title_widget import ListWithTitleWidget


class ObjectListWidget(ListWithTitleWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__setup_widget_properties()

        self.__init_widgets()

        self.__init_menu()

    def __setup_widget_properties(self):
        self.set_title("Annotation Object")

    def __init_widgets(self):
        pass

    def __init_menu(self):
        self.list_widget.have_menu = True
        q_menu: QMenu = self.list_widget.menu
        select_enable_list: List[QAction] = \
            self.list_widget.select_enable_list

        self.menu_operate_del = \
            QAction(
                "Delete the target",
                q_menu
            )
        q_menu.addAction(self.menu_operate_del)
        select_enable_list.append(self.menu_operate_del)

        self.menu_operate_del_subsequent = \
            QAction(
                "Delete the target in subsequent frames(Label)",
                q_menu
            )
        q_menu.addAction(self.menu_operate_del_subsequent)
        select_enable_list.append(self.menu_operate_del_subsequent)

        q_menu.addSeparator()

        self.menu_mark_appear = \
            QAction(
                "Mark as Appear Frame",
                q_menu
            )
        q_menu.addAction(self.menu_mark_appear)
        select_enable_list.append(self.menu_mark_appear)

        q_menu.addSeparator()

        self.menu_unselect_all = \
            QAction(
                "Unselect All",
                q_menu
            )
        q_menu.addAction(self.menu_unselect_all)
        select_enable_list.append(self.menu_unselect_all)
