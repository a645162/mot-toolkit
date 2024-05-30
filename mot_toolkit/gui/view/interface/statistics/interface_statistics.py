from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout, QGroupBox,
    QMessageBox,
    QLabel, QPushButton, QLineEdit,
)

from mot_toolkit.gui.view.components.base_interface_window import BaseInterfaceWindow
from mot_toolkit.utils.statistics.stats_file import stats_file_count


class FileStatisticsWidget(QGroupBox):
    work_directory_path: str = ""

    def __init__(self, parent=None, work_directory_path: str = ""):
        super().__init__(parent=parent)

        self.work_directory_path = work_directory_path

        self.__setup_widget_properties()

        self.__init_widgets()

    def __setup_widget_properties(self):
        pass

    def __init_widgets(self):
        self.v_layout = QVBoxLayout()
        self.setLayout(self.v_layout)

        self.label = QLabel(parent=self)
        self.label.setText("Statistics Files:")
        self.v_layout.addWidget(self.label)

        self.line_edit_file_extension = QLineEdit(parent=self)
        self.line_edit_file_extension.setPlaceholderText("File Extension")
        self.line_edit_file_extension.setText("json")
        self.v_layout.addWidget(self.line_edit_file_extension)

        self.btn_stats_files = QPushButton(parent=self)
        self.btn_stats_files.setText("Stats Files")
        self.btn_stats_files.clicked.connect(self.__button_stats_files_clicked)
        self.v_layout.addWidget(self.btn_stats_files)

    def __button_stats_files_clicked(self):
        file_extension = self.line_edit_file_extension.text().strip()

        if not file_extension or len(file_extension) == 0:
            file_extension = "json"

        file_count = \
            stats_file_count(
                directory_path=self.work_directory_path,
                file_extension=file_extension,
                recursive=True
            )
        QMessageBox.information(self, "Info", f"File Count: {file_count}")


class StatisticsWidget(QWidget):
    work_directory_path: str = ""

    def __init__(self, work_directory_path: str):
        super().__init__()

        self.work_directory_path = work_directory_path

        self.__setup_window_properties()

        self.__init_widgets()

    def __setup_window_properties(self):
        self.setWindowTitle("Statistics")

    def __init_widgets(self):
        self.v_layout = QVBoxLayout()
        self.setLayout(self.v_layout)

        self.label_path = QLabel(parent=self)
        self.label_path.setText(f"Path:{self.work_directory_path}")
        self.v_layout.addWidget(self.label_path)

        self.v_layout.addSpacing(10)

        self.widget_file_statistics = FileStatisticsWidget(
            parent=self,
            work_directory_path=self.work_directory_path
        )
        self.v_layout.addWidget(self.widget_file_statistics)


class InterfaceStatistics(BaseInterfaceWindow):
    work_directory_path: str = ""

    def __init__(self, work_directory_path: str = ""):
        super().__init__(work_directory_path=work_directory_path)

        self.__setup_window_properties()

        self.__init_widgets()

    def __setup_window_properties(self):
        pass

    def __init_widgets(self):
        self.statistics_widget = StatisticsWidget(self.work_directory_path)
        self.v_layout.addWidget(self.statistics_widget)
