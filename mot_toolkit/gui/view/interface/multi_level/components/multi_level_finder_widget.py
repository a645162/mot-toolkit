import os.path
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QScrollArea, QLabel, QSizePolicy
)

from datatype.directory.dir_file import DirectoryAndFile
from gui.view.components. \
    base_q_widget_with_layout import BaseQWidgetWithLayout
from gui.view.interface.multi_level. \
    components.file_list_widget import FileListWidget


class MultiLevelFinderWidget(BaseQWidgetWithLayout):
    slot_path_changed: Signal = Signal(str)

    __current_path: str = ""

    base_directory_path: str = ""
    base_directory_obj: DirectoryAndFile

    __current_valid_depth = 0

    __list_widget_list: List[FileListWidget]

    def __init__(self, work_directory_path: str = "", parent=None):
        super().__init__(
            work_directory_path=work_directory_path,
            parent=parent
        )

        self.__list_widget_list = []

        self.__init_widgets()

        self.__set_widget_properties()

        self.__init_base_dir()

    def __init_widgets(self):
        label_title = QLabel("Select the directory:")

        self.scroll_area = QScrollArea()

        self.h_widget = QWidget(self)
        self.h_layout = QHBoxLayout()
        self.h_layout.setSpacing(0)
        self.h_widget.setLayout(self.h_layout)

        # Set Color for Debug
        # self.h_widget.setStyleSheet(
        #     "background-color: rgb(255, 255, 255);"
        #     "border: 1px solid rgb(0, 0, 0);"
        # )

        self.scroll_area.setWidget(self.h_widget)

        self.list_widget_container = QWidget(self.h_widget)
        self.list_widget_layout = QHBoxLayout()
        self.list_widget_container.setLayout(self.list_widget_layout)
        self.h_layout.addWidget(self.list_widget_container)
        self.h_layout.addStretch()

        self.h_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.scroll_area.setWidget(self.h_widget)
        self.scroll_area.setWidgetResizable(True)

        self.label_current_path = QLabel(parent=self)
        self.label_current_path.setText("Current Path:[None]")

        self.v_layout.addWidget(label_title)
        self.v_layout.addWidget(self.scroll_area)
        self.v_layout.addWidget(self.label_current_path)

    def __set_widget_properties(self):
        # Block Vertical Scroll Bar
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

    def __init_base_dir(self):
        self.base_directory_obj = \
            DirectoryAndFile(self.work_directory_path)
        self.base_directory_obj.walk_dir()
        self.base_directory_obj.update()

        self.base_list_widget = FileListWidget(parent=self.h_widget)

        self.base_list_widget.current_depth = 0
        self.base_list_widget.current_directory_obj = self.base_directory_obj
        self.base_list_widget.update_list_content()
        self.base_list_widget.slot_selection_changed.connect(
            self.__list_widget_selection_changed
        )
        self.base_list_widget.slot_focused.connect(
            self.__list_widget_focused
        )

        self.list_widget_layout.addWidget(self.base_list_widget)
        self.__list_widget_list.append(self.base_list_widget)

    def __list_widget_selection_changed(self, widget_index: int):
        list_widget: FileListWidget = \
            self.__list_widget_list[widget_index]

        # selection_index = list_widget.selection_index
        text = list_widget.selection_text

        is_dir = text.endswith("/")

        if is_dir:
            text = text[:-1]

            while widget_index < self.max_depth - 1:
                self.remove_last_list_widget()

            child_obj = None
            for current_child_obj in list_widget.current_directory_obj.child_dir_object_list:
                if current_child_obj.directory_name == text:
                    child_obj = current_child_obj
            if child_obj is None:
                return

            child_obj.walk_dir()
            child_obj.update()

            new_list_widget: FileListWidget = FileListWidget(parent=self.h_widget)

            new_list_widget.current_depth = widget_index + 1
            new_list_widget.current_directory_obj = child_obj
            new_list_widget.update_list_content()

            self.list_widget_layout.addWidget(new_list_widget)
            self.__list_widget_list.append(new_list_widget)

            h_scroll_bar = self.scroll_area.horizontalScrollBar()
            # Set the horizontal scroll bar to the right
            h_scroll_bar.setValue(h_scroll_bar.maximum())
            h_scroll_bar.update()

            new_list_widget.slot_selection_changed.connect(
                self.__list_widget_selection_changed
            )
            new_list_widget.slot_focused.connect(
                self.__list_widget_focused
            )

        self.__list_widget_focused(widget_index)

    def __list_widget_focused(self, index: int):
        self.__current_valid_depth = index
        self.__generate_path()

    @property
    def current_valid_depth(self):
        return min(self.__current_valid_depth, self.max_depth - 1)

    @property
    def max_depth(self) -> int:
        return len(self.__list_widget_list)

    def check_work_directory_path(self) -> bool:
        return os.path.isdir(self.work_directory_path)

    def remove_last_list_widget(self):
        if self.max_depth > 1:
            self.h_layout.removeWidget(self.__list_widget_list[-1])
            self.__list_widget_list[-1].deleteLater()

            self.__list_widget_list.pop()

    @property
    def path(self) -> str:
        return self.__current_path

    def __generate_path(self):
        path = ""

        def fix_name(name: str) -> str:
            name = name.strip()

            if name.endswith("/"):
                name = name[:-1]

            return name

        for i in range(self.current_valid_depth + 1):
            list_widget = self.__list_widget_list[i]

            text = fix_name(list_widget.selection_text)
            if len(text) == 0:
                break

            path = os.path.join(path, text)

        if os.path.exists(path):
            path = os.path.abspath(path)

        self.__current_path = path

        # Show the current path
        if os.path.exists(path):
            if os.path.isdir(path):
                self.label_current_path.setText(f"Current Directory Path:{path}")
            else:
                self.label_current_path.setText(f"Current File Path:{path}")
        else:
            self.label_current_path.setText(f"Current Path:{path}")

        # Notify the path changed
        self.slot_path_changed.emit(path)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    path = "../../../../../.."
    path = os.path.abspath(path)
    print(path)

    app = QApplication(sys.argv)
    widget = MultiLevelFinderWidget(work_directory_path=path)
    # widget.setFixedWidth(1200)
    # widget.setFixedHeight(400)
    widget.setMinimumSize(400, 400)
    widget.show()
    sys.exit(app.exec())
