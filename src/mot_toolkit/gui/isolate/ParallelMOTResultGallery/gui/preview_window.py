"""预览窗口"""

import os
import cv2
import numpy as np
from typing import List, Dict, Optional
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QGroupBox,
    QScrollArea,
    QProgressBar,
    QMessageBox,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPainter, QColor, QFont

from mot_toolkit.gui.isolate.ParallelMOTResultGallery.core import (
    VideoFrameLoader,
    MOTResultParser,
    MOTResultLoader,
)


class VideoDisplayWidget(QWidget):
    """视频显示组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.frames = []
        self.results = {}  # {algorithm_name: {frame_id: results}}
        self.algorithms = []
        self.display_size = (640, 360)
        self.setMinimumSize(650, 400)

    def set_frames_and_results(
        self, frames: List[np.ndarray], results: Dict[str, Dict[int, List[Dict]]]
    ):
        """设置帧和结果"""
        self.frames = frames
        self.results = results
        self.algorithms = list(results.keys())
        self.update()

    def paintEvent(self, event):
        """绘制事件"""
        if not self.frames:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 计算布局
        frame_height = self.display_size[1]
        total_height = len(self.algorithms) * len(self.frames) * (frame_height + 40)

        # 调整组件大小
        self.setFixedHeight(max(total_height, 400))

        # 绘制每个算法的帧序列
        y_offset = 10
        for algorithm in self.algorithms:
            algorithm_results = self.results.get(algorithm, {})

            # 绘制算法名称
            painter.setFont(QFont("Arial", 14, QFont.Bold))
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(10, y_offset + 20, f"算法: {algorithm}")
            y_offset += 30

            # 绘制该算法的5帧
            for i, frame in enumerate(self.frames):
                if i < len(self.frames):
                    # 调整帧大小
                    display_frame = cv2.resize(frame, self.display_size)

                    # 绘制跟踪结果
                    frame_results = algorithm_results.get(i, [])
                    display_frame = self.draw_tracking_results(
                        display_frame, frame_results
                    )

                    # 转换为QImage
                    height, width, channel = display_frame.shape
                    bytes_per_line = 3 * width
                    q_img = QImage(
                        display_frame.data,
                        width,
                        height,
                        bytes_per_line,
                        QImage.Format_RGB888,
                    ).rgbSwapped()

                    # 绘制图像
                    painter.drawImage(10, y_offset, q_img)

                    # 绘制帧号
                    painter.setFont(QFont("Arial", 12))
                    painter.setPen(QColor(255, 255, 255))
                    painter.drawText(20, y_offset + 25, f"帧: {i + 1}")

                    y_offset += frame_height + 10

    def draw_tracking_results(
        self, frame: np.ndarray, results: List[Dict]
    ) -> np.ndarray:
        """在帧上绘制跟踪结果"""
        for result in results:
            bbox = result["bbox"]
            track_id = result["track_id"]

            x, y, w, h = map(int, bbox)
            color = self.get_color(track_id)

            # 绘制边界框
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

            # 绘制ID和置信度
            label = f"{track_id}"
            if "confidence" in result:
                label += f":{result['confidence']:.2f}"

            cv2.putText(
                frame,
                label,
                (x, max(y - 5, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
            )

        return frame

    def get_color(self, track_id: int) -> tuple:
        """根据跟踪ID生成颜色"""
        # 使用固定的颜色映射
        colors = [
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
            (255, 255, 0),
            (255, 0, 255),
            (0, 255, 255),
            (128, 0, 0),
            (0, 128, 0),
            (0, 0, 128),
            (128, 128, 0),
            (128, 0, 128),
            (0, 128, 128),
        ]
        return colors[track_id % len(colors)]


class PreviewWindow(QMainWindow):
    """预览窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MOT结果预览")
        self.setGeometry(200, 200, 1200, 800)

        # 核心组件
        self.video_loader = VideoFrameLoader()
        self.result_parser = MOTResultParser()
        self.mot_loader = MOTResultLoader()

        # 状态
        self.current_sequence = None
        self.current_frame = 0
        self.is_playing = False

        self.init_ui()
        self.setup_timer()

    def init_ui(self):
        """初始化UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # 控制面板
        control_group = QGroupBox("播放控制")
        control_layout = QHBoxLayout(control_group)

        self.play_btn = QPushButton("播放")
        self.play_btn.clicked.connect(self.toggle_play)
        control_layout.addWidget(self.play_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_playback)
        control_layout.addWidget(self.stop_btn)

        self.prev_btn = QPushButton("上一帧")
        self.prev_btn.clicked.connect(self.previous_frame)
        control_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("下一帧")
        self.next_btn.clicked.connect(self.next_frame)
        control_layout.addWidget(self.next_btn)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        control_layout.addWidget(self.progress_bar)

        # 帧号显示
        self.frame_label = QLabel("帧: 0/0")
        control_layout.addWidget(self.frame_label)

        layout.addWidget(control_group)

        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # 显示组件
        self.display_widget = VideoDisplayWidget()
        scroll_area.setWidget(self.display_widget)

        layout.addWidget(scroll_area)

    def setup_timer(self):
        """设置定时器"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.setInterval(100)  # 100ms

    def set_config(self, config: dict):
        """设置配置"""
        self.mot_loader = MOTResultLoader()

        algorithms = config.get("algorithms", {})
        for name, path in algorithms.items():
            self.mot_loader.add_algorithm_directory(path, name)

        self.dataset_path = config.get("dataset_path", "")

    def set_sequence(self, sequence: str):
        """设置当前序列"""
        self.current_sequence = sequence
        if not sequence or not self.dataset_path:
            return

        # 查找视频文件
        video_path = self.find_video_file(sequence)
        if video_path:
            if self.video_loader.set_video(video_path):
                self.current_frame = 0
                self.update_progress_bar()
                self.update_display()
            else:
                QMessageBox.warning(self, "警告", f"无法加载视频: {video_path}")
        else:
            QMessageBox.warning(self, "警告", f"未找到序列 {sequence} 的视频文件")

    def find_video_file(self, sequence: str) -> Optional[str]:
        """查找视频文件"""
        if not self.dataset_path:
            return None

        # DanceTrack格式
        possible_paths = [
            os.path.join(self.dataset_path, "train", sequence, f"{sequence}.mp4"),
            os.path.join(self.dataset_path, "val", sequence, f"{sequence}.mp4"),
            os.path.join(self.dataset_path, "test", sequence, f"{sequence}.mp4"),
            os.path.join(self.dataset_path, f"{sequence}.mp4"),
            os.path.join(self.dataset_path, f"{sequence}.avi"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        return None

    def toggle_play(self):
        """切换播放状态"""
        if self.is_playing:
            self.timer.stop()
            self.play_btn.setText("播放")
            self.is_playing = False
        else:
            if self.current_sequence:
                self.timer.start()
                self.play_btn.setText("暂停")
                self.is_playing = True

    def stop_playback(self):
        """停止播放"""
        self.timer.stop()
        self.play_btn.setText("播放")
        self.is_playing = False
        self.current_frame = 0
        self.update_display()

    def previous_frame(self):
        """上一帧"""
        if self.current_frame > 0:
            self.current_frame -= 1
            self.update_display()

    def next_frame(self):
        """下一帧"""
        if self.current_frame < self.video_loader.get_total_frames() - 5:
            self.current_frame += 1
            self.update_display()

    def update_frame(self):
        """更新帧"""
        if self.current_frame < self.video_loader.get_total_frames() - 5:
            self.current_frame += 1
            self.update_display()
        else:
            self.stop_playback()

    def update_display(self):
        """更新显示"""
        if not self.current_sequence:
            return

        # 获取5帧
        frames = self.video_loader.get_frames_range(self.current_frame, 5)
        if not frames:
            return

        # 获取所有算法的结果
        all_results = {}
        algorithms = self.mot_loader.get_algorithms()

        for algorithm in algorithms:
            result_path = self.mot_loader.get_result_path(
                self.current_sequence, algorithm
            )
            if result_path:
                results = self.result_parser.parse_results_for_frames(
                    result_path, self.current_frame, 5
                )
                all_results[algorithm] = results

        # 更新显示
        self.display_widget.set_frames_and_results(frames, all_results)
        self.update_progress_bar()

    def update_progress_bar(self):
        """更新进度条"""
        total = self.video_loader.get_total_frames()
        if total > 0:
            self.progress_bar.setMaximum(total - 5)
            self.progress_bar.setValue(self.current_frame)
            self.frame_label.setText(f"帧: {self.current_frame}/{total - 5}")

    def closeEvent(self, event):
        """关闭事件"""
        self.timer.stop()
        self.video_loader.release()
        super().closeEvent(event)
