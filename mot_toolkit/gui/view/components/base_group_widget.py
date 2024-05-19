from PySide6.QtWidgets import (
    QGroupBox,
    QVBoxLayout
)


class BaseGroupWidget(QGroupBox):

    def __init__(self, parent=None, title: str = ""):
        super().__init__(parent=parent)

        if title and len(title) > 0:
            self.setTitle(title)

        self.__setup_widget_properties()

        self.__init_widgets()

    def __setup_widget_properties(self):
        pass

    def __init_widgets(self):
        self.v_layout = QVBoxLayout()
        self.setLayout(self.v_layout)
