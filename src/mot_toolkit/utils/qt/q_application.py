import sys

from PySide6.QtWidgets import QApplication


def getQApplication() -> QApplication:
    """Get the current QApplication instance.

    Returns:
        QApplication: The current QApplication instance.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app
