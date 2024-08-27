from mot_toolkit.gui.view.components. \
    base_interface_window import BaseWorkInterfaceWindow

from mot_toolkit.utils.logs import get_logger

logger = get_logger()


class InterFaceSmooth(BaseWorkInterfaceWindow):
    def __init__(self, work_directory_path: str):
        super().__init__(work_directory_path)
        logger.info(f"Smooth Work Directory: {work_directory_path}")
