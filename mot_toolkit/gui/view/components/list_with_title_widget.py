from typing import List

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel
)

from mot_toolkit.gui.view. \
    components.base_list_widget_with_menu import BaseListWidgetWithMenu


class ListWithTitleWidget(QWidget):
    title: str
    __title: str
    __title_show: str

    __count_offset: int = 0

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
        self.v_layout.addWidget(self.label_title)

        self.list_widget = BaseListWidgetWithMenu(parent=self)
        self.v_layout.addWidget(self.list_widget)

        self.label_title.setText("Title")

    def set_title(self, title: str):
        self.title = title
        self.list_widget.title = self.title

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
        self.update()

    @property
    def count_offset(self) -> int:
        return self.__count_offset

    @count_offset.setter
    def count_offset(self, value: int):
        self.__count_offset = value

        self.update()

    @property
    def __title_show(self) -> str:
        title_str = self.title

        end_str = ""

        count = self.list_widget.count() + self.count_offset

        if count == 0:
            end_str = end_str + " [Empty]"
        else:
            end_str = end_str + " [" + str(count) + "]"

        title_str = title_str + end_str

        if not title_str.endswith(":"):
            title_str = title_str + ":"

        return title_str

    def update(self):
        super().update()

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
    def selection_text(self) -> str:
        return self.list_widget.selection_text

    @selection_text.setter
    def selection_text(self, text: str):
        self.list_widget.selection_text = text

    @property
    def count(self) -> int:
        return self.list_widget.count()

    def is_selected_last(self) -> bool:
        return self.selection_index == self.count - 1
