from typing import List, Optional
import cv2
import numpy as np
from PySide6.QtGui import QImage, QPixmap


def canny_edge_detection(
        image: np.ndarray,
        gaussian_kernel_size: int = 5,
        low_threshold: int = 50,
        high_threshold: int = 150
) -> np.ndarray:
    """
    Perform edge detection using the Canny algorithm.

    :param image: Input grayscale or color image (will be converted to grayscale if in color).
    :param gaussian_kernel_size: Size of the Gaussian kernel for blurring.
    :param low_threshold: Low threshold for the hysteresis procedure.
    :param high_threshold: High threshold for the hysteresis procedure.
    :return: Edge detection result as a NumPy array.
    """

    # Ensure the input image is a grayscale image
    if len(image.shape) == 3:  # If the image is in color
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 1. Gaussian blur
    blurred = cv2.GaussianBlur(image, (gaussian_kernel_size, gaussian_kernel_size), 0)

    # 2. Apply Canny edge detection
    edges = cv2.Canny(blurred, low_threshold, high_threshold)

    return edges


def multi_scale_canny(
        image: np.ndarray,
        scales: Optional[List[int]] = None,
        low_threshold: int = 50,
        high_threshold: int = 150
) -> np.ndarray:
    """
    Perform multi-scale Canny edge detection.

    :param image: Input grayscale or color image (will be converted to grayscale if in color).
    :param scales: List of Gaussian kernel sizes for different scales. Default is [3, 5, 7].
    :param low_threshold: Low threshold for the hysteresis procedure.
    :param high_threshold: High threshold for the hysteresis procedure.
    :return: Combined edge detection result as a NumPy array.
    """

    # Ensure the input image is a grayscale image
    if len(image.shape) == 3:  # If the image is in color
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if scales is None:
        scales = [3, 5, 7]

    combined_edges = np.zeros_like(image, dtype=np.uint8)
    for scale in scales:
        edges = canny_edge_detection(image, scale, low_threshold, high_threshold)

        # Resize the edges to match the original image size
        edges = cv2.resize(edges, (image.shape[1], image.shape[0]))

        combined_edges = cv2.bitwise_or(combined_edges, edges)
    return combined_edges


def canny_edge_detection_q_image(image: QImage) -> QImage:
    """
    Perform multi-scale Canny edge detection on a QImage and return the result as a QImage.

    :param image: Input QImage.
    :return: Edge detection result as a QImage.
    """

    # Convert QImage to NumPy array
    image_np = q_image_to_opencv(image)

    # Apply multi-scale Canny edge detection
    edges_np = multi_scale_canny(image_np, scales=[3, 5, 7])

    # Convert NumPy array back to QImage
    result_q_image = opencv_to_q_image(edges_np)

    return result_q_image


def canny_edge_detection_q_pixmap(image: QPixmap) -> QPixmap:
    """
    Perform multi-scale Canny edge detection on a QPixmap and return the result as a QPixmap.

    :param image: Input QPixmap.
    :return: Edge detection result as a QPixmap.
    """

    # Convert QPixmap to QImage
    image_q_image = image.toImage()

    # Apply multi-scale Canny edge detection
    edges_q_image = canny_edge_detection_q_image(image_q_image)

    # Convert QImage back to QPixmap
    return QPixmap.fromImage(edges_q_image)
