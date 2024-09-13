from PySide6.QtWidgets import QWidget


class RectThumbnail(QWidget):
    img_width: int = 0
    img_height: int = 0

    rect_x: int = 0
    rect_y: int = 0
    rect_width: int = 0
    rect_height: int = 0

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__setup_widget_properties()

        self.__init_widgets()

    def __setup_widget_properties(self):
        pass

    def __init_widgets(self):
        pass

    def check_is_valid(self):
        if self.rect_width <= 0 or self.rect_height <= 0:
            return False

        return True

    def check_is_out_of_range(self):
        if self.rect_x + self.rect_width > self.img_width:
            return True
        if self.rect_y + self.rect_height > self.img_height:
            return True

        return False

    def update(self):
        super().update()
