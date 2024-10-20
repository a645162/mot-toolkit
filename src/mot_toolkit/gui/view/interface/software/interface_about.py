import sys

import PySide6
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel
)

from mot_toolkit.gui.view.components. \
    window.base_q_main_window import BaseQMainWindow
from mot_toolkit.gui.view.components.widget. \
    basic.link_label import LinkLabel
from mot_toolkit.utils.system.linux.system import is_linux
from mot_toolkit.utils.system.system import SystemType


class InterFaceAbout(BaseQMainWindow):
    basic_window_title: str = "About"

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__setup_window_properties()

        self.__init_widgets()

    def __setup_window_properties(self):
        self.setWindowTitle(self.basic_window_title)

        # self.setMinimumSize(QSize(640, 320))
        # self.setMinimumSize(QSize(800, 600))
        # self.setBaseSize(QSize(800, 600))

    def add_label(self, text: str) -> QLabel:
        q_label = QLabel(text, parent=self.v_layout_widget)
        self.v_layout.addWidget(q_label)

        return q_label

    def __init_widgets(self):
        self.v_layout_widget = QWidget(parent=self)
        self.v_layout = QVBoxLayout()
        self.v_layout_widget.setLayout(self.v_layout)
        self.setCentralWidget(self.v_layout_widget)

        self.add_label("MOT-Toolkit")
        self.add_label("Multiple Object Tracking Toolkit")

        self.add_label("")

        system_type = SystemType.get_system_type()
        self.add_label(f"System Platform: {system_type.value}")

        if is_linux():
            from mot_toolkit.utils.system.linux.display import LinuxWindowSystem
            window_system = LinuxWindowSystem.detect()
            self.add_label(f"Graphic System: {window_system.value}")

        self.add_label("")

        python_version = str(sys.version)
        self.add_label(f"Python Version: Python {python_version}")
        qt_version = PySide6.__version__
        self.add_label(f"Qt Version: PySide6({qt_version})")

        self.add_label("")
        self.add_label("Author: Haomin Kong")
        self.add_label("2024 Shanghai Maritime University")
        self.add_label("")

        github_link = LinkLabel(
            url="https://github.com/a645162/mot-toolkit",
        )
        self.v_layout.addWidget(github_link)


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    main_window = InterFaceAbout()
    main_window.show()
    sys.exit(app.exec())
