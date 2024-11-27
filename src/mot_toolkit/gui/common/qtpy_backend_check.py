def qtpy_backend() -> str:
    import qtpy

    # Get Current QtPy Backend Binding
    return qtpy.API


def is_pyside2_installed() -> bool:
    try:
        import PySide2
        return True
    except ImportError:
        return False


def is_pyqt5_installed() -> bool:
    try:
        import PyQt5
        return True
    except ImportError:
        return False


def is_pyside6_installed() -> bool:
    try:
        import PySide6
        return True
    except ImportError:
        return False


def is_pyqt6_installed() -> bool:
    try:
        import PyQt6
        return True
    except ImportError:
        return False
