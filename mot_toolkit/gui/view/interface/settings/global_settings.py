from PySide6.QtCore import QSettings


class ProgramSettings:
    settings = QSettings("KHM", "mot-toolkit")

    def __init__(self):
        pass

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


program_settings = ProgramSettings()

if __name__ == "__main__":
    program_settings.last_work_directory = "C:/Users/username/Desktop"
    print(program_settings.last_work_directory)
