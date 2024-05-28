from mot_toolkit.datatype.common.object_annotation import ObjectAnnotation


class RectDataAnnotation(ObjectAnnotation):
    x1: float
    y1: float

    x2: float
    y2: float

    width: float
    height: float

    def __init__(self, label: str = ""):
        super().__init__(label)

        self.x1 = 0
        self.y1 = 0

        self.x2 = 0
        self.y2 = 0

    @property
    def x(self):
        return self.x1

    @property
    def y(self):
        return self.y1

    @property
    def center_x(self):
        return (self.x1 + self.x2) / 2

    @property
    def center_y(self):
        return (self.y1 + self.y2) / 2

    @property
    def width(self):
        return self.x2 - self.x1

    @width.setter
    def width(self, value):
        self.x2 = self.x1 + value

    @property
    def height(self):
        return self.y2 - self.y1

    @height.setter
    def height(self, value):
        self.y2 = self.y1 + value

    def set_by_position_and_size(
            self,
            x: float, y: float,
            width: float, height: float
    ):
        self.x1 = x
        self.y1 = y

        self.x2 = x + width
        self.y2 = y + height

    def set_by_rect_two_point(
            self,
            x1: float, y1: float,
            x2: float, y2: float
    ):
        self.x1 = min(x1, x2)
        self.y1 = min(y1, y2)

        self.x2 = max(x1, x2)
        self.y2 = max(y1, y2)

    def get_rect_two_point(self):
        return [
            [self.x1, self.y1],
            [self.x2, self.y2]
        ]

    def set_by_center_and_size(
            self,
            center_x: float, center_y: float,
            width: float, height: float
    ):
        self.x1 = center_x - width / 2
        self.y1 = center_y - height / 2

        self.x2 = center_x + width / 2
        self.y2 = center_y + height / 2

    def set_by_yolo_format(
            self,
            image_width: float, image_height: float,

            center_x_ratio: float, center_y_ratio: float,
            width_ratio: float, height_ratio: float
    ):
        center_x = image_width * center_x_ratio
        center_y = image_height * center_y_ratio

        width = image_width * width_ratio
        height = image_height * height_ratio

        self.set_by_center_and_size(center_x, center_y, width, height)

    def fix_bugs(self):
        if self.x1 > self.x2:
            self.x1, self.x2 = self.x2, self.x1
        if self.y1 > self.y2:
            self.y1, self.y2 = self.y2, self.y1

        if self.x1 < 0:
            self.x1 = 0
        if self.y1 < 0:
            self.y1 = 0

    def __str__(self):
        return (
            f"RectDataAnnotation("
            f"label={self.label}, "
            f"x1={self.x1}, "
            f"y1={self.y1}, "
            f"x2={self.x2}, "
            f"y2={self.y2}, "
            f"width={self.width}, "
            f"height={self.height}"
            f")"
        )
