from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel, QListWidget
)


class ListWithTitleWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__setup_widget_properties()

        self.__init_widgets()

    def __setup_widget_properties(self):
        pass

    def __init_widgets(self):
        self.v_layout = QVBoxLayout(parent=self)
        self.setLayout(self.v_layout)

        self.label_title = QLabel(parent=self)
        self.label_title.setText("Title")
        self.v_layout.addWidget(self.label_title)

        self.list_widget = QListWidget(parent=self)
        self.v_layout.addWidget(self.list_widget)

    def set_title(self, title: str):
        title_str = title.strip()
        if not title_str.endswith(":"):
            title_str = title_str + ":"

        self.label_title.setText(title_str)

    def get_title(self) -> str:
        return self.label_title.text()
