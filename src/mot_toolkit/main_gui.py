import sys

from mot_toolkit.gui.common.qtpy_backend_check import (
    qtpy_backend,
    is_pyside2_installed, is_pyside6_installed,
    is_pyqt5_installed, is_pyqt6_installed
)
from mot_toolkit.utils.cli.print_info import print_info

sys.path.append("..")

from mot_toolkit.utils.logs import get_logger

logger = get_logger()

logger.info("Start Load Init MainWindow Package")

# Get Current QtPy Backend Binding
current_backend = qtpy_backend()

logger.info(f"Current QtPy backend: {current_backend}")
logger.info(f"PySide2 Installed: {is_pyside2_installed()}")
logger.info(f"PyQt5 Installed: {is_pyqt5_installed()}")
logger.info(f"PySide6 Installed: {is_pyside6_installed()}")
logger.info(f"PyQt6 Installed: {is_pyqt6_installed()}")

from mot_toolkit.gui.view.main_window import init_main_window


def test():
    logger.info("Test Passed!")
    exit(0)


def main():
    print_info()

    logger.info("Start to initialize the Main Window")
    init_main_window()


if __name__ == "__main__":
    main()
