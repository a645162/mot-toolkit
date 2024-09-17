import os.path

import cv2
import numpy as np
from PySide6.QtGui import QImage, QPixmap

from mot_toolkit.utils.image.qt_opencv import (
    q_image_to_opencv,
    opencv_to_q_image
)

from mot_toolkit.config import program_path


def adjust_brightness_contrast(
        img: np.ndarray,
        brightness: int = 0,
        contrast: int = 0
):
    # Check if brightness and contrast are within the range of 0-100
    if brightness < 0 or brightness > 100 or contrast < 0 or contrast > 100:
        raise ValueError("Brightness and contrast values must be in the range [0, 100].")

    # Map brightness and contrast from [0, 100] range to [0, 2] range
    alpha = (contrast / 50.0) + 1.0  # Contrast adjustment factor
    beta = (brightness - 50) * 2.55  # Brightness adjustment factor, mapping 0-100 to 0-255

    # Adjust brightness and contrast
    adjusted = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)

    return adjusted


def adjust_brightness_contrast_q_image(
        image: QImage,
        brightness: int = 0,
        contrast: int = 0
) -> QImage:
    # Convert QImage to NumPy array
    image_np = q_image_to_opencv(image)

    # Adjust brightness and contrast
    adjusted_np = adjust_brightness_contrast(image_np, brightness, contrast)

    # Convert NumPy array to QImage
    result_q_image = opencv_to_q_image(adjusted_np)

    return result_q_image


def adjust_brightness_contrast_q_pixmap(
        image: QImage,
        brightness: int = 0,
        contrast: int = 0
):
    result_q_pixmap = \
        adjust_brightness_contrast_q_image(
            image,
            brightness,
            contrast
        )

    return QPixmap.fromImage(result_q_pixmap)


if __name__ == '__main__':
    # Resources/PySide6/Logo/Logo.png
    image_path = os.path.join(
        program_path.path_project,
        "Resources",
        "PySide6",
        "Logo",
        "Logo.png"
    )
    img = cv2.imread(image_path)

    brightness = 70  # 增加亮度
    contrast = 80  # 增加对比度

    # 调整图像亮度和对比度
    adjusted_image = adjust_brightness_contrast(img, brightness, contrast)

    cv2.imshow("Original Image", img)
    cv2.imshow("Adjusted Image", adjusted_image)
    cv2.waitKey()
    cv2.destroyAllWindows()
