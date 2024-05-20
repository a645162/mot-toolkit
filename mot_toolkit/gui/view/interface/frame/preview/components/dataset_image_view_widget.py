from PySide6.QtCore import Signal, Qt

from mot_toolkit.gui.view. \
    components.scroll_image_view import ScrollImageView


class DatasetImageView(ScrollImageView):
    slot_previous_image: Signal
    slot_next_image: Signal

    def __init__(self, parent=None):
        super().__init__()

        self.__setup_widget_properties()

    def __setup_widget_properties(self):
        pass

    def __init_shortcut(self):
        pass

    def keyPressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.NoModifier:
            if event.key() == Qt.Key.Key_A:
                self.slot_previous_image.emit()
                return
            elif event.key() == Qt.Key.Key_D:
                self.slot_next_image.emit()
                return

        super().keyPressEvent(event)
