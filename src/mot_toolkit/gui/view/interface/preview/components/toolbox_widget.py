from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QSizePolicy,
    QPushButton, QLabel
)


class ToolboxButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__setup_widget_properties()

    def __setup_widget_properties(self):
        self.setMinimumWidth(0)
        self.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Minimum
        )


class ToolboxWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.__setup_widget_properties()

        self.__init_widgets()

    def __setup_widget_properties(self):
        self.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding
        )
        # self.setFixedWidth(48)
        # pass

    def __init_widgets(self):
        self.v_layout = QVBoxLayout()
        self.setLayout(self.v_layout)

        self.btn_open_dir = ToolboxButton(parent=self)
        self.btn_open_dir.setIcon(QIcon(":/toolbox/folder_open"))
        self.btn_open_dir.setToolTip("Open Directory")
        self.v_layout.addWidget(self.btn_open_dir)

        self.btn_refresh_dir = ToolboxButton(parent=self)
        self.btn_refresh_dir.setIcon(QIcon(":/toolbox/folder_refresh"))
        self.btn_refresh_dir.setToolTip("Refresh Directory")
        self.v_layout.addWidget(self.btn_refresh_dir)

        self.v_layout.addWidget(QLabel(parent=self))

        # Frame
        self.btn_previous_frame = ToolboxButton(parent=self)
        self.btn_previous_frame.setIcon(QIcon(":/toolbox/frame_previous"))
        self.btn_previous_frame.setToolTip("Previous Frame")
        self.v_layout.addWidget(self.btn_previous_frame)

        self.btn_next_frame = ToolboxButton(parent=self)
        self.btn_next_frame.setIcon(QIcon(":/toolbox/frame_next"))
        self.btn_next_frame.setToolTip("Next Frame")
        self.v_layout.addWidget(self.btn_next_frame)

        self.v_layout.addWidget(QLabel(parent=self))

        # Zoom
        self.btn_zoom_in_10 = ToolboxButton(parent=self)
        self.btn_zoom_in_10.setText("+1.")
        self.btn_zoom_in_10.setToolTip("Zoom In + 1.0")
        self.v_layout.addWidget(self.btn_zoom_in_10)

        self.btn_zoom_in_5 = ToolboxButton(parent=self)
        self.btn_zoom_in_5.setText("+.5")
        self.btn_zoom_in_5.setToolTip("Zoom In + 0.5")
        self.v_layout.addWidget(self.btn_zoom_in_5)

        self.btn_zoom_in = ToolboxButton(parent=self)
        self.btn_zoom_in.setIcon(QIcon(":/toolbox/zoom_in"))
        self.btn_zoom_in.setToolTip("Zoom In + 0.1")
        self.v_layout.addWidget(self.btn_zoom_in)

        self.btn_zoom_restore = ToolboxButton(parent=self)
        self.btn_zoom_restore.setIcon(QIcon(":/toolbox/zoom_restore"))
        self.btn_zoom_restore.setToolTip("Zoom Restore -> 0")
        self.v_layout.addWidget(self.btn_zoom_restore)

        self.btn_zoom_out = ToolboxButton(parent=self)
        self.btn_zoom_out.setIcon(QIcon(":/toolbox/zoom_out"))
        self.btn_zoom_out.setToolTip("Zoom Out - 0.1")
        self.v_layout.addWidget(self.btn_zoom_out)

        self.btn_zoom_out_5 = ToolboxButton(parent=self)
        self.btn_zoom_out_5.setText("-.5")
        self.btn_zoom_out_5.setToolTip("Zoom Out - 0.5")
        self.v_layout.addWidget(self.btn_zoom_out_5)

        self.btn_zoom_out_10 = ToolboxButton(parent=self)
        self.btn_zoom_out_10.setText("-1.")
        self.btn_zoom_out_10.setToolTip("Zoom Out - 1.0")
        self.v_layout.addWidget(self.btn_zoom_out_10)

        self.btn_zoom_fit = ToolboxButton(parent=self)
        self.btn_zoom_fit.setIcon(QIcon(":/toolbox/zoom_fit"))
        self.btn_zoom_fit.setToolTip("Zoom Fit")
        self.v_layout.addWidget(self.btn_zoom_fit)

        self.btn_zoom_input = ToolboxButton(parent=self)
        self.btn_zoom_input.setText("Zoom")
        self.btn_zoom_input.setToolTip("Zoom")
        self.v_layout.addWidget(self.btn_zoom_input)

        self.btn_center = ToolboxButton(parent=self)
        self.btn_center.setText("Center")
        self.btn_center.setToolTip("Center")
        self.v_layout.addWidget(self.btn_center)

        self.v_layout.addWidget(QLabel(parent=self))

        self.btn_reverse_color = ToolboxButton(parent=self)
        self.btn_reverse_color.setIcon(QIcon(":/toolbox/reverse_color"))
        self.btn_reverse_color.setToolTip("Reverse Color")
        self.v_layout.addWidget(self.btn_reverse_color)

        self.v_layout.addStretch()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    from mot_toolkit.gui.resources.resources import qInitResources

    qInitResources()

    app = QApplication([])

    window = QWidget()
    window.setWindowTitle("ToolboxWidget")
    v_layout = QVBoxLayout()
    window.setLayout(v_layout)

    widget = ToolboxWidget(parent=window)
    widget.setSizePolicy(
        QSizePolicy.Policy.Minimum,
        QSizePolicy.Policy.Expanding
    )
    v_layout.addWidget(widget)

    window.show()

    app.exec()
