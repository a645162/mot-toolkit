from typing import List

import cv2
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit, QPushButton,
                               QVBoxLayout, QWidget, QColorDialog, QCheckBox, QHBoxLayout, QMessageBox)
from PySide6.QtGui import QColor

from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotation


class OpenCVPreviewOptionWindow(QMainWindow):
    frame_index_min: int
    frame_index_max: int

    current_frame_index: int

    annotation_file: List[XAnyLabelingAnnotation]

    def __init__(
            self,
            annotation_file=None,
            current_frame: int = -1,
            start_frame: int = 0,
            end_frame: int = 1,
            unselected_color: tuple | QColor = QColor(0, 255, 0),
            selected_color: tuple | QColor = QColor(0, 255, 255),
            text_color: tuple | QColor = QColor(0, 0, 255),
            thickness: int = 2,
            selection_label="",
            parent=None
    ):
        super().__init__(parent=parent)

        if isinstance(selected_color, tuple):
            selected_color = QColor(*selected_color)
        if isinstance(unselected_color, tuple):
            unselected_color = QColor(*unselected_color)
        if isinstance(text_color, tuple):
            text_color = QColor(*text_color)

        if annotation_file is None:
            annotation_file = []
        self.annotation_file = annotation_file

        self.frame_index_min = start_frame
        self.frame_index_max = end_frame
        self.current_frame_index = current_frame

        # 设置窗口标题
        self.setWindowTitle('OpenCV Preview')

        # 设置默认颜色
        self.selected_color = selected_color
        self.unselected_color = unselected_color
        self.text_color = text_color

        # 创建控件
        self.start_label = QLabel('Start Frame:')
        self.start_edit = QLineEdit(str(start_frame))

        self.end_label = QLabel('End Frame:')
        self.end_edit = QLineEdit(str(end_frame))

        if current_frame != -1 and start_frame <= current_frame <= end_frame:
            self.start_edit.setText(str(current_frame))
            self.end_edit.setText(str(current_frame))

        self.label_frame_range = QLabel(f'Frame Range:{start_frame} - {end_frame}')

        self.show_box_checkbox = QCheckBox('Show Box')
        self.show_box_checkbox.setChecked(True)
        self.with_text_checkbox = QCheckBox('With Text')
        self.with_text_checkbox.setChecked(True)

        self.select_color_button = QPushButton('Select Selected Color')
        self.text_color_button = QPushButton('Select Text Color')
        self.unselect_color_button = QPushButton('Select Unselected Color')

        self.frame_interval_label = QLabel('Frame Interval:')
        self.frame_interval_edit = QLineEdit('1')

        self.thickness_label = QLabel('Thickness:')
        self.thickness_edit = QLineEdit(str(thickness))

        self.selection_label_label = QLabel('Selection Label:')
        self.selection_label_edit = QLineEdit(selection_label)

        self.ok_button = QPushButton('Start')
        self.cancel_button = QPushButton('Close')

        # 设置颜色按钮的样式
        self.update_color_buttons_style()

        # 连接事件
        self.select_color_button.clicked.connect(self.select_selected_color)
        self.unselect_color_button.clicked.connect(self.select_unselected_color)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        # 设置布局
        layout = QVBoxLayout()

        layout.addWidget(self.start_label)
        layout.addWidget(self.start_edit)

        layout.addWidget(self.end_label)
        layout.addWidget(self.end_edit)

        layout.addWidget(self.label_frame_range)

        layout.addWidget(self.show_box_checkbox)
        layout.addWidget(self.with_text_checkbox)

        layout.addWidget(self.select_color_button)
        layout.addWidget(self.text_color_button)
        layout.addWidget(self.unselect_color_button)

        layout.addWidget(self.frame_interval_label)
        layout.addWidget(self.frame_interval_edit)

        layout.addWidget(self.thickness_label)
        layout.addWidget(self.thickness_edit)

        layout.addWidget(self.selection_label_label)
        layout.addWidget(self.selection_label_edit)

        button_layout = QHBoxLayout()

        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def select_selected_color(self):
        color = QColorDialog.getColor(initial=self.selected_color, parent=self)
        if color.isValid():
            self.selected_color = color
            self.update_color_buttons_style()

    def select_text_color(self):
        color = QColorDialog.getColor(initial=self.text_color, parent=self)
        if color.isValid():
            self.text_color = color
            self.update_color_buttons_style()

    def select_unselected_color(self):
        color = QColorDialog.getColor(initial=self.unselected_color, parent=self)
        if color.isValid():
            self.unselected_color = color
            self.update_color_buttons_style()

    def update_color_buttons_style(self):
        self.select_color_button.setStyleSheet(f'background-color: {self.selected_color.name()};')
        self.text_color_button.setStyleSheet(f'background-color: {self.text_color.name()};')
        self.unselect_color_button.setStyleSheet(f'background-color: {self.unselected_color.name()};')

    def accept(self):
        try:
            start_frame = int(self.start_edit.text())
            end_frame = int(self.end_edit.text())
            thickness = int(self.thickness_edit.text())

            frame_interval = int(self.frame_interval_edit.text())
            selection_label = str(self.selection_label_edit.text()).strip()

            show_box = self.show_box_checkbox.isChecked()
            with_text = self.with_text_checkbox.isChecked()
        except ValueError:
            QMessageBox.critical(self, 'Error', 'Invalid input')
            return

        if thickness <= 0:
            thickness = 1

        if start_frame < self.frame_index_min or start_frame > self.frame_index_max:
            QMessageBox.critical(self, 'Error', 'Start frame out of range')
            return

        if frame_interval < 0:
            QMessageBox.critical(self, 'Error', 'Frame interval should be positive')
            return

        selected_color = self.selected_color
        text_color = self.text_color
        unselected_color = self.unselected_color

        file_count = len(self.annotation_file)

        """
        def get_cv_mat_with_box(
            self,
            with_text=True,
            color: tuple = (0, 255, 0),
            text_color: tuple = (0, 0, 255),
            thickness: int = 2,
            selection_label: str = "",
            selection_color: tuple = (0, 255, 255),
    )
    """

        for i, annotation in enumerate(self.annotation_file):
            frame_index = i + 1
            if frame_index < start_frame or frame_index > end_frame:
                continue

            if show_box:
                image = annotation.get_cv_mat_with_box(
                    with_text=with_text,
                    color=unselected_color,
                    text_color=text_color,
                    thickness=thickness,
                    selection_label=selection_label,
                    selection_color=selected_color,
                )
            else:
                image = annotation.get_cv_mat()

            # Draw Text
            text = f"{i + 1}/{file_count}"
            cv2.putText(
                image,
                text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

            cv2.imshow("OpenCV Preview", image)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()

    def reject(self):
        self.close()


if __name__ == '__main__':
    app = QApplication([])

    window = OpenCVPreviewOptionWindow(start_frame=1, end_frame=100)
    window.show()

    app.exec_()
