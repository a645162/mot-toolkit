"""连续帧预览组件"""

import os
from typing import List, Optional, Dict
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QScrollArea, QGroupBox
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QPixmap, QImage, QPainter, QFont, QResizeEvent

from core.video_loader import VideoFrameLoader


class ContinuousPreviewWidget(QWidget):
    """连续帧预览组件 - 横向并排显示n张连续帧"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_loaders = {}  # {algorithm_name: VideoFrameLoader}
        self.current_frame = 0
        self.total_frames = 0
        self.preview_frames = 5  # 默认显示5张连续帧
        self.algorithm_labels = {}  # 算法名称标签
        self.frame_labels = {}  # 帧图像标签
        self.algo_name_width = 120  # 算法名称标签固定宽度
        
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
                        pixmap = QPixmap(image_path)
                        if not pixmap.isNull():
                            scaled_pixmap = pixmap.scaled(
                                image_width, image_height,
                                Qt.KeepAspectRatio,
                                Qt.SmoothTransformation
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