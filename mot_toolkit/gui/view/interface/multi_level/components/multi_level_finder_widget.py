import os.path
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QScrollArea
)

from gui.view.components. \
    base_q_widget_with_layout import BaseQWidgetWithLayout
from gui.view.interface.multi_level. \
    components.file_list_widget import FileListWidget


class MultiLevelFinderWidget(BaseQWidgetWithLayout):
    list_widget_list: List[FileListWidget]

    def __init__(self, work_directory_path: str = "", parent=None):
        super().__init__(
            work_directory_path=work_directory_path,
            parent=parent
        )

        self.list_widget_list = []

        self.__init_widgets()

        self.__set_widget_properties()

    def __init_widgets(self):
        self.scroll_area = QScrollArea()

        self.h_widget = QWidget()
        self.h_layout = QHBoxLayout()
        self.h_layout.setSpacing(0)
        self.h_widget.setLayout(self.h_layout)
        self.scroll_area.setWidget(self.h_widget)

        self.v_layout.addWidget(self.scroll_area)

    def __set_widget_properties(self):
        # Block Vertical Scroll Bar
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

    @property
    def current_depth(self) -> int:
        return len(self.list_widget_list)

    def check_work_directory_path(self) -> bool:
        return os.path.isdir(self.work_directory_path)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    path = "../../../../../.."
    path = os.path.abspath(path)
    print(path)

    app = QApplication(sys.argv)
    widget = MultiLevelFinderWidget(work_directory_path=path)
    widget.setFixedHeight(400)
    widget.show()
    sys.exit(app.exec())
