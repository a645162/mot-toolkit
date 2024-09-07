from PySide6.QtGui import QImage, QPixmap

import cv2
import numpy as np

from mot_toolkit.utils.image.qt_opencv import q_image_to_opencv, opencv_to_q_image


def sobel_edge_detection(image):
    """
    使用 Sobel 算子对图像进行边缘检测，并返回边缘图。

    :param image: 输入的图像像素数组（NumPy 数组）。
    :return: 边缘检测后的图像像素数组（NumPy 数组）。
    """
    # 确保输入图像为灰度图像
    if len(image.shape) == 3:  # 如果是彩色图像
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 应用 Sobel 算子
    sobelx = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)

    # 计算梯度幅度
    abs_sobelx = cv2.convertScaleAbs(sobelx)
    abs_sobely = cv2.convertScaleAbs(sobely)

    # 合并两个方向的梯度
    edges = cv2.addWeighted(abs_sobelx, 0.5, abs_sobely, 0.5, 0)

    return edges


def sobel_edge_detection_q_image(image: QImage) -> QImage:
    # Convert QImage to NumPy array
    image_np = q_image_to_opencv(image)

    # Apply Sobel edge detection
    edges_np = sobel_edge_detection(image_np)

    # _, binary_image = cv2.threshold(edges_np, 127, 255, cv2.THRESH_BINARY)

    # Convert NumPy array to QImage
    result_q_image = opencv_to_q_image(edges_np)

    return result_q_image


def sobel_edge_detection_q_pixmap(image: QPixmap) -> QPixmap:
    # Convert QPixmap to QImage
    image_q_image = image.toImage()

    # Apply Sobel edge detection
    edges_q_image = sobel_edge_detection_q_image(image_q_image)

    return QPixmap.fromImage(edges_q_image)
