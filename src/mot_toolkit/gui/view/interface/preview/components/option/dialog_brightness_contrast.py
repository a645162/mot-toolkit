from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QVBoxLayout,
    QLabel, QPushButton, QWidget
)

from mot_toolkit.gui.view.components.window. \
    base_q_main_window import BaseQMainWindow
from mot_toolkit.gui.view.components.widget. \
    combination.draggable_progressbar_with_text import DraggableProgressbarWithText


class DialogBrightnessContrast(BaseQMainWindow):
    slot_brightness_changed: Signal = Signal(int)
    slot_contrast_changed: Signal = Signal(int)

    __brightness: int = 50
    __contrast: int = 50

    def __init__(self, parent=None):
        super().__init__(parent)

        self.__setup_widget_properties()

        self.__init_widgets()

    def __setup_widget_properties(self):
        self.setWindowTitle("Brightness and Contrast")

    def __init_widgets(self):
        self.center_widget = QWidget(parent=self)
        self.setCentralWidget(self.center_widget)
        self.v_layout = QVBoxLayout()
        self.center_widget.setLayout(self.v_layout)

        # Brightness
        label_brightness = QLabel(parent=self.center_widget)
        label_brightness.setText("Brightness")
        self.v_layout.addWidget(label_brightness)

        self.brightness_slider = \
            DraggableProgressbarWithText(parent=self.center_widget)
        self.brightness_slider.min = 0
        self.brightness_slider.max = 100
        self.brightness_slider.value = self.brightness
        self.brightness_slider.slot_on_value_changed.connect(
            self.__on_brightness_changed
        )
        self.v_layout.addWidget(self.brightness_slider)

        # Contrast
        label_contrast = QLabel(parent=self.center_widget)
        label_contrast.setText("Contrast")
        self.v_layout.addWidget(label_contrast)

        self.contrast_slider = \
            DraggableProgressbarWithText(parent=self.center_widget)
        self.contrast_slider.min = 0
        self.contrast_slider.max = 100
        self.contrast_slider.value = self.contrast
        self.contrast_slider.slot_on_value_changed.connect(
            self.__on_contrast_changed
        )
        self.v_layout.addWidget(self.contrast_slider)

        # Restore default
        self.btn_restore_default = QPushButton(parent=self.center_widget)
        self.btn_restore_default.setText("Restore Default")
        self.btn_restore_default.clicked.connect(self.restore_default)
        self.v_layout.addWidget(self.btn_restore_default)

    def __on_brightness_changed(self, value: int):
        self.brightness = value

    def __on_contrast_changed(self, value: int):
        self.contrast = value

    @property
    def brightness(self):
        return self.__brightness

    @brightness.setter
    def brightness(self, value):
        self.__brightness = value

        if self.brightness_slider.value != value:
            self.brightness_slider.value = value

        self.slot_brightness_changed.emit(value)

    @property
    def contrast(self):
        return self.__contrast

    @contrast.setter
    def contrast(self, value):
        self.__contrast = value

        if self.contrast_slider.value != value:
            self.contrast_slider.value = value

        self.slot_contrast_changed.emit(value)

    def restore_default(self):
        self.brightness = 50
        self.contrast = 50


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication([])

    dialog = DialogBrightnessContrast()
    dialog.show()

    app.exec()
