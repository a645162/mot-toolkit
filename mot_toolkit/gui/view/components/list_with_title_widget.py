from typing import List

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel, QListWidget
)


class ListWithTitleWidget(QWidget):
    title: str
    __title: str
    __title_show: str

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__setup_widget_properties()

        self.__init_widgets()

    def __setup_widget_properties(self):
        pass

    def __init_widgets(self):
        self.v_layout = QVBoxLayout()
        self.setLayout(self.v_layout)

        self.label_title = QLabel(parent=self)
        self.label_title.setText("Title")
        self.v_layout.addWidget(self.label_title)

        self.list_widget = QListWidget(parent=self)
        self.v_layout.addWidget(self.list_widget)

    def set_title(self, title: str):
        self.title = title

    def get_title(self) -> str:
        return self.title

    @property
    def title(self) -> str:
        title_str = self.__title.strip()
        while title_str.endswith(":"):
            title_str = title_str[:-1]
        return title_str

    @title.setter
    def title(self, title: str):
        title_str = title.strip()
        self.__title = title_str
        self.update_ui()

    @property
    def __title_show(self) -> str:
        title_str = self.title

        list_empty_str = ""
        if self.list_widget.count() == 0:
            list_empty_str = " (Empty)"
        title_str = title_str + list_empty_str

        if not title_str.endswith(":"):
            title_str = title_str + ":"

        return title_str

    def update_ui(self):
        self.label_title.setText(self.__title_show)

    @property
    def selection_index(self) -> int:
        selected_items = self.list_widget.selectedItems()
        if len(selected_items) == 0:
            return -1

        selected_item = selected_items[0]
        index = self.list_widget.row(selected_item)

        return index

    @selection_index.setter
    def selection_index(self, index: int):
        if index < 0 or index >= self.list_widget.count():
            return

        self.list_widget.setCurrentRow(index)

    @property
    def selection_index_list(self) -> List[int]:
        selected_items = self.list_widget.selectedItems()

        index_list = []

        for selected_item in selected_items:
            index = self.list_widget.row(selected_item)
            if index not in index_list:
                index_list.append(index)

        return index_list

    @property
    def count(self) -> int:
        return self.list_widget.count()
