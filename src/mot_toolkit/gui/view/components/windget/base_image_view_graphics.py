import sys
from enum import EnumType

from PySide6.QtCore import Qt, QEvent, Signal, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsView,
    QGraphicsScene, QPinchGesture
)

from mot_toolkit.utils. \
    image.stylization.image_sobel import (
    sobel_edge_detection_q_pixmap,
    sobel_edge_detection_binary_q_pixmap
)


class ImageDisplayType(EnumType):
    Original = 0
    Outline = 1
    OutlineBinary = 2
    Adjustment = 3


class ImageViewGraphics(QGraphicsView):
    slot_image_changed: Signal = Signal()
    slot_image_scale_factor_changing: Signal = Signal(float)
    slot_image_scale_factor_changed_and_displayed: Signal = Signal(float)

    # 双指外扩(放大)为正，双指内缩(缩小)为负
    # Two-finger expansion (zoom in) is positive(+),
    # two-finger contraction (zoom out) is negative(-)
    pinch_triggered: Signal = Signal(float)

    # 顺时针为负，逆时针为正
    # Clockwise is negative(-)
    # counterclockwise is positive(+)
    rotate_triggered: Signal = Signal(float)

    __image_display_type: ImageDisplayType = 0
    __outline_binary_threshold: int = 127

    __last_scale_factor: float = 1.0

    def __init__(self, parent=None):
        super().__init__(parent)

        self.grabGesture(Qt.GestureType.PinchGesture)

        self.scene = QGraphicsScene()
        # self.scene.setSceneRect(-5000, -5000, 10000, 10000)
        # self.scene.addRect(0, 0, 100, 100, QPen(Qt.NoPen), QBrush(Qt.green))

        self.setScene(self.scene)

        self.__scale_factor = 1.0

        self.image: QPixmap | None = None
        self.image_display: QPixmap | None = None

        self.__setup_widget_properties()

    def __setup_widget_properties(self):
        # Disable horizontal scroll bar
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Disable vertical scroll bar
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Disable wheel event
        def __disable_wheel_event(event):
            # Block wheel event
            event.ignore()

        self.wheelEvent = __disable_wheel_event

        # Disable interaction
        self.setInteractive(False)

    def scrollContentsBy(self, dx, dy):
        # 阻止滚动内容
        return False

    def event(self, event):
        if event.type() == QEvent.Type.Gesture:
            self.__gesture_event(event)
            return True
        return super().event(event)

    def __gesture_event(self, event: QEvent):
        pinch_gesture = event.gesture(Qt.GestureType.PinchGesture)

        if pinch_gesture:
            self.__pinch_triggered(pinch_gesture)

    def __pinch_triggered(self, gesture):
        if gesture.changeFlags() & QPinchGesture.ChangeFlag.ScaleFactorChanged:
            factor_delta = gesture.totalScaleFactor() - gesture.scaleFactor()
            factor_delta = round(factor_delta, 6)
            self.pinch_triggered.emit(factor_delta)
            # print(
            #     "Scale factor changed",
            #     gesture.scaleFactor(),
            #     gesture.totalScaleFactor(),
            #     gesture.lastScaleFactor()
            # )
            # print("factor_delta", factor_delta)
        if gesture.changeFlags() & QPinchGesture.ChangeFlag.RotationAngleChanged:
            angle_delta = gesture.totalRotationAngle() - gesture.rotationAngle()
            angle_delta = round(angle_delta, 6)
            self.rotate_triggered.emit(angle_delta)
            # print(
            #     "Rotation angle changed",
            #     gesture.rotationAngle(),
            #     gesture.totalRotationAngle(),
            #     gesture.lastRotationAngle()
            # )
            # print("angle_delta", angle_delta)

    def set_image_by_path(self, image_path: str):
        q_pixmap = QPixmap(image_path)

        self.set_image(q_pixmap)

    def set_image(self, image: QPixmap):
        self.image = image

        self.update()

        self.slot_image_changed.emit()

    def get_image(self) -> QPixmap:
        return self.image

    @property
    def scale_factor(self) -> float:
        return self.__scale_factor

    @scale_factor.setter
    def scale_factor(self, value: float):
        self.try_to_set_scale_factor(value=value)

    @property
    def last_scale_factor(self) -> float:
        return self.__last_scale_factor

    def check_new_scale_factor(self, value: float) -> bool:
        new_size = self.calc_new_size(value)
        if new_size.width() < 100 or new_size.height() < 100:
            return False

        return True

    def try_to_set_scale_factor(self, value: float) -> bool:
        # Check NULL Point
        if self.image is None:
            return False

        # Prevent too small
        if not self.check_new_scale_factor(value):
            return False

        self.__scale_factor = value
        self.slot_image_scale_factor_changing.emit(value)
        self.update()

        return True

    def calc_new_size(self, scale_factor: float) -> QSize:
        return QSize(
            int(self.image.width() * scale_factor),
            int(self.image.height() * scale_factor)
        )

    @property
    def image_display_type(self) -> ImageDisplayType:
        return self.__image_display_type

    @image_display_type.setter
    def image_display_type(self, value: ImageDisplayType):
        self.__image_display_type = value
        self.update()

    @property
    def outline_binary_threshold(self) -> int:
        return self.__outline_binary_threshold

    @outline_binary_threshold.setter
    def outline_binary_threshold(self, value: int):
        if value < 0:
            value = 0

        if value > 255:
            value = 255

        self.__outline_binary_threshold = value

        self.update()

    def update(self):
        if self.image is None:
            return

        # Calculate New Size
        # ori_size = self.image.size()
        new_size = self.calc_new_size(self.scale_factor)

        # Generate New Image
        self.image_display = self.image.scaled(new_size)

        if self.scale_factor != self.__last_scale_factor:
            self.__last_scale_factor = self.scale_factor
            self.slot_image_scale_factor_changed_and_displayed.emit(self.scale_factor)

        if self.image_display_type != ImageDisplayType.Original:
            match self.image_display_type:
                case ImageDisplayType.Outline:
                    self.image_display = \
                        sobel_edge_detection_q_pixmap(self.image_display)
                case ImageDisplayType.OutlineBinary:
                    self.image_display = \
                        sobel_edge_detection_binary_q_pixmap(
                            image=self.image_display,
                            binary_threshold=self.outline_binary_threshold
                        )

        # Clear Old Scene
        self.scene.clear()

        # Display Image
        self.scene.addPixmap(self.image_display)

        # Set Scene Size
        self.scene.setSceneRect(
            0, 0,
            new_size.width(), new_size.height()
        )
        self.setFixedSize(new_size)

        super().update()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    view = ImageViewGraphics()
    view.set_image_by_path('../../../../Test/00000000.jpg')
    view.show()

    sys.exit(app.exec())
