from PySide6.QtGui import QImage, QPixmap
import cv2
import numpy as np


def q_image_to_opencv(q_image, output_channels=3) -> np.ndarray:
    """
    Convert a QImage to an OpenCV image (numpy array).

    :param q_image: The QImage to convert.
    :param output_channels: Number of output channels (3 for BGR, 4 for BGRA).
    :return: Numpy array representing the OpenCV image.
    """
    # Convert QImage to the appropriate format that matches OpenCV's BGR or BGRA format
    q_image = q_image.convertToFormat(QImage.Format.Format_RGBA8888)

    # Get the image data
    ptr = q_image.constBits()
    original_arr = np.array(ptr).copy()
    arr = \
        original_arr.reshape(
            q_image.height(), q_image.width(),
            4
        )

    # Convert RGBA to BGRA
    arr = arr[:, :, [2, 1, 0, 3]]

    # Channel
    if output_channels == 3:
        arr = arr[:, :, :3]

    return arr


def opencv_to_q_image(cv_image) -> QImage:
    """
    Convert an OpenCV image (numpy array) to a QImage.

    :param cv_image: The OpenCV image to convert.
    :return: QImage object.
    """

    # Check Shape is 2 dim(Gray)
    if len(cv_image.shape) == 2:
        # Convert to 3 dim
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_GRAY2BGR)

    # Check the number of channels and convert BGR to RGB if necessary
    if cv_image.shape[2] == 3:
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        q_format = QImage.Format.Format_RGB888
    elif cv_image.shape[2] == 4:
        cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGBA)
        q_format = QImage.Format.Format_RGBA8888
    else:
        raise ValueError("Unsupported number of channels. Image should have 3 (BGR) or 4 (BGRA) channels.")

    # Convert NumPy array to QImage
    height, width, channels = cv_image.shape
    bytes_per_line = channels * width
    q_image = QImage(
        cv_image.data,
        width, height,
        bytes_per_line,
        q_format
    )

    return q_image


def opencv_to_q_pixmap(cv_image) -> QPixmap:
    return QPixmap.fromImage(opencv_to_q_image(cv_image))


def q_pixmap_to_opencv(q_pixmap: QPixmap, output_channels: int = 3):
    return q_image_to_opencv(
        q_image=q_pixmap.toImage(),
        output_channels=output_channels
    )


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Load Test Image
    img_4_channel = cv2.imread("./Test/Logo.png", cv2.IMREAD_UNCHANGED)

    # Check is 4-Channel Image
    if img_4_channel.shape[2] == 4:
        print("4-Channel Image")
    else:
        print("Not 4-Channel Image")
        exit(1)

    # Convert to 3-Channel Image
    img_3_channel = cv2.cvtColor(img_4_channel, cv2.COLOR_BGRA2BGR)

    # Convert OpenCV to QImage
    q_image_4_channel = opencv_to_q_image(img_4_channel)
    q_image_3_channel = opencv_to_q_image(img_3_channel)

    # Convert OpenCV to QPixmap
    q_pixmap_4_channel = opencv_to_q_pixmap(img_4_channel)
    q_pixmap_3_channel = opencv_to_q_pixmap(img_3_channel)

    # Convert QImage back to OpenCV
    q_image_4_channel_back = q_image_to_opencv(q_image_4_channel, output_channels=4)
    q_image_3_channel_back = q_image_to_opencv(q_image_3_channel, output_channels=3)

    # Convert QPixmap back to OpenCV
    q_pixmap_4_channel_back = q_pixmap_to_opencv(q_pixmap_4_channel, output_channels=4)
    q_pixmap_3_channel_back = q_pixmap_to_opencv(q_pixmap_3_channel, output_channels=3)

    cv2.imshow("Original Image", img_4_channel)
    cv2.imshow("3-Channel Image", img_3_channel)

    cv2.imshow("QImage 4-Channel", q_image_4_channel_back)
    cv2.imshow("QImage 3-Channel", q_image_3_channel_back)

    cv2.imshow("QPixmap 4-Channel", q_pixmap_4_channel_back)
    cv2.imshow("QPixmap 3-Channel", q_pixmap_3_channel_back)

    cv2.waitKey(0)
