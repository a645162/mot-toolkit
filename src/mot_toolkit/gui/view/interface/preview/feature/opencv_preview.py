import datetime
import os
from typing import List

import cv2
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit, QPushButton,
                               QVBoxLayout, QWidget, QColorDialog, QCheckBox, QHBoxLayout, QMessageBox)
from PySide6.QtGui import QColor

from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotation
from mot_toolkit.gui.view.components.widget.combination.file_save_widget import FileSaveWidget


def bgr2rgb(color: tuple) -> tuple:
    return color[2], color[1], color[0]


def reverse_color(color: QColor) -> QColor:
    return QColor(255 - color.red(), 255 - color.green(), 255 - color.blue())


class OpenCVPreviewOptionWindow(QMainWindow):
    frame_index_min: int
    frame_index_max: int

    current_frame_index: int

    annotation_file_list: List[XAnyLabelingAnnotation]
    color_dict: dict

    def __init__(
            self,
            annotation_file: List[XAnyLabelingAnnotation] = None,
            current_frame: int = -1,
            start_frame: int = 0,
            end_frame: int = 1,
            unselected_color: tuple | QColor = (0, 255, 0),
            selected_color: tuple | QColor = (0, 255, 255),
            text_color: tuple | QColor = (0, 0, 255),
            thickness: int = 2,
            selection_label: str = "",
            color_dict: dict = None,
            parent=None
    ):
        super().__init__(parent=parent)

        if isinstance(selected_color, tuple):
            selected_color = QColor(*bgr2rgb(selected_color))
        if isinstance(unselected_color, tuple):
            unselected_color = QColor(*bgr2rgb(unselected_color))
        if isinstance(text_color, tuple):
            text_color = QColor(*bgr2rgb(text_color))

        if annotation_file is None:
            annotation_file = []
        self.annotation_file_list = annotation_file

        if color_dict is None:
            color_dict = {}
        self.color_dict = color_dict

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

        # if current_frame != -1 and start_frame <= current_frame <= end_frame:
        #     self.start_edit.setText(str(current_frame))
        #     self.end_edit.setText(str(current_frame))

        self.label_frame_range = QLabel(f'Frame Range: {start_frame} - {end_frame}')
        self.label_current_frame = QLabel(f'Current Frame: {current_frame}')

        self.__init_ui(current_frame, thickness, selection_label)

    def __init_ui(
            self,
            current_frame: int,
            thickness: int,
            selection_label: str
    ):

        range_widget = QWidget()
        range_layout = QHBoxLayout()
        range_widget.setLayout(range_layout)

        self.button_current_frame = QPushButton('Current Frame')
        self.button_current_frame.clicked.connect(self.set_current_frame)
        range_layout.addWidget(self.button_current_frame)
        self.button_restore_range = QPushButton('Restore Range')
        self.button_restore_range.clicked.connect(self.restore_range)
        range_layout.addWidget(self.button_restore_range)

        if current_frame == -1:
            self.label_current_frame.setVisible(False)
            self.button_current_frame.setVisible(False)

        self.play_loop_checkbox = QCheckBox('Play in a loop')
        self.play_loop_checkbox.setChecked(False)
        self.pause_on_last_frame_checkbox = QCheckBox('Pause on Last Frame')
        self.pause_on_last_frame_checkbox.setChecked(False)
        self.show_box_checkbox = QCheckBox('Show Box')
        self.show_box_checkbox.setChecked(True)
        self.different_color_checkbox = QCheckBox('Different Color')
        self.different_color_checkbox.setChecked(False)
        self.with_text_checkbox = QCheckBox('With Text')
        self.with_text_checkbox.setChecked(False)
        self.center_point_trajectory_checkbox = QCheckBox('Center Point Trajectory')
        self.center_point_trajectory_checkbox.setChecked(True)
        self.only_near_selection_checkbox = QCheckBox('Only Near Selection')
        self.only_near_selection_checkbox.setChecked(False)
        self.only_selection_box = QCheckBox('Only Selection Box')
        self.only_selection_box.setChecked(False)

        self.select_color_button = QPushButton('Select Selected Color')
        self.text_color_button = QPushButton('Select Text Color')
        self.unselect_color_button = QPushButton('Select Unselected Color')

        self.frame_interval_label = QLabel('Frame Interval:')
        self.frame_interval_edit = QLineEdit('1')

        self.thickness_label = QLabel('Thickness:')
        self.thickness_edit = QLineEdit(str(thickness))

        self.selection_label_label = QLabel('Selection Label:')
        self.selection_label_edit = QLineEdit(selection_label)

        self.crop_padding_label = QLabel('Crop Padding:')
        self.crop_padding_edit = QLineEdit("50")

        self.output_video_checkbox = QCheckBox('Output Video')
        self.output_video_checkbox.setChecked(False)

        self.video_path_widget = FileSaveWidget()

        now = datetime.datetime.now()
        formatted_time = now.strftime("%Y-%m-%d-%H-%M-%S")
        self.video_path_widget.file_path = f"{formatted_time}.mp4"
        self.video_path_widget.filter = "MP4 Video (*.mp4);;AVI Video (*.avi);;All Files (*)"

        self.ok_button = QPushButton('Start')
        self.cancel_button = QPushButton('Close')

        # Set Button Text Color
        self.update_color_buttons_style()

        #  Connect Signals
        self.select_color_button.clicked.connect(self.select_selected_color)
        self.text_color_button.clicked.connect(self.select_text_color)
        self.unselect_color_button.clicked.connect(self.select_unselected_color)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        # Setup Layout
        layout = QVBoxLayout()

        layout.addWidget(self.start_label)
        layout.addWidget(self.start_edit)

        layout.addWidget(self.end_label)
        layout.addWidget(self.end_edit)

        layout.addWidget(self.label_frame_range)
        layout.addWidget(self.label_current_frame)
        layout.addWidget(range_widget)

        layout.addWidget(self.play_loop_checkbox)
        layout.addWidget(self.pause_on_last_frame_checkbox)
        layout.addWidget(self.show_box_checkbox)
        layout.addWidget(self.different_color_checkbox)
        layout.addWidget(self.with_text_checkbox)
        layout.addWidget(self.center_point_trajectory_checkbox)
        layout.addWidget(self.only_near_selection_checkbox)
        layout.addWidget(self.only_selection_box)

        layout.addWidget(self.select_color_button)
        layout.addWidget(self.text_color_button)
        layout.addWidget(self.unselect_color_button)

        layout.addWidget(self.frame_interval_label)
        layout.addWidget(self.frame_interval_edit)

        layout.addWidget(self.thickness_label)
        layout.addWidget(self.thickness_edit)

        layout.addWidget(self.selection_label_label)
        layout.addWidget(self.selection_label_edit)

        layout.addWidget(self.crop_padding_label)
        layout.addWidget(self.crop_padding_edit)

        layout.addWidget(self.output_video_checkbox)
        layout.addWidget(self.video_path_widget)

        button_layout = QHBoxLayout()

        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def set_current_frame(self):
        if self.current_frame_index == -1:
            return
        if self.frame_index_min <= self.current_frame_index <= self.frame_index_max:
            self.start_edit.setText(str(self.current_frame_index))
            self.end_edit.setText(str(self.current_frame_index))

    def restore_range(self):
        self.start_edit.setText(str(self.frame_index_min))
        self.end_edit.setText(str(self.frame_index_max))

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
        # self.select_color_button.setStyleSheet(f'background-color: {self.selected_color.name()};')
        # self.text_color_button.setStyleSheet(f'background-color: {self.text_color.name()};')
        # self.unselect_color_button.setStyleSheet(f'background-color: {self.unselected_color.name()};')

        # Set button Text Color
        self.select_color_button.setStyleSheet(f'color: {self.selected_color.name()};')
        self.text_color_button.setStyleSheet(f'color: {self.text_color.name()};')
        self.unselect_color_button.setStyleSheet(f'color: {self.unselected_color.name()};')

        # # Set button Background Color(Reverse Color)
        # self.select_color_button.setStyleSheet(f'background-color: {reverse_color(self.selected_color).name()};')
        # self.text_color_button.setStyleSheet(f'background-color: {reverse_color(self.text_color).name()};')
        # self.unselect_color_button.setStyleSheet(f'background-color: {reverse_color(self.unselected_color).name()};')

    def accept(self):
        if len(self.annotation_file_list) == 0:
            QMessageBox.critical(self, 'Error', 'No any annotation file!')
            return

        try:
            start_frame = int(self.start_edit.text())
            end_frame = int(self.end_edit.text())
            thickness = int(self.thickness_edit.text())
            crop_padding = int(self.crop_padding_edit.text())

            frame_interval = int(self.frame_interval_edit.text())
            selection_label = str(self.selection_label_edit.text()).strip()

            loop_play = self.play_loop_checkbox.isChecked()
            pause_on_last_frame = self.pause_on_last_frame_checkbox.isChecked()
            show_box = self.show_box_checkbox.isChecked()
            different_color = self.different_color_checkbox.isChecked()
            with_text = self.with_text_checkbox.isChecked()
            show_center_point_trajectory = self.center_point_trajectory_checkbox.isChecked()
            only_near_selection = self.only_near_selection_checkbox.isChecked()
            only_selection_box = self.only_selection_box.isChecked()

            output_video = self.output_video_checkbox.isChecked()
            video_path = self.video_path_widget.get_file_path()
        except ValueError:
            QMessageBox.critical(self, 'Error', 'Invalid input')
            return

        if thickness <= 0:
            thickness = 1

        if crop_padding < 0:
            crop_padding = 0

        if output_video:
            try:
                # Write Test
                with open(video_path, 'w') as f:
                    f.write("Test")

                # Remove
                os.remove(video_path)
            except Exception:
                output_video = False

        if start_frame < self.frame_index_min or start_frame > self.frame_index_max:
            QMessageBox.critical(self, 'Error', 'Start frame out of range')
            return

        if frame_interval < 0:
            QMessageBox.critical(self, 'Error', 'Frame interval should be positive')
            return

        selected_color = self.selected_color
        text_color = self.text_color
        unselected_color = self.unselected_color

        # Generate Color List

        file_count = len(self.annotation_file_list)

        image_width, image_height = (
            self.annotation_file_list[0].image_width,
            self.annotation_file_list[0].image_height
        )

        play_one = False
        while loop_play or (not play_one):
            center_point_trajectory: dict = {}

            output_video = output_video and (not play_one)

            video_out = None
            if output_video:
                if video_path.endswith('.mp4'):
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                else:
                    fourcc = cv2.VideoWriter_fourcc(*'XVID')
                video_out = cv2.VideoWriter(video_path, fourcc, 30.0, (image_width, image_height))

            for i, annotation in enumerate(self.annotation_file_list):
                frame_index = i + 1
                is_last_frame = frame_index == file_count
                if frame_index < start_frame or frame_index > end_frame:
                    continue

                if show_box:
                    image = annotation.get_cv_mat_with_box(
                        with_text=with_text,
                        color=unselected_color,
                        text_color=text_color,
                        thickness=thickness,
                        center_point_trajectory=center_point_trajectory,
                        draw_trajectory=show_center_point_trajectory,
                        selection_label=selection_label,
                        selection_color=selected_color,
                        only_selection_box=only_selection_box,
                        crop_selection=only_near_selection,
                        not_found_return_none=only_near_selection,
                        crop_padding=crop_padding,
                        color_dict=self.color_dict if different_color else None
                    )
                else:
                    image = annotation.get_cv_mat()

                if image is None:
                    continue

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

                if output_video and video_out is not None:
                    video_out.write(image)
                cv2.imshow("OpenCV Preview", image)
                if is_last_frame and pause_on_last_frame:
                    if cv2.waitKey(0) & 0xFF == ord('q'):
                        loop_play = False
                        break
                else:
                    if cv2.waitKey(frame_interval) & 0xFF == ord('q'):
                        loop_play = False
                        break
            if video_out:
                video_out.release()
            play_one = True

        cv2.destroyAllWindows()

    def reject(self):
        self.close()


if __name__ == '__main__':
    app = QApplication([])

    window = OpenCVPreviewOptionWindow(start_frame=1, end_frame=100)
    window.show()

    app.exec_()
