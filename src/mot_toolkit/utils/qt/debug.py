from PySide6.QtCore import QRect


def q_rect_str(rect: QRect) -> str:
    return f"{rect.x()}, {rect.y()}, {rect.width()}, {rect.height()}"


def print_q_rect(rect: QRect, text: str = ""):
    """
    Print a QRect object in a more readable format.
    """

    if not text:
        text = "QRect"

    print(f"{text}({q_rect_str(rect)})")
