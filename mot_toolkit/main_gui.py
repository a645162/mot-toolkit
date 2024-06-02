import sys

sys.path.append(".")

from mot_toolkit.utils.logs import get_logger

logger = get_logger()

logger.info("Start Load Init MainWindow Package")

from mot_toolkit.gui.view.main_window import init_main_window

if __name__ == "__main__":
    logger.info("Start to initialize the Main Window")
    init_main_window()
