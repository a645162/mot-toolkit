from PySide6.QtCore import QObject, Signal


class ImageRect(QObject):
    __img_width: int = 0
    __img_height: int = 0

    __rect_x: int = 0
    __rect_y: int = 0
    __rect_width: int = 0
    __rect_height: int = 0

    slot_update: Signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)

    @property
    def img_width(self) -> int:
        return self.__img_width

    @img_width.setter
    def img_width(self, value: int):
        if value < 0:
            value = 0
        self.__img_width = value
        self.update()

    @property
    def img_height(self) -> int:
        return self.__img_height

    @img_height.setter
    def img_height(self, value: int):
        if value < 0:
            value = 0
        self.__img_height = value
        self.update()

    @property
    def rect_x(self) -> int:
        return self.__rect_x

    @rect_x.setter
    def rect_x(self, value: int):
        self.__rect_x = value
        self.update()

    @property
    def rect_y(self) -> int:
        return self.__rect_y

    @rect_y.setter
    def rect_y(self, value: int):
        self.__rect_y = value
        self.update()

    @property
    def rect_width(self) -> int:
        return self.__rect_width

    @rect_width.setter
    def rect_width(self, value: int):
        if value < 0:
            value = 0
        self.__rect_width = value
        self.update()

    @property
    def rect_height(self) -> int:
        return self.__rect_height

    @rect_height.setter
    def rect_height(self, value: int):
        if value < 0:
            value = 0
        self.__rect_height = value
        self.update()

    rect_w = rect_width
    rect_h = rect_height

    def set_rect(
            self,
            x: int, y: int,
            width: int, height: int
    ):
        self.rect_x = x
        self.rect_y = y
        self.rect_width = width
        self.rect_height = height

    def set_q_rect(self, rect):
        self.rect_x = rect.x()
        self.rect_y = rect.y()
        self.rect_width = rect.width()
        self.rect_height = rect.height()

    def __str__(self):
        return (
            f"ImageRect: ["
            f"img_width: {self.img_width}, "
            f"img_height: {self.img_height}, "
            f"rect_x: {self.rect_x}, "
            f"rect_y: {self.rect_y}, "
            f"rect_width: {self.rect_width}, "
            f"rect_height: {self.rect_height}]"
        )

    def update_by(self, other: "ImageRect"):
        self.img_width = other.img_width
        self.img_height = other.img_height

        self.rect_x = other.rect_x
        self.rect_y = other.rect_y
        self.rect_width = other.rect_width
        self.rect_height = other.rect_height

        self.update()

    def check_is_valid(self) -> bool:
        if self.rect_width <= 0 or self.rect_height <= 0:
            return False

        return True

    def update(self):
        self.slot_update.emit()
