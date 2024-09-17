from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel

from mot_toolkit.gui.view.components.widget.basic.draggable_progressbar import DraggableProgressBar


class DraggableProgressbarWithText(QWidget):
    slot_on_value_changed: Signal = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.__setup_widget_properties()

        self.__init_widgets()

    def __setup_widget_properties(self):
        pass

    def __init_widgets(self):
        self.h_layout = QHBoxLayout()
        self.setLayout(self.h_layout)

        self.progressbar = DraggableProgressBar(parent=self)
        self.progressbar.valueChanged.connect(self.__on_value_changed)
        self.h_layout.addWidget(self.progressbar)

        self.label = QLabel(parent=self)
        self.__on_value_changed(self.progressbar.value())
        self.h_layout.addWidget(self.label)

    def __on_value_changed(self, value: int):
        value = int(round(value, 0))
        self.label.setText(str(value))
        self.slot_on_value_changed.emit(value)

    @property
    def min(self) -> int:
        return self.progressbar.min

    @min.setter
    def min(self, value: int):
        value = int(round(value, 0))
        self.progressbar.min = value

    @property
    def max(self) -> int:
        return self.progressbar.max

    @max.setter
    def max(self, value: int):
        value = int(round(value, 0))
        self.progressbar.max = value

    @property
    def value(self) -> int:
        return int(self.progressbar.value())

    @value.setter
    def value(self, value: int):
        value = int(round(value, 0))
        new_value = max(self.min, min(value, self.max))
        self.progressbar.setValue(new_value)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication([])

    widget = DraggableProgressbarWithText()
    widget.show()

    app.exec()
