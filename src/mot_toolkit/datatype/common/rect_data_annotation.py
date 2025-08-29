from typing import List

from mot_toolkit.datatype.common.object_annotation import ObjectAnnotation


class RectDataAnnotation(ObjectAnnotation):
    """
    矩形数据标注类，继承自ObjectAnnotation
    用于表示和处理矩形标注框的数据结构
    """
    # 左上角坐标
    x1: float  # 左上角x坐标
    y1: float  # 左上角y坐标

    # 右下角坐标
    x2: float  # 右下角x坐标
    y2: float  # 右下角y坐标

    # 宽高属性（作为计算属性实现，实际值由x1,y1,x2,y2决定）
    width: float  # 矩形宽度
    height: float  # 矩形高度

    # 原始数据字典，用于存储额外信息
    ori_dict: dict  # 存储原始数据的字典

    # 图片尺寸，用于计算相对比例
    picture_width: float = 0.0   # 图片宽度
    picture_height: float = 0.0  # 图片高度

    def __init__(self, label: str = ""):
        """
        初始化矩形数据标注对象
        
        Args:
            label: 标注类别标签
        """
        super().__init__(label)

        # 初始化坐标为0
        self.x1 = 0
        self.y1 = 0

        self.x2 = 0
        self.y2 = 0

        # 初始化原始数据字典
        self.ori_dict = {}

    def __copy__(self):
        """
        复制当前对象
        
        Returns:
            RectDataAnnotation: 返回当前对象的副本
        """
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
        """
        获取左上角x坐标的属性访问器
        
        Returns:
            float: 返回x1值
        """
        return self.x1

    @x.setter
    def x(self, value: float):
        """
        设置左上角x坐标
        
        Args:
            value: 要设置的x值
        """
        self.x1 = value

    @property
    def y(self) -> float:
        """
        获取左上角y坐标的属性访问器
        
        Returns:
            float: 返回y1值
        """
        return self.y1

    @y.setter
    def y(self, value: float):
        """
        设置左上角y坐标
        
        Args:
            value: 要设置的y值
        """
        self.y1 = value

    @property
    def center_x(self) -> float:
        """
        获取矩形中心x坐标
        
        Returns:
            float: 返回中心点x坐标
        """
        return (self.x1 + self.x2) / 2

    @center_x.setter
    def center_x(self, value: float):
        """
        设置矩形中心x坐标，会相应调整x1和x2
        
        Args:
            value: 要设置的中心点x坐标
        """
        self.x1 = value - self.width / 2
        self.x2 = value + self.width / 2

    @property
    def center_y(self) -> float:
        """
        获取矩形中心y坐标
        
        Returns:
            float: 返回中心点y坐标
        """
        return (self.y1 + self.y2) / 2

    @center_y.setter
    def center_y(self, value: float):
        """
        设置矩形中心y坐标，会相应调整y1和y2
        
        Args:
            value: 要设置的中心点y坐标
        """
        self.y1 = value - self.height / 2
        self.y2 = value + self.height / 2

    @property
    def width(self) -> float:
        """
        获取矩形宽度
        
        Returns:
            float: 返回宽度值
        """
        return self.x2 - self.x1

    @width.setter
    def width(self, value: float):
        """
        设置矩形宽度，会相应调整x2
        
        Args:
            value: 要设置的宽度值
        """
        self.x2 = self.x1 + value

    @property
    def height(self) -> float:
        """
        获取矩形高度
        
        Returns:
            float: 返回高度值
        """
        return self.y2 - self.y1

    @height.setter
    def height(self, value: float):
        """
        设置矩形高度，会相应调整y2
        
        Args:
            value: 要设置的高度值
        """
        self.y2 = self.y1 + value

    @property
    def width_int(self) -> int:
        """
        获取矩形宽度的整数值
        
        Returns:
            int: 返回宽度的整数值
        """
        return int(self.width)

    @width_int.setter
    def width_int(self, value: int):
        """
        设置矩形宽度的整数值
        
        Args:
            value: 要设置的宽度整数值
        """
        self.width = value

    @property
    def height_int(self) -> int:
        """
        获取矩形高度的整数值
        
        Returns:
            int: 返回高度的整数值
        """
        return int(self.height)

    @height_int.setter
    def height_int(self, value: int):
        """
        设置矩形高度的整数值
        
        Args:
            value: 要设置的高度整数值
        """
        self.height = value

    @property
    def width_ratio(self) -> float:
        """
        获取矩形宽度相对于图片宽度的比例(归一化)
        
        Returns:
            float: 返回宽度比例
        """
        if self.picture_width <= 0:
            return 0
        return self.width / self.picture_width

    @width_ratio.setter
    def width_ratio(self, value: float):
        """
        设置矩形宽度相对于图片宽度的比例(归一化)

        Args:
            value: 要设置的宽度比例
        """
        if self.picture_width <= 0:
            return
        self.width = self.picture_width * value

    @property
    def height_ratio(self) -> float:
        """
        获取矩形高度相对于图片高度的比例(归一化)

        Returns:
            float: 返回高度比例
        """
        if self.picture_height <= 0:
            return 0
        return self.height / self.picture_height

    @height_ratio.setter
    def height_ratio(self, value: float):
        """
        设置矩形高度相对于图片高度的比例(归一化)

        Args:
            value: 要设置的高度比例
        """
        if self.picture_height <= 0:
            return
        self.height = self.picture_height * value

    @property
    def center_x_ratio(self) -> float:
        """
        获取矩形中心x坐标相对于图片宽度的比例(归一化)

        Returns:
            float: 返回中心x坐标比例
        """
        if self.picture_width <= 0:
            return 0
        return self.center_x / self.picture_width

    @center_x_ratio.setter
    def center_x_ratio(self, value: float):
        """
        设置矩形中心x坐标相对于图片宽度的比例(归一化)

        Args:
            value: 要设置的中心x坐标比例
        """
        if self.picture_width <= 0:
            return
        self.center_x = self.picture_width * value

    @property
    def center_y_ratio(self) -> float:
        """
        获取矩形中心y坐标相对于图片高度的比例(归一化)

        Returns:
            float: 返回中心y坐标比例
        """
        if self.picture_height <= 0:
            return 0
        return self.center_y / self.picture_height

    @center_y_ratio.setter
    def center_y_ratio(self, value: float):
        """
        设置矩形中心y坐标相对于图片高度的比例(归一化)

        Args:
            value: 要设置的中心y坐标比例
        """
        if self.picture_height <= 0:
            return
        self.center_y = self.picture_height * value

    def get_xyxy_tuple(self) -> tuple:
        """
        获取矩形框的(x1,y1,x2,y2)元组
        
        Returns:
            tuple: 返回(x1,y1,x2,y2)四元组
        """
        return self.x1, self.y1, self.x2, self.y2

    def get_xyxy_list(self) -> List[float]:
        """
        获取矩形框的[x1,y1,x2,y2]列表
        
        Returns:
            List[float]: 返回[x1,y1,x2,y2]列表
        """
        return [self.x1, self.y1, self.x2, self.y2]

    def set_by_position_and_size(
            self,
            x: float, y: float,
            width: float, height: float
    ):
        """
        通过左上角坐标和宽高设置矩形
        
        Args:
            x: 左上角x坐标
            y: 左上角y坐标
            width: 矩形宽度
            height: 矩形高度
        """
        self.x1 = x
        self.y1 = y

        self.x2 = x + width
        self.y2 = y + height

    def set_by_rect_two_point(
            self,
            x1: float, y1: float,
            x2: float, y2: float
    ):
        """
        通过两个点的坐标设置矩形框
        
        Args:
            x1: 第一个点的x坐标
            y1: 第一个点的y坐标
            x2: 第二个点的x坐标
            y2: 第二个点的y坐标
        """
        self.x1 = min(x1, x2)
        self.y1 = min(y1, y2)

        self.x2 = max(x1, x2)
        self.y2 = max(y1, y2)

    def set_rect_two_point_2dim_array(self, rect_two_point_2dim_array):
        """
        通过二维数组设置矩形框的两个点
        
        Args:
            rect_two_point_2dim_array: 二维数组，包含两个点的坐标
        """
        self.set_by_rect_two_point(
            rect_two_point_2dim_array[0][0],
            rect_two_point_2dim_array[0][1],
            rect_two_point_2dim_array[1][0],
            rect_two_point_2dim_array[1][1]
        )

    def get_rect_two_point_2dim_array(self):
        """
        获取矩形框的两个点的二维数组表示
        
        Returns:
            List[List[float]]: 返回二维数组表示的两个点坐标
        """
        return [
            [self.x1, self.y1],
            [self.x2, self.y2]
        ]

    def get_rect_two_point_tuple(self) -> tuple:
        """
        获取矩形框的两个点的元组表示
        
        Returns:
            tuple: 返回两个点的元组表示
        """
        return self.x1, self.y1, self.x2, self.y2

    def get_rect_two_point_tuple_int(self) -> tuple:
        """
        获取矩形框的两个点的整数元组表示
        
        Returns:
            tuple: 返回两个点的整数元组表示
        """
        return int(self.x1), int(self.y1), int(self.x2), int(self.y2)

    def set_by_center_and_size(
            self,
            center_x: float, center_y: float,
            width: float, height: float
    ):
        """
        通过中心点坐标和宽高设置矩形框
        
        Args:
            center_x: 中心点x坐标
            center_y: 中心点y坐标
            width: 矩形宽度
            height: 矩形高度
        """
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
        """
        通过YOLO格式的比例设置矩形框
        
        Args:
            image_width: 图片宽度
            image_height: 图片高度
            center_x_ratio: 中心点x坐标比例
            center_y_ratio: 中心点y坐标比例
            width_ratio: 宽度比例
            height_ratio: 高度比例
        """
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
        """
        修复矩形框的异常情况，例如坐标错误或超出图片范围
        
        Args:
            image_width: 图片宽度
            image_height: 图片高度
        
        Returns:
            bool: 是否进行了修复
        """
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
        """
        获取矩形框的字符串表示
        
        Returns:
            str: 返回矩形框的字符串表示
        """
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
        """
        更新当前矩形框的属性为另一个矩形框的属性
        
        Args:
            rect_data_annotation: 另一个矩形标注对象
        """
        self.x1 = rect_data_annotation.x1
        self.y1 = rect_data_annotation.y1

        self.x2 = rect_data_annotation.x2
        self.y2 = rect_data_annotation.y2

    def get_iou(self, other: "RectDataAnnotation")->float:
        """
        计算与另一个矩形框的IoU(交并比)值
        
        Args:
            other: 另一个矩形标注对象
            
        Returns:
            float: 返回IoU值，范围[0,1]
        """
        from mot_toolkit.dl.utils.value_calc import calculate_iou

        return calculate_iou(
            box1=self.get_xyxy_list(),
            box2=other.get_xyxy_list()
        )
