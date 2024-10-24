path = "/mnt/h/Datasets/TrackShipOnlineVideo/sea_video_20240313_part4/OnshoreTL/BV18t4y1N7xW-NCzsi9qAknPVr9iI/00000000-00000291/00000000.jpg"

import cv2
import numpy as np


def canny_edge_detection(image, gaussian_kernel_size=5, low_threshold=50, high_threshold=150):
    """
    使用Canny算法进行边缘检测。

    :param image: 输入的灰度图像
    :param low_threshold: 低阈值
    :param high_threshold: 高阈值
    :return: 边缘检测结果
    """
    # 1. 高斯模糊
    blurred = cv2.GaussianBlur(image, (gaussian_kernel_size, gaussian_kernel_size), 0)

    # 2. 应用Canny边缘检测
    edges = cv2.Canny(blurred, low_threshold, high_threshold)

    # Sobel
    # sobelx = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
    # sobely = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)
    # magnitude = np.sqrt(sobelx ** 2 + sobely ** 2)
    # edges = np.uint8(magnitude)

    return edges


def multi_scale_canny(image, low_threshold=50, high_threshold=150):
    """ 多尺度Canny边缘检测 """
    combined_edges = np.zeros_like(image, dtype=np.uint8)
    for scale in [3, 5, 7]:
        edges = canny_edge_detection(image, scale, low_threshold, high_threshold)

        # Resize
        edges = cv2.resize(edges, (image.shape[1], image.shape[0]))

        combined_edges = cv2.bitwise_or(combined_edges, edges)
    return combined_edges


# 读取图像
image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)

if image is None:
    print("Error: Could not load image.")
else:
    # 应用Canny边缘检测
    edges = canny_edge_detection(image, low_threshold=50, high_threshold=150)

    # 显示结果
    # cv2.imshow('Original Image', image)
    cv2.imshow('Edges', edges)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
