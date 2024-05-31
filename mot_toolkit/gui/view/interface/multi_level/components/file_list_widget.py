from typing import List

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QSizePolicy

from datatype.directory.dir_file import DirectoryAndFile

from gui.view. \
    components.base_list_widget_with_menu import BaseListWidgetWithMenu


class FileListWidget(BaseListWidgetWithMenu):
    current_depth = -1

    current_directory_path: str = ""
    current_directory_obj: DirectoryAndFile

    slot_selection_changed: Signal = Signal(int)
    slot_focused: Signal = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.__init_widgets()

        self.__set_widget_properties()

    def __init_widgets(self):
        self.itemSelectionChanged.connect(self.__file_list_selection_changed)

    def __set_widget_properties(self):
        self.setFixedWidth(200)
        # self.setFixedHeight(200)
        self.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding
        )

    def update_list_content(self):
        if self.current_directory_obj is None:
            return
        if self.current_directory_obj.is_walked() is False:
            return

        child_obj_list: List[DirectoryAndFile] = \
            self.current_directory_obj.child_dir_object_list
        for child_obj in child_obj_list:
            dir_name = child_obj.directory_name
            self.add_dir(dir_name + "/")

        for file_name in self.current_directory_obj.file_name_list:
            self.add_file(file_name)

    def add_dir(self, dir_name: str):
        self.addItem(dir_name)

    def add_file(self, file_name: str):
        self.addItem(file_name)

    def setFixedWidth(self, w: int = 0):
        if w == 0:
            w = 200

        super().setFixedWidth(w)

    def setFixedHeight(self, h: int = 0):
        if h == 0:
            h = 200

        super().setFixedHeight(h)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.slot_focused.emit(self.current_depth)

    def item_is_dir(self, index: int) -> bool:
        text = self.item(index).text()
        return text.endswith("/")

    def __file_list_selection_changed(self):
        self.slot_selection_changed.emit(self.current_depth)
