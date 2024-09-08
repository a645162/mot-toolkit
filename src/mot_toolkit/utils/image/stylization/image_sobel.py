from PySide6.QtGui import QImage, QPixmap

import cv2

from mot_toolkit.utils.image.qt_opencv import q_image_to_opencv, opencv_to_q_image


def sobel_edge_detection(image):
    """
    Perform edge detection on an image using the Sobel operator and return the edge map.

    :param image: Input image pixel array (NumPy array).
    :return: Image pixel array after edge detection (NumPy array).
    """
    # Ensure the input image is a grayscale image
    if len(image.shape) == 3:  # If the image is in color
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur
    image = cv2.GaussianBlur(image, (3, 3), 0)

    # Apply the Sobel operator
    sobel_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)

    # Calculate the magnitude of the gradients
    abs_sobel_x = cv2.convertScaleAbs(sobel_x)
    abs_sobely = cv2.convertScaleAbs(sobel_y)

    # Combine gradients from both directions
    edges = cv2.addWeighted(abs_sobel_x, 0.5, abs_sobely, 0.5, 0)

    return edges


def sobel_edge_detection_q_image(image: QImage) -> QImage:
    # Convert QImage to NumPy array
    image_np = q_image_to_opencv(image)

    # Apply Sobel edge detection
    edges_np = sobel_edge_detection(image_np)

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
    edges_np = sobel_edge_detection(image_np)

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

    # Apply Sobel edge detection
    edges_q_image = sobel_edge_detection_binary_q_image(
        image=image_q_image,
        binary_threshold=binary_threshold
    )

    return QPixmap.fromImage(edges_q_image)
