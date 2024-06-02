from PySide6.QtCore import QSettings
from mot_toolkit.utils.logs import get_logger

logger = get_logger()


class ProgramSettings:
    settings = QSettings("KHM", "mot-toolkit")

    def __init__(self):
        logger.info("ProgramSettings Init")

    def load(self):
        pass

    def save(self):
        self.settings.sync()

    @property
    def last_work_directory(self) -> str:
        return str(self.settings.value(
            "last/last_work_directory",
            "./Test",
            type=str
        ))

    @last_work_directory.setter
    def last_work_directory(self, value: str):
        self.settings.setValue(
            "last/last_work_directory",
            value
        )

    @property
    def preview_auto_save(self) -> bool:
        return bool(self.settings.value(
            "preview/auto_save",
            False,
            type=bool
        ))

    @preview_auto_save.setter
    def preview_auto_save(self, value: bool):
        self.settings.setValue(
            "preview/auto_save",
            value
        )


program_settings = ProgramSettings()

if __name__ == "__main__":
    program_settings.last_work_directory = "C:/Users/username/Desktop"
    print(program_settings.last_work_directory)
