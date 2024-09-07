import os.path
from typing import List

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QSizePolicy, QApplication

from mot_toolkit.datatype.directory.dir_file import DirectoryAndFile

from mot_toolkit.gui.view.components. \
    windget.base_list_widget_with_menu import BaseListWidgetWithMenu


class FileListWidget(BaseListWidgetWithMenu):
    current_depth = -1

    current_directory_path: str = ""
    current_directory_obj: DirectoryAndFile

    slot_selection_changed: Signal = Signal(int)
    slot_double_clicked: Signal = Signal(int)
    slot_focused: Signal = Signal(int)
    slot_refreshed: Signal = Signal(int)

    __path: str = ""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.__init_widgets()

        self.__set_widget_properties()

        self.__init_menu()

    def __init_widgets(self):
        self.itemSelectionChanged.connect(self.__file_list_selection_changed)
        self.itemDoubleClicked.connect(
            lambda: self.slot_double_clicked.emit(self.current_depth)
        )

    def __set_widget_properties(self):
        self.setFixedWidth(200)
        # self.setFixedHeight(200)
        self.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding
        )

    def __init_menu(self):
        self.have_menu = True

        self.menu_global_title.setText("File List")
        self.menu_global_title.setVisible(True)

        self.menu.addSeparator()

        self.menu_refresh = QAction("Refresh", self.menu)
        self.menu_refresh.triggered.connect(self.refresh_list)
        self.menu.addAction(self.menu_refresh)

        self.menu.addSeparator()

        self.menu_copy_name = QAction("Copy File Name", self.menu)
        self.menu_copy_name.triggered.connect(self.__copy_name)
        self.menu.addAction(self.menu_copy_name)
        self.select_enable_list.append(self.menu_copy_name)

        self.menu_copy_all_name = QAction("Copy All File Name", self.menu)
        self.menu_copy_all_name.triggered.connect(self.__copy_all_name)
        self.menu.addAction(self.menu_copy_all_name)
        self.select_enable_list.append(self.menu_copy_all_name)

        self.menu_copy_path = QAction("Copy Path", self.menu)
        self.menu_copy_path.triggered.connect(self.__copy_path)
        self.menu.addAction(self.menu_copy_path)
        self.select_enable_list.append(self.menu_copy_path)

    def update_list_content(self):
        if self.current_directory_obj is None:
            return
        if self.current_directory_obj.is_walked() is False:
            return

        # Clear
        self.clear()

        child_obj_list: List[DirectoryAndFile] = \
            self.current_directory_obj.child_dir_object_list
        for child_obj in child_obj_list:
            dir_name = child_obj.directory_name
            self.add_dir(dir_name)

        for file_name in self.current_directory_obj.file_name_list:
            self.add_file(file_name)

    def add_dir(self, dir_name: str):
        self.addItem(dir_name + "/")

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
        self.update_path()

        self.slot_selection_changed.emit(self.current_depth)

    @property
    def path(self) -> str:
        return self.__path

    def update_path(self):
        if self.selection_index == -1:
            self.__path = ""
            return

        text = self.selection_text
        if text.endswith("/"):
            text = text[:-1]

        self.__path = os.path.join(
            self.current_directory_obj.directory_path,
            text
        )

    def refresh_list(self):
        self.current_directory_obj.walk_dir()
        self.update_list_content()

        self.slot_refreshed.emit(self.current_depth)

    def __copy_name(self):
        self.update_path()

        file_name = (
            self.selection_text
            .replace("/", "")
            .replace("\\", "")
        )

        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(file_name)

    def __copy_all_name(self):
        self.update_path()

        final_text = ""

        for i in range(self.count()):
            file_name = (
                self.item(i).text()
                .replace("/", "")
                .replace("\\", "")
            )
            final_text += file_name + "\n"

        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(final_text)

    def __copy_path(self):
        self.update_path()

        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(self.path)
