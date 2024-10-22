import datetime
import os
from typing import List

import cv2

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout, QHBoxLayout, QGroupBox,
    QColorDialog,
    QLabel, QLineEdit, QPushButton, QCheckBox,
    QMessageBox
)
from PySide6.QtGui import QColor

from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotation
from mot_toolkit.gui.view.components.widget.combination.file_save_widget import FileSaveWidget
from mot_toolkit.gui.view.components.window.base_q_main_window import BaseQMainWindow


def bgr2rgb(color: tuple) -> tuple:
    return color[2], color[1], color[0]


def reverse_color(color: QColor) -> QColor:
    return QColor(255 - color.red(), 255 - color.green(), 255 - color.blue())


class OpenCVPreviewOptionWindow(BaseQMainWindow):
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

        self.selected_color = selected_color
        self.unselected_color = unselected_color
        self.text_color = text_color

        self.__setup_properties()

        # Create widget
        self.__init_ui(current_frame, thickness, selection_label)

        self.move_to_center()

    def __setup_properties(self):
        self.setWindowTitle('OpenCV Preview')

    def __init_ui(
            self,
            current_frame: int,
            thickness: int,
            selection_label: str
    ):
        main_layout = QVBoxLayout()

        content_widget = QWidget()
        content_layout = QHBoxLayout()
        content_widget.setLayout(content_layout)

        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        content_layout.addLayout(left_layout)
        content_layout.addLayout(right_layout)

        main_layout.addWidget(content_widget)

        # Group Range
        group_range = QGroupBox("Range")
        group_range_layout = QVBoxLayout()
        group_range.setLayout(group_range_layout)
        left_layout.addWidget(group_range)

        self.start_label = QLabel('Start Frame:')
        group_range_layout.addWidget(self.start_label)
        self.start_edit = QLineEdit(str(self.frame_index_min))
        group_range_layout.addWidget(self.start_edit)

        self.end_label = QLabel('End Frame:')
        group_range_layout.addWidget(self.end_label)
        self.end_edit = QLineEdit(str(self.frame_index_max))
        group_range_layout.addWidget(self.end_edit)

        self.label_frame_range = QLabel(
            f'Frame Range: {self.frame_index_min} - {self.frame_index_max}'
        )
        group_range_layout.addWidget(self.label_frame_range)
        self.label_current_frame = QLabel(f'Current Frame: {current_frame}')
        group_range_layout.addWidget(self.label_current_frame)

        range_widget = QWidget()
        range_layout = QHBoxLayout()
        range_widget.setLayout(range_layout)

        self.button_current_frame = QPushButton('Current Frame')
        self.button_current_frame.clicked.connect(self.set_current_frame)
        range_layout.addWidget(self.button_current_frame)
        self.button_restore_range = QPushButton('Restore Range')
        self.button_restore_range.clicked.connect(self.restore_range)
        range_layout.addWidget(self.button_restore_range)

        group_range_layout.addWidget(range_widget)

        if current_frame == -1:
            self.label_current_frame.setVisible(False)
            self.button_current_frame.setVisible(False)

        # Group Play Control
        group_play_control = QGroupBox("Play Control")
        group_play_control_layout = QVBoxLayout()
        group_play_control.setLayout(group_play_control_layout)
        left_layout.addWidget(group_play_control)

        self.play_loop_checkbox = QCheckBox('Play in a loop')
        group_play_control_layout.addWidget(self.play_loop_checkbox)
        self.play_loop_checkbox.setChecked(False)
        group_play_control_layout.addWidget(self.play_loop_checkbox)
        self.pause_on_last_frame_checkbox = QCheckBox('Pause on Last Frame')
        group_play_control_layout.addWidget(self.pause_on_last_frame_checkbox)
        self.pause_on_last_frame_checkbox.setChecked(False)
        group_play_control_layout.addWidget(self.pause_on_last_frame_checkbox)

        self.frame_interval_label = QLabel('Frame Interval:')
        group_play_control_layout.addWidget(self.frame_interval_label)
        self.frame_interval_edit = QLineEdit('1')
        group_play_control_layout.addWidget(self.frame_interval_edit)

        # Group Box Control
        group_box_control = QGroupBox("Box Control")
        group_box_control_layout = QVBoxLayout()
        group_box_control.setLayout(group_box_control_layout)
        right_layout.addWidget(group_box_control)

        self.show_box_checkbox = QCheckBox('Show Box')
        group_box_control_layout.addWidget(self.show_box_checkbox)
        self.show_box_checkbox.setChecked(True)
        self.different_color_checkbox = QCheckBox('Different Color')
        group_box_control_layout.addWidget(self.different_color_checkbox)
        self.different_color_checkbox.setChecked(True)
        self.with_text_checkbox = QCheckBox('With Text')
        group_box_control_layout.addWidget(self.with_text_checkbox)
        self.with_text_checkbox.setChecked(False)
        self.center_point_trajectory_checkbox = QCheckBox('Center Point Trajectory')
        group_box_control_layout.addWidget(self.center_point_trajectory_checkbox)
        self.center_point_trajectory_checkbox.setChecked(True)

        self.select_color_button = QPushButton('Select Selected Color')
        self.select_color_button.clicked.connect(self.select_selected_color)
        group_box_control_layout.addWidget(self.select_color_button)
        self.text_color_button = QPushButton('Select Text Color')
        self.text_color_button.clicked.connect(self.select_text_color)
        group_box_control_layout.addWidget(self.text_color_button)
        self.unselect_color_button = QPushButton('Select Unselected Color')
        self.unselect_color_button.clicked.connect(self.select_unselected_color)
        group_box_control_layout.addWidget(self.unselect_color_button)
        # Set Button Text Color
        self.update_color_buttons_style()

        self.thickness_label = QLabel('Thickness:')
        group_box_control_layout.addWidget(self.thickness_label)
        self.thickness_edit = QLineEdit(str(thickness))
        group_box_control_layout.addWidget(self.thickness_edit)

        # Group Filter
        group_filter = QGroupBox("Filter")
        group_filter_layout = QVBoxLayout()
        group_filter.setLayout(group_filter_layout)
        right_layout.addWidget(group_filter)
        self.only_near_selection_checkbox = QCheckBox('Only Near Selection')
        group_filter_layout.addWidget(self.only_near_selection_checkbox)
        self.only_near_selection_checkbox.setChecked(False)
        self.only_selection_box = QCheckBox('Only Selection Box')
        group_filter_layout.addWidget(self.only_selection_box)
        self.only_selection_box.setChecked(False)

        self.selection_label_label = QLabel('Selection Label:')
        group_filter_layout.addWidget(self.selection_label_label)
        self.selection_label_edit = QLineEdit(selection_label)
        group_filter_layout.addWidget(self.selection_label_edit)

        self.crop_padding_label = QLabel('Crop Padding:')
        group_filter_layout.addWidget(self.crop_padding_label)
        self.crop_padding_edit = QLineEdit("50")
        group_filter_layout.addWidget(self.crop_padding_edit)

        # Group Output
        group_output = QGroupBox("Output")
        group_output_layout = QVBoxLayout()
        group_output.setLayout(group_output_layout)
        left_layout.addWidget(group_output)

        self.output_video_checkbox = QCheckBox('Output Video')
        group_output_layout.addWidget(self.output_video_checkbox)
        self.output_video_checkbox.setChecked(False)

        self.video_path_widget = FileSaveWidget()
        group_output_layout.addWidget(self.video_path_widget)

        now = datetime.datetime.now()
        formatted_time = now.strftime("%Y-%m-%d-%H-%M-%S")
        self.video_path_widget.file_path = f"{formatted_time}.mp4"
        self.video_path_widget.filter = "MP4 Video (*.mp4);;AVI Video (*.avi);;All Files (*)"

        # Control Buttons
        control_button_widget = QWidget()
        control_button_layout = QHBoxLayout()
        control_button_widget.setLayout(control_button_layout)

        self.ok_button = QPushButton('Start')
        self.ok_button.clicked.connect(self.accept)
        control_button_layout.addWidget(self.ok_button)

        self.cancel_button = QPushButton('Close')
        self.cancel_button.clicked.connect(self.reject)
        control_button_layout.addWidget(self.cancel_button)

        main_layout.addWidget(control_button_widget)

        container = QWidget()
        container.setLayout(main_layout)
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

    app.exec()
