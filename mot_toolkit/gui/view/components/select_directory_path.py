import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QSizePolicy,
)


class SelectDirectoryPathWidget(QGroupBox):

    def __init__(self):
        super().__init__()

        self.__init_widgets()

        self.__init_drag()

    def __init_widgets(self):
        size_policy = QSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Fixed
        )
        self.setSizePolicy(size_policy)

        self.v_layout = QVBoxLayout()

        self.top_label = QLabel(parent=self)
        self.top_label.setText("Select Directory Path:")
        self.v_layout.addWidget(self.top_label)

        self.path_h_layout = QHBoxLayout()

        self.path_line_edit = QLineEdit(parent=self)
        self.path_line_edit.setMinimumWidth(200)
        self.path_line_edit.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.path_line_edit.setPlaceholderText("Select/Input a directory path")
        self.path_line_edit.textChanged.connect(self.__line_edit_text_changed)
        self.path_h_layout.addWidget(self.path_line_edit)

        self.select_path_button = QPushButton(parent=self)
        self.select_path_button.setText("...")
        self.select_path_button.setFixedWidth(30)
        self.select_path_button.clicked.connect(
            self.__button_select_path_clicked
        )
        self.path_h_layout.addWidget(self.select_path_button)

        self.v_layout.addLayout(self.path_h_layout)

        self.setLayout(self.v_layout)

    def __init_drag(self):
        def drag_enter_event(event):
            if (
                    event.mimeData().hasUrls() and
                    all(
                        url.isLocalFile()
                        for url in event.mimeData().urls()
                    )
            ):
                event.acceptProposedAction()

        def drag_move_event(event):
            if event.mimeData().hasUrls():
                event.acceptProposedAction()

        def drop_event(event):
            for url in event.mimeData().urls():
                folder_path = url.toLocalFile()
                print(folder_path)
            event.acceptProposedAction()

        self.setAcceptDrops(True)
        self.dragEnterEvent = drag_enter_event
        self.dragMoveEvent = drag_move_event
        self.dropEvent = drop_event

    def __button_select_path_clicked(self):
        current_dir = self.get_path()
        if len(current_dir) == 0:
            current_dir = "."

        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory", current_dir,
            (
                    QFileDialog.Option.ShowDirsOnly |
                    QFileDialog.Option.DontResolveSymlinks
            )
        )

        # If user selected a directory
        if directory and os.path.isdir(directory):
            self.path_line_edit.setText(directory)

    def check_path_is_valid(self):
        return os.path.isdir(self.path_line_edit.text())

    def __line_edit_text_changed(self):
        self.path_line_edit.setStyleSheet(
            "border: 1px solid green;"
            if self.check_path_is_valid()
            else "border: 1px solid red;"
        )

    def get_path(self):
        if self.check_path_is_valid():
            return self.path_line_edit.text()
        return ""

    def get_absolute_path(self):
        path = self.get_path()
        if path == "":
            return ""
        else:
            return os.path.abspath(path)
