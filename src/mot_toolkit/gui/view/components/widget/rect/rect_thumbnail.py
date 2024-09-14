from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QPen, QColor
from PySide6.QtWidgets import QWidget

from mot_toolkit.gui.view.components.widget.rect.image_rect import ImageRect


class RectThumbnail(QWidget):
    image_rect: ImageRect

    def __init__(self, image_rect: ImageRect = None, parent=None):
        super().__init__(parent=parent)

        if image_rect is not None:
            self.image_rect = image_rect
        else:
            self.image_rect = ImageRect(parent=self)

        self.__setup_widget_properties()

        self.__init_widgets()

    def __setup_widget_properties(self):
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def __init_widgets(self):
        pass

    def check_is_valid(self):
        if self.image_rect.img_width <= 0 or self.image_rect.img_height <= 0:
            return False

        return True

    def check_is_out_of_range(self):
        if self.image_rect.rect_x < 0:
            return True
        if self.image_rect.rect_y < 0:
            return True
        if self.image_rect.rect_x + self.image_rect.rect_width > self.image_rect.img_width:
            return True
        if self.image_rect.rect_y + self.image_rect.rect_height > self.image_rect.img_height:
            return True

        return False

    def paintEvent(self, event):
        super().paintEvent(event)

        if not self.check_is_valid():
            return

        # img_border_width = 10
        img_border_color = Qt.GlobalColor.black
        img_fill_color = QColor(200, 200, 200)
        img_opacity = 1.0

        rect_border_width = 5
        rect_border_color = Qt.GlobalColor.red
        rect_fill_color = Qt.GlobalColor.green
        rect_opacity = 0.5

        if self.check_is_out_of_range():
            rect_border_color = Qt.GlobalColor.green
            rect_fill_color = Qt.GlobalColor.red

        ratio = min(
            self.width() / self.image_rect.img_width,
            self.height() / self.image_rect.img_height
        )

        img_width = int(self.image_rect.img_width * ratio)
        img_height = int(self.image_rect.img_height * ratio)

        rect_x = int(self.image_rect.rect_x * ratio)
        rect_y = int(self.image_rect.rect_y * ratio)
        rect_width = int(self.image_rect.rect_width * ratio)
        rect_height = int(self.image_rect.rect_height * ratio)

        start_x = int(
            (self.width() - img_width) / 2
        )
        start_y = int(
            (self.height() - img_height) / 2
        )

        painter = QPainter(self)

        painter.setPen(QPen(img_border_color))
        painter.setBrush(img_fill_color)
        painter.setOpacity(img_opacity)
        painter.drawRect(
            QRect(
                start_x,
                start_y,
                img_width,
                img_height
            )
        )

        painter.setPen(QPen(rect_border_color, rect_border_width))
        painter.setBrush(rect_fill_color)
        painter.setOpacity(rect_opacity)
        painter.drawRect(
            QRect(
                start_x + rect_x,
                start_y + rect_y,
                rect_width,
                rect_height
            )
        )

        painter.end()

    def update(self):
        super().update()

        self.repaint()


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    widget = RectThumbnail()
    widget.resize(400, 400)
    widget.show()

    widget.image_rect.img_width = 800
    widget.image_rect.img_height = 600

    widget.image_rect.rect_x = 100
    widget.image_rect.rect_y = 100
    widget.image_rect.rect_width = 200
    widget.image_rect.rect_height = 200

    sys.exit(app.exec())
