from mot_toolkit.datatype.common.object_annotation import ObjectAnnotation


class RectDataAnnotation(ObjectAnnotation):
    x1: float
    y1: float

    x2: float
    y2: float

    width: float
    height: float

    ori_dict: dict

    picture_width: float = 0.0
    picture_height: float = 0.0

    def __init__(self, label: str = ""):
        super().__init__(label)

        self.x1 = 0
        self.y1 = 0

        self.x2 = 0
        self.y2 = 0

        self.ori_dict = {}

    def __copy__(self):
        new_object = RectDataAnnotation(self.label)

        new_object.text = self.text

        new_object.x1 = self.x1
        new_object.y1 = self.y1

        new_object.x2 = self.x2
        new_object.y2 = self.y2

        new_object.ori_dict = {}
        new_object.ori_dict.update(self.ori_dict)

        new_object.picture_width = self.picture_width
        new_object.picture_height = self.picture_height

        return new_object

    @property
    def x(self) -> float:
        return self.x1

    @x.setter
    def x(self, value: float):
        self.x1 = value

    @property
    def y(self) -> float:
        return self.y1

    @y.setter
    def y(self, value: float):
        self.y1 = value

    @property
    def center_x(self) -> float:
        return (self.x1 + self.x2) / 2

    @center_x.setter
    def center_x(self, value: float):
        self.x1 = value - self.width / 2
        self.x2 = value + self.width / 2

    @property
    def center_y(self) -> float:
        return (self.y1 + self.y2) / 2

    @center_y.setter
    def center_y(self, value: float):
        self.y1 = value - self.height / 2
        self.y2 = value + self.height / 2

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @width.setter
    def width(self, value: float):
        self.x2 = self.x1 + value

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @height.setter
    def height(self, value: float):
        self.y2 = self.y1 + value

    @property
    def width_int(self) -> int:
        return int(self.width)

    @width_int.setter
    def width_int(self, value: int):
        self.width = value

    @property
    def height_int(self) -> int:
        return int(self.height)

    @height_int.setter
    def height_int(self, value: int):
        self.height = value

    @property
    def width_ratio(self) -> float:
        if self.picture_width <= 0:
            return 0
        return self.width / self.picture_width

    @width_ratio.setter
    def width_ratio(self, value: float):
        if self.picture_width <= 0:
            return
        self.width = self.picture_width * value

    @property
    def height_ratio(self) -> float:
        if self.picture_height <= 0:
            return 0
        return self.height / self.picture_height

    @height_ratio.setter
    def height_ratio(self, value: float):
        if self.picture_height <= 0:
            return
        self.height = self.picture_height * value

    @property
    def center_x_ratio(self) -> float:
        if self.picture_width <= 0:
            return 0
        return self.center_x / self.picture_width

    @center_x_ratio.setter
    def center_x_ratio(self, value: float):
        if self.picture_width <= 0:
            return
        self.center_x = self.picture_width * value

    @property
    def center_y_ratio(self) -> float:
        if self.picture_height <= 0:
            return 0
        return self.center_y / self.picture_height

    @center_y_ratio.setter
    def center_y_ratio(self, value: float):
        if self.picture_height <= 0:
            return
        self.center_y = self.picture_height * value

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

    def set_rect_two_point_2dim_array(self, rect_two_point_2dim_array):
        self.set_by_rect_two_point(
            rect_two_point_2dim_array[0][0],
            rect_two_point_2dim_array[0][1],
            rect_two_point_2dim_array[1][0],
            rect_two_point_2dim_array[1][1]
        )

    def get_rect_two_point_2dim_array(self):
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

    def fix_bugs(
            self,
            image_width: int = 0,
            image_height: int = 0
    ) -> bool:
        modified = False

        if self.x1 > self.x2:
            self.x1, self.x2 = self.x2, self.x1
            modified = True
        if self.y1 > self.y2:
            self.y1, self.y2 = self.y2, self.y1
            modified = True

        if self.x1 < 0:
            self.x1 = 0
            modified = True
        if self.y1 < 0:
            self.y1 = 0
            modified = True

        if image_width > 0 and image_height > 0:
            if self.x2 > image_width:
                self.x2 = image_width
                modified = True
            if self.y2 > image_height:
                self.y2 = image_height
                modified = True

        return modified

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

    def update_by(self, rect_data_annotation: "RectDataAnnotation"):
        self.x1 = rect_data_annotation.x1
        self.y1 = rect_data_annotation.y1

        self.x2 = rect_data_annotation.x2
        self.y2 = rect_data_annotation.y2
