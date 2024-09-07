from PySide6.QtCore import QRect
from PySide6.QtWidgets import QApplication

from mot_toolkit.utils.qt.q_application import getQApplication


def q_rect_by_factor(original_rect: QRect, scale_factor: float) -> QRect:
    return QRect(
        int(original_rect.x() * scale_factor),
        int(original_rect.y() * scale_factor),
        int(original_rect.width() * scale_factor),
        int(original_rect.height() * scale_factor)
    )


def get_qt_dpi_scaling():
    # Get instance of QApplication
    app: QApplication = getQApplication()

    # Get the default screen
    screen = app.screens()[0]
    # Get the logical DPI
    dpi = screen.logicalDotsPerInch()
    # Get the physical DPI
    physical_dpi = screen.physicalDotsPerInch()
    # Calculate the scaling factor
    scaling = dpi / physical_dpi

    return scaling


def get_qt_device_pixel_ratio():
    app: QApplication = getQApplication()

    ratio = app.devicePixelRatio()

    return ratio


if __name__ == "__main__":
    # Get the DPI scaling factor
    dpi_scaling = get_qt_dpi_scaling()
    # Print the current DPI scaling factor
    print(f"The current DPI scaling factor is: {dpi_scaling}")

    dpi_ratio = get_qt_device_pixel_ratio()
    print(f"The current DPI ratio is: {dpi_ratio}")
