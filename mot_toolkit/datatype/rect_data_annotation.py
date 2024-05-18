class RectDataAnnotation:
    def __init__(self, label=""):
        self.label = label

        self.x1 = 0
        self.y1 = 0

        self.x2 = 0
        self.y2 = 0

        self.width = 0
        self.height = 0

    def set_label(self, label):
        self.label = label

    def set_by_position_and_size(self, x, y, width, height):
        self.x1 = x
        self.y1 = y

        self.x2 = x + width
        self.y2 = y + height

        self.width = width
        self.height = height

    def set_by_rect_two_point(self, x1, y1, x2, y2):
        self.x1 = min(x1, x2)
        self.y1 = min(y1, y2)

        self.x2 = max(x1, x2)
        self.y2 = max(y1, y2)

        self.width = abs(x2 - x1)
        self.height = abs(y2 - y1)

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
