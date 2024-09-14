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

    @property
    def rect_x1(self) -> int:
        return self.rect_x

    @rect_x1.setter
    def rect_x1(self, value: int):
        self.rect_x = value

    @property
    def rect_y1(self) -> int:
        return self.rect_y

    @rect_y1.setter
    def rect_y1(self, value: int):
        self.rect_y = value

    @property
    def rect_x2(self) -> int:
        return self.rect_x + self.rect_width

    @rect_x2.setter
    def rect_x2(self, value: int):
        self.rect_x = value - self.rect_width

    @property
    def rect_y2(self) -> int:
        return self.rect_y + self.rect_height

    @rect_y2.setter
    def rect_y2(self, value: int):
        self.rect_y = value - self.rect_height

    @property
    def rect_top(self) -> int:
        return self.rect_y1

    @rect_top.setter
    def rect_top(self, value: int):
        self.rect_y1 = value

    @property
    def rect_bottom(self) -> int:
        return self.rect_y2

    @rect_bottom.setter
    def rect_bottom(self, value: int):
        self.rect_y2 = value

    @property
    def rect_left(self) -> int:
        return self.rect_x1

    @rect_left.setter
    def rect_left(self, value: int):
        self.rect_x1 = value

    @property
    def rect_right(self) -> int:
        return self.rect_x2

    @rect_right.setter
    def rect_right(self, value: int):
        self.rect_x2 = value

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
