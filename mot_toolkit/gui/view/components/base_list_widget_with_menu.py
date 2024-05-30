from typing import List

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QListWidget, QMenu


class BaseListWidgetWithMenu(QListWidget):
    title = ""

    menu: QMenu
    have_menu: bool = False

    # Only enable when selection is not empty
    select_enable_list: List[QAction]

    def __init__(self, parent=None):
        super().__init__(parent)

        self.select_enable_list = []

        self.__init_menu()

        self.itemSelectionChanged.connect(self.__selection_changed)

    def __init_menu(self):
        self.menu = QMenu(self)

        self.menu_global_title = \
            QAction("", self)
        self.menu_global_title.setEnabled(False)
        self.menu.addAction(self.menu_global_title)

        self.menu_global_selection_index = \
            QAction("", self)
        self.menu_global_selection_index.setEnabled(False)
        self.menu.addAction(self.menu_global_selection_index)

        self.menu_global_total_count = \
            QAction("", self)
        self.menu_global_total_count.setEnabled(False)
        self.menu.addAction(self.menu_global_total_count)

    def update_menu(self):
        self.title = self.title.strip()
        if len(self.title) > 0:
            self.menu_global_title.setText(self.title)
            self.menu_global_title.setToolTip(self.title)
            self.menu_global_title.setVisible(True)
        else:
            self.menu_global_title.setVisible(False)

        selection_index = self.selection_index
        selection_index_str = "None"
        if selection_index != -1:
            selection_index_str = str(selection_index)
        current_action_text = \
            f"Current Selection Index:{selection_index_str}"
        self.menu_global_selection_index.setText(current_action_text)
        self.menu_global_selection_index.setToolTip(current_action_text)

        current_action_text = \
            f"Total Count:{self.count()}"
        self.menu_global_total_count.setText(current_action_text)
        self.menu_global_total_count.setToolTip(current_action_text)

        for action in self.select_enable_list:
            action.setEnabled(selection_index != -1)

    def contextMenuEvent(self, event):
        if not self.have_menu:
            return

        self.update_menu()

        self.menu.exec_(event.globalPos())

    @property
    def selection_index(self) -> int:
        selected_items = self.selectedItems()
        if len(selected_items) == 0:
            return -1

        selected_item = selected_items[0]
        index = self.row(selected_item)

        return index

    @selection_index.setter
    def selection_index(self, index: int):
        if index < 0 or index >= self.count():
            return

        self.setCurrentRow(index)

    @property
    def selection_index_list(self) -> List[int]:
        selected_items = self.selectedItems()

        index_list = []

        for selected_item in selected_items:
            index = self.row(selected_item)
            if index not in index_list:
                index_list.append(index)

        return index_list

    def clear(self):
        super().clear()

        self.update_menu()

    def __selection_changed(self):
        self.update_menu()
