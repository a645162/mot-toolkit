from PySide6.QtCore import Qt
from PySide6.QtWidgets import QProgressBar


class DraggableProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setMouseTracking(True)
        self.setValue(0)
        self.setRange(0, 100)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            ratio = event.position().x() / self.width()
            if ratio < 0:
                ratio = 0
            if ratio > 1:
                ratio = 1

            new_value: int = int(round(ratio * self.maximum(), 0))

            new_value = max(self.minimum(), min(new_value, self.maximum()))

            self.setValue(new_value)

    @property
    def min(self) -> int:
        return self.minimum()

    @min.setter
    def min(self, value: int):
        self.setMinimum(value)

        if self.value() < value:
            self.setValue(value)

    @property
    def max(self) -> int:
        return self.maximum()

    @max.setter
    def max(self, value: int):
        self.setMaximum(value)

        if self.value() > value:
            self.setValue(value)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication([])

    widget = DraggableProgressBar()
    widget.show()

    app.exec()
