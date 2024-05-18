from mot_toolkit.datatype.object_annotation import ObjectAnnotation


class RectDataAnnotation(ObjectAnnotation):
    x1: int
    y1: int

    x2: int
    y2: int

    width: int
    height: int

    def __init__(self, label: str = ""):
        super().__init__(label)

        self.x1 = 0
        self.y1 = 0

        self.x2 = 0
        self.y2 = 0

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
            x: int, y: int,
            width: int, height: int
    ):
        self.x1 = x
        self.y1 = y

        self.x2 = x + width
        self.y2 = y + height

    def set_by_rect_two_point(
            self,
            x1: int, y1: int,
            x2: int, y2: int
    ):
        self.x1 = min(x1, x2)
        self.y1 = min(y1, y2)

        self.x2 = max(x1, x2)
        self.y2 = max(y1, y2)

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
            f"x={self.x1}, "
            f"y={self.y1}, "
            f"width={self.width}, "
            f"height={self.height}"
            f")"
        )
