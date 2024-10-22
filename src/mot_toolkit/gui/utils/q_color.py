from PySide6.QtGui import QColor


def generate_unique_q_colors(n: int) -> list[QColor]:
    """
    Generate a list of n unique QColor objects.

    :param n: int, the number of unique colors to generate. Must be greater than 0.
    :return: list[QColor], a list containing n unique QColor objects.
    """
    if n <= 0:
        return []

    # List to store the generated colors
    color_list: list[QColor] = []

    for i in range(n):
        # Calculate the hue value (H in HSV), which is evenly distributed between 0 and 359
        hue: int = int(360.0 * i / n)

        # Create a QColor object from the HSV values
        # S (saturation) and V (value) are set to 255 for maximum saturation and brightness
        current_color: QColor = QColor.fromHsv(hue, 255, 255)

        # Add the generated color to the list
        color_list.append(current_color)

    return color_list


def rgb2bgr(rgb: tuple) -> tuple[int, int, int]:
    """
    Convert an RGB color to BGR.

    :param rgb: tuple[int, int, int], an RGB color.
    :return: tuple[int, int, int], the BGR color.
    """
    return rgb[2], rgb[1], rgb[0]


def qcolor2bgr(color: QColor) -> tuple[int, int, int]:
    """
    Convert a QColor object to BGR.

    :param color: QColor, a QColor object.
    :return: tuple[int, int, int], the BGR color.
    """
    return rgb2bgr((color.red(), color.green(), color.blue()))


def generate_unique_opencv_colors(n: int) -> list[tuple[int, int, int]]:
    """
    Generate a list of n unique OpenCV colors.

    :param n: int, the number of unique colors to generate. Must be greater than 0.
    :return: list[tuple[int, int, int]], a list containing n unique OpenCV colors.
    """

    return [qcolor2bgr(color) for color in generate_unique_q_colors(n)]


if __name__ == "__main__":
    colors: list[QColor] = generate_unique_q_colors(10)
    for color in colors:
        print(f"RGB: {color.red()}, {color.green()}, {color.blue()} - Hex: {color.name()}")

    opencv_colors: list[tuple[int, int, int]] = generate_unique_opencv_colors(10)
    for color in opencv_colors:
        print(f"BGR: {color}")
