from PySide6.QtGui import QScreen, QCursor
from PySide6.QtWidgets import QApplication


def get_activate_screen() -> QScreen:
    # Get the cursor position
    cursor_pos = QCursor.pos()

    # Get the screen where the cursor is
    active_screen = QApplication.screenAt(cursor_pos)

    return active_screen
