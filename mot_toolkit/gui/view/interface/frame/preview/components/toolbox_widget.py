from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton
)


class ToolboxWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__setup_widget_properties()

        self.__init_widgets()

    def __setup_widget_properties(self):
        self.setFixedWidth(48)
        # pass

    def __init_widgets(self):
        self.v_layout = QVBoxLayout()
        self.setLayout(self.v_layout)

        self.btn_open_dir = QPushButton(parent=self)
        # self.btn_open_dir.setText("Open Directory")
        self.btn_open_dir.setIcon(QIcon(":/toolbox/folder_open"))
        self.btn_open_dir.setToolTip("Open Directory")
        self.v_layout.addWidget(self.btn_open_dir)

        self.btn_refresh_dir = QPushButton(parent=self)
        # self.btn_refresh_dir.setText("Refresh Dir")
        self.btn_refresh_dir.setIcon(QIcon(":/toolbox/folder_refresh"))
        self.btn_refresh_dir.setToolTip("Refresh Directory")
        self.v_layout.addWidget(self.btn_refresh_dir)

        self.v_layout.addStretch()