from typing import List

import numpy as np
from PySide6.QtGui import QImage, QPixmap

import cv2

from mot_toolkit.utils.image.process import image_before_edge
from mot_toolkit.utils.image.qt_opencv import (
    q_image_to_opencv,
    opencv_to_q_image
)


def sobel_edge_detection(
        image: np.ndarray,
        gaussian_kernel_size: int = 3,
        sobel_kernel_size: int = 3
) -> np.ndarray:
    """
    Perform edge detection on an image using the Sobel operator and return the edge map.

    :param image: Input image pixel array (NumPy array).
    :param gaussian_kernel_size: Size of the Gaussian kernel for blurring the image.
    :param sobel_kernel_size: Size of the Sobel kernel for edge detection.
    :return: Image pixel array after edge detection (NumPy array).
    """
    # Ensure the input image is a grayscale image
    if len(image.shape) == 3:  # If the image is in color
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    if gaussian_kernel_size % 2 == 1:
        gaussian_kernel = (gaussian_kernel_size, gaussian_kernel_size)

        # Apply Gaussian blur
        image = cv2.GaussianBlur(image, gaussian_kernel, 0)

    # Apply the Sobel operator
    # ksize = 3
    ksize = sobel_kernel_size
    sobel_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=ksize)
    sobel_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=ksize)

    # Calculate the magnitude of the gradients
    abs_sobel_x = cv2.convertScaleAbs(sobel_x)
    abs_sobel_y = cv2.convertScaleAbs(sobel_y)

    # Combine gradients from both directions
    edges = cv2.addWeighted(abs_sobel_x, 0.5, abs_sobel_y, 0.5, 0)

    return edges


def multi_scale_sobel(
        image: np.ndarray,
        gaussian_kernel_scales: List[int] | None = None,
        sobel_ksize_scales: List[int] | None = None
) -> np.ndarray:
    if gaussian_kernel_scales is None:
        gaussian_kernel_scales = [3, 5]
    if sobel_ksize_scales is None:
        sobel_ksize_scales = [3]

    # Ensure the input image is a grayscale image
    if len(image.shape) == 3:  # If the image is in color
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    combined_edges: np.ndarray | None = None
    for ksize in sobel_ksize_scales:
        current_image: np.ndarray | None = None

        for scale in gaussian_kernel_scales:
            processed_image = image

            blur_image = image_before_edge.gaussian_blur(processed_image, kernel_size=scale)

            edges = sobel_edge_detection(
                blur_image,
                gaussian_kernel_size=0,
                sobel_kernel_size=ksize
            )
            if current_image is None:
                current_image = edges
            else:
                current_image = cv2.bitwise_or(current_image, edges)

        if combined_edges is None:
            combined_edges = current_image
        else:
            combined_edges = cv2.bitwise_and(combined_edges, current_image)

    return combined_edges


def sobel_edge_detection_q_image(image: QImage) -> QImage:
    # Convert QImage to NumPy array
    image_np = q_image_to_opencv(image)

    # Apply Sobel-edge detection
    edges_np = multi_scale_sobel(
        image_np,
        gaussian_kernel_scales=[3, 5],
        sobel_ksize_scales=[3, 5]
    )

    # Convert NumPy array to QImage
    result_q_image = opencv_to_q_image(edges_np)

    return result_q_image


def sobel_edge_detection_binary_q_image(
        image: QImage,
        binary_threshold: int = 127
) -> QImage:
    # Convert QImage to NumPy array
    image_np = q_image_to_opencv(image)

    # Apply Sobel edge detection
    edges_np = multi_scale_sobel(
        image_np,
        gaussian_kernel_scales=[3, 5],
        sobel_ksize_scales=[3, 5]
    )

    # Convert to binary image
    _, binary_image = cv2.threshold(
        src=edges_np,
        thresh=binary_threshold,
        maxval=255,
        type=cv2.THRESH_BINARY
    )

    # Convert NumPy array to QImage
    result_q_image = opencv_to_q_image(binary_image)

    return result_q_image


def sobel_edge_detection_q_pixmap(image: QPixmap) -> QPixmap:
    # Convert QPixmap to QImage
    image_q_image = image.toImage()

    # Apply Sobel edge detection
    edges_q_image = sobel_edge_detection_q_image(image_q_image)

    return QPixmap.fromImage(edges_q_image)


def sobel_edge_detection_binary_q_pixmap(
        image: QPixmap,
        binary_threshold: int = 127
) -> QPixmap:
    # Convert QPixmap to QImage
    image_q_image = image.toImage()

    # Apply Sobel-edge detection
    edges_q_image = sobel_edge_detection_binary_q_image(
        image=image_q_image,
        binary_threshold=binary_threshold
    )

    return QPixmap.fromImage(edges_q_image)
