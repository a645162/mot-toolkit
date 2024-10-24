import cv2
import numpy as np


def gaussian_blur(
        image: np.ndarray,
        kernel_size: int = 3
) -> np.ndarray:
    """
    Apply Gaussian blur to an image using the specified kernel size.

    :param image: Input image pixel array (NumPy array).
    :param kernel_size: Size of the Gaussian kernel.
    :return: Image pixel array after Gaussian blur (NumPy array).
    """
    return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)


def apply_morphology(image, kernel_size=5, erosion_iterations=1, dilation_iterations=1):
    """
    Apply morphological operations (erosion and dilation) to the input image.

    :param image: Input grayscale or color image.
    :param kernel_size: Size of the structuring element.
    :param erosion_iterations: Number of iterations for erosion.
    :param dilation_iterations: Number of iterations for dilation.
    :return: Processed image after applying erosion and dilation.
    """

    # Ensure the input image is a grayscale image
    if len(image.shape) == 3:  # If the image is in color
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Define the structuring element
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))

    # Apply erosion
    eroded = cv2.erode(image, kernel, iterations=erosion_iterations)

    # Apply dilation
    dilated = cv2.dilate(eroded, kernel, iterations=dilation_iterations)

    return dilated
