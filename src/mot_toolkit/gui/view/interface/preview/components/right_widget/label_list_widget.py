from typing import List

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu

from mot_toolkit.gui.view.components.widget. \
    list.list_with_title_widget import ListWithTitleWidget


class LabelClassListWidget(ListWithTitleWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__setup_widget_properties()

        self.__init_widgets()

        self.__init_menu()

    def __setup_widget_properties(self):
        self.set_title("Label(Classes)")
        self.count_offset = -1

    def __init_widgets(self):
        pass

    def __init_menu(self):
        self.list_widget.have_menu = True

        q_menu: QMenu = self.list_widget.menu
        select_enable_list: List[QAction] = \
            self.list_widget.select_enable_list

        # Change Class
        self.menu_change_class = QAction("Change Class", self)
        q_menu.addAction(self.menu_change_class)
        select_enable_list.append(self.menu_change_class)

    def keyPressEvent(self, event):
        modifier_key = event.modifiers()
        key = event.key()

        send_to_parent = False

        if modifier_key == Qt.KeyboardModifier.NoModifier:
            if key == Qt.Key.Key_D:
                send_to_parent = True

                # Prevent
                event.ignore()

        if send_to_parent:
            if self.parent():
                self.parent().keyPressEvent(event)
