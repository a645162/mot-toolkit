from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout
)


class ToolkitWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__setup_widget_properties()

        self.__init_widgets()

    def __setup_widget_properties(self):
        pass

    def __init_widgets(self):
        self.v_layout = QVBoxLayout(parent=self)
        self.setLayout(self.v_layout)
