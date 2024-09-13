from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QLabel, QSizePolicy, QVBoxLayout

from mot_toolkit.gui.view.components. \
    widget.rect.image_rect import ImageRect
from mot_toolkit.gui.view.components. \
    widget.rect.rect_thumbnail import RectThumbnail
from mot_toolkit.gui.view.components. \
    window.base_q_widget import BaseQWidget


class DetailWidget(BaseQWidget):
    image_rect: ImageRect

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__setup_widget_properties()

        self.__init_widgets()

    def __setup_widget_properties(self):
        pass

    def __init_widgets(self):
        self.image_rect = ImageRect(parent=self)
        self.image_rect.slot_update.connect(self.update)

        self.v_layout = QVBoxLayout()
        self.setLayout(self.v_layout)

        label_title = QLabel(parent=self)
        label_title.setText("Detail:")
        self.v_layout.addWidget(label_title)

        self.label_image_size = QLabel(parent=self)
        self.label_image_size.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.v_layout.addWidget(self.label_image_size)

        self.rect_thumbnail = RectThumbnail(
            image_rect=self.image_rect,
            parent=self
        )
        self.rect_thumbnail.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        # self.rect_thumbnail.setFixedSize(200, 200)
        self.v_layout.addWidget(self.rect_thumbnail)

    def update(self):
        super().update()

        size_str = f"{self.image_rect.img_width}x{self.image_rect.img_height}"
        self.label_image_size.setText(size_str)
        self.label_image_size.setVisible(self.image_rect.check_is_valid())

        self.rect_thumbnail.update()


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    widget = DetailWidget()

    widget.image_rect.img_width = 800
    widget.image_rect.img_height = 600

    widget.image_rect.rect_x = 100
    widget.image_rect.rect_y = 100
    widget.image_rect.rect_width = 200
    widget.image_rect.rect_height = 200

    widget.update()

    widget.show()

    sys.exit(app.exec())
