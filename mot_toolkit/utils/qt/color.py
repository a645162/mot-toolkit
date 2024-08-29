from PySide6.QtGui import QColor


def hex_to_qcolor(hex_color: str) -> QColor:
    if not hex_color.startswith('#'):
        hex_color = '#' + hex_color

    color = QColor()
    color.setNamedColor(hex_color)

    return color
