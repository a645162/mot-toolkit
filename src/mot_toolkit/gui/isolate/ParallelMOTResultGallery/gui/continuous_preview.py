"""连续帧预览组件"""

import os
import cv2
from typing import List, Optional, Dict
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QScrollArea,
    QGroupBox,
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QPixmap, QImage, QPainter, QFont, QResizeEvent

from mot_toolkit.gui.isolate.ParallelMOTResultGallery.core.video_loader import (
    VideoFrameLoader,
)
from mot_toolkit.gui.isolate.ParallelMOTResultGallery.core.result_plotter import (
    ResultPlotter,
)
from mot_toolkit.utils.logs import get_logger

LOGGER = get_logger()


class ContinuousPreviewWidget(QWidget):
    """连续帧预览组件 - 横向并排显示n张连续帧"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_loaders = {}  # {algorithm_name: VideoFrameLoader}
        self.result_loaders = {}  # {algorithm_name: MOTResultLoader}
        self.current_frame = 0
        self.total_frames = 0
        self.preview_frames = 5  # 默认显示5张连续帧
        self.algorithm_labels = {}  # 算法名称标签
        self.frame_labels = {}  # 帧图像标签
        self.algo_name_width = 120  # 算法名称标签固定宽度
        self.plotter = ResultPlotter()  # 添加绘制器

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setMinimumHeight(200)

        # 创建滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 创建内容widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(5)
        self.content_layout.setContentsMargins(5, 5, 5, 5)

        self.scroll_area.setWidget(self.content_widget)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scroll_area)

    def set_video_loaders(self, video_loaders: Dict[str, VideoFrameLoader]):
        """设置视频加载器"""
        self.video_loaders = video_loaders
        self.update_preview()

    def set_result_loaders(self, result_loaders: Dict[str, object]):
        """设置结果加载器"""
        self.result_loaders = result_loaders
        self.update_preview()

    def set_sequence(self, sequence: str):
        """设置当前序列"""
        self.current_sequence = sequence
        self.update_preview()

    def set_current_frame(self, frame: int):
        """设置当前帧"""
        self.current_frame = frame
        self.update_preview()

    def set_preview_frames(self, count: int):
        """设置预览帧数"""
        self.preview_frames = max(1, min(count, 10))  # 限制在1-10之间
        self.update_preview()

    def set_total_frames(self, total: int):
        """设置总帧数"""
        self.total_frames = total
        self.update_preview()

    def update_preview(self):
        """更新预览显示"""
        # 清除旧的控件
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if not self.video_loaders:
            return

        # 计算每张图片的宽度
        available_width = self.scroll_area.viewport().width() - 20  # 减去边距
        if available_width <= 0:
            available_width = 800

        # 算法名称固定宽度，剩余空间分配给图片
        image_total_width = available_width - self.algo_name_width - 20
        image_width = max(100, image_total_width // self.preview_frames)
        image_height = int(image_width * 0.75)  # 4:3比例

        # 添加表头
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(2)

        # 空白占位符（算法名称列）
        placeholder_label = QLabel()
        placeholder_label.setFixedWidth(self.algo_name_width)
        header_layout.addWidget(placeholder_label)

        # 添加帧名称到表头
        for i in range(self.preview_frames):
            frame_num = self.current_frame + i
            frame_label = QLabel(f"{frame_num:08d}.jpg")
            frame_label.setAlignment(Qt.AlignCenter)
            frame_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    background-color: #e0e0e0;
                    border: 1px solid #ccc;
                    padding: 5px;
                }
            """)
            frame_label.setFixedSize(image_width, 30)  # 固定高度为30
            header_layout.addWidget(frame_label)

        # 添加弹性空间
        header_layout.addStretch()
        self.content_layout.addWidget(header_widget)

        # 为每个算法创建一行
        for algo_name, loader in self.video_loaders.items():
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(2)

            # 算法名称标签（固定宽度）
            algo_label = QLabel(algo_name)
            algo_label.setFixedWidth(self.algo_name_width)
            algo_label.setAlignment(Qt.AlignCenter)
            algo_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    padding: 5px;
                }
            """)
            row_layout.addWidget(algo_label)

            # 连续帧图片
            for i in range(self.preview_frames):
                frame_num = self.current_frame + i
                if frame_num < self.total_frames:
                    image_path = loader.get_frame_path(frame_num)
                    if image_path and os.path.exists(image_path):
                        # 读取图像
                        img = cv2.imread(image_path)
                        if img is not None:
                            # 获取跟踪结果
                            results = []
                            if algo_name in self.result_loaders:
                                # 获取序列名称 - 需要从父窗口获取
                                sequence_name = getattr(self, "current_sequence", "")
                                if sequence_name:
                                    results = self.result_loaders[
                                        algo_name
                                    ].get_results_for_frame(
                                        sequence_name, algo_name, frame_num
                                    )

                            # 绘制跟踪结果
                            if results:
                                img = self.plotter.draw_results_on_frame(
                                    img, results, algo_name
                                )

                            # 转换为QPixmap
                            h, w, ch = img.shape
                            bytes_per_line = ch * w
                            q_img = QImage(
                                img.data, w, h, bytes_per_line, QImage.Format_RGB888
                            ).rgbSwapped()
                            pixmap = QPixmap.fromImage(q_img)

                            if not pixmap.isNull():
                                scaled_pixmap = pixmap.scaled(
                                    image_width,
                                    image_height,
                                    Qt.KeepAspectRatio,
                                    Qt.SmoothTransformation,
                                )

                                frame_label = QLabel()
                                frame_label.setPixmap(scaled_pixmap)
                                frame_label.setFixedSize(image_width, image_height)
                                frame_label.setStyleSheet("""
                                    QLabel {
                                        border: 1px solid #ddd;
                                        background-color: white;
                                    }
                                """)
                                frame_label.setToolTip(f"帧 {frame_num + 1}")
                            else:
                                frame_label = QLabel("转换失败")
                                frame_label.setFixedSize(image_width, image_height)
                        else:
                            frame_label = QLabel("加载失败")
                            frame_label.setFixedSize(image_width, image_height)
                    else:
                        frame_label = QLabel("无图片")
                        frame_label.setFixedSize(image_width, image_height)
                else:
                    frame_label = QLabel("超出范围")
                    frame_label.setFixedSize(image_width, image_height)

                row_layout.addWidget(frame_label)

            # 添加弹性空间
            row_layout.addStretch()
            self.content_layout.addWidget(row_widget)

    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        self.update_preview()
