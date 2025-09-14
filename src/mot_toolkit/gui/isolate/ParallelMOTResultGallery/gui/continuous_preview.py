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
from mot_toolkit.datatype.dataset.danceteck_gt import DanceTrackGTReader, find_gt_file
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
        self.current_sequence = ""  # 当前序列名称
        self.preview_frames = 5  # 默认显示5张连续帧
        self.algorithm_labels = {}  # 算法名称标签
        self.frame_labels = {}  # 帧图像标签
        self.algo_name_width = 120  # 算法名称标签固定宽度
        self.plotter = ResultPlotter()  # 添加绘制器
        self.gt_reader = DanceTrackGTReader()  # GT读取器
        self.show_gt = False  # 是否显示GT
        self.gt_loaded = False  # GT是否已加载

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

    def set_plotter_config(self, config: dict):
        """设置绘制器配置"""
        if hasattr(self, 'plotter') and self.plotter:
            self.plotter.set_config(config)
            
        # 更新GT显示设置
        self.show_gt = config.get("show_gt", False)
        LOGGER.debug(f"GT显示设置: {self.show_gt}")
        
        # 如果启用GT显示，尝试加载GT数据
        if self.show_gt and not self.gt_loaded:
            self._try_load_gt_data()

    def set_sequence(self, sequence: str):
        """设置当前序列"""
        self.current_sequence = sequence
        self.gt_loaded = False  # 重置GT加载状态
        if self.show_gt:
            self._try_load_gt_data()
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

    def set_render_mode(self, mode: str):
        """设置渲染模式 - 已弃用，保持兼容性"""
        # 不再使用渲染模式，统一使用按需渲染
        self.update_preview()

    def _try_load_gt_data(self):
        """尝试加载GT数据"""
        if not hasattr(self, 'current_sequence') or not self.current_sequence:
            return
            
        # 从父窗口获取序列路径
        parent = self.parent()
        while parent and not hasattr(parent, 'config'):
            parent = parent.parent()
            
        if parent and hasattr(parent, 'config'):
            sequence_paths = parent.config.get("sequence_paths", {})
            seq_path = sequence_paths.get(self.current_sequence, "")
            if seq_path:
                gt_file = find_gt_file(seq_path)
                if gt_file:
                    LOGGER.info(f"找到GT文件: {gt_file}")
                    if self.gt_reader.load_gt_file(gt_file):
                        self.gt_loaded = True
                        LOGGER.info(f"GT数据加载成功，总帧数: {len(self.gt_reader.gt_data)}")
                    else:
                        LOGGER.warning("GT数据加载失败")
                else:
                    LOGGER.warning(f"在序列目录中未找到GT文件: {seq_path}")
            else:
                LOGGER.warning(f"未找到序列路径: {self.current_sequence}")

    def update_preview(self):
        """更新预览显示"""
        # 清除旧的控件
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if not self.video_loaders:
            return
            
        # 如果需要显示GT但未加载，尝试加载
        if self.show_gt and not self.gt_loaded:
            self._try_load_gt_data()

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

        # 首先添加GT行（如果启用GT显示且已加载GT数据）
        if self.show_gt and self.gt_loaded:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(2)

            # GT名称标签（固定宽度）
            gt_label = QLabel("GT")
            gt_label.setFixedWidth(self.algo_name_width)
            gt_label.setAlignment(Qt.AlignCenter)
            gt_label.setStyleSheet("""
                QLabel {
                    font-weight: bold;
                    background-color: #e0ffe0;
                    border: 1px solid #4CAF50;
                    padding: 5px;
                    color: #2E7D32;
                }
            """)
            row_layout.addWidget(gt_label)

            # 连续帧图片（GT数据）
            for i in range(self.preview_frames):
                frame_num = self.current_frame + i
                if frame_num < self.total_frames:
                    frame_label = self._render_gt_frame(frame_num, image_width, image_height)
                else:
                    frame_label = QLabel("超出范围")
                    frame_label.setFixedSize(image_width, image_height)

                row_layout.addWidget(frame_label)

            # 添加弹性空间
            row_layout.addStretch()
            self.content_layout.addWidget(row_widget)

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
                    # 统一使用按需渲染
                    frame_label = self._render_algorithm_frame(algo_name, frame_num, image_width, image_height, loader)
                else:
                    frame_label = QLabel("超出范围")
                    frame_label.setFixedSize(image_width, image_height)

                row_layout.addWidget(frame_label)

            # 添加弹性空间
            row_layout.addStretch()
            self.content_layout.addWidget(row_widget)

    def _render_realtime(self, algo_name, frame_num, image_width, image_height, loader):
        """实时渲染帧"""
        image_path = loader.get_frame_path(frame_num)
        if image_path and os.path.exists(image_path):
            # 读取图像
            img = cv2.imread(image_path)
            if img is not None:
                # 获取渲染配置
                render_config = self._get_render_config()
                
                # 根据渲染模式处理图像
                if render_config["render_mode"] == "limit_resolution":
                    img = self._limit_resolution(img, render_config)
                
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
                        LOGGER.debug(f"获取到 {len(results)} 个跟踪结果")

                # 绘制跟踪结果
                if results:
                    LOGGER.debug(f"开始绘制 {len(results)} 个结果")
                    img = self.plotter.draw_results_on_frame(
                        img, results, algo_name
                    )
                    LOGGER.debug("绘制完成")

                # 绘制GT结果（如果启用）
                if self.show_gt and self.gt_loaded:
                    gt_results = self.gt_reader.convert_to_mot_format(frame_num)
                    if gt_results:
                        LOGGER.debug(f"开始绘制 {len(gt_results)} 个GT结果")
                        # 使用不同的颜色绘制GT（例如绿色）
                        img = self.plotter.draw_results_on_frame(
                            img, gt_results, "GT",
                            color=(0, 255, 0),  # 绿色
                            thickness=3  # 更粗的线
                        )
                        LOGGER.debug("GT绘制完成")

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
                    return frame_label
                else:
                    frame_label = QLabel("转换失败")
                    frame_label.setFixedSize(image_width, image_height)
                    return frame_label
            else:
                frame_label = QLabel("加载失败")
                frame_label.setFixedSize(image_width, image_height)
                return frame_label
        else:
            frame_label = QLabel("无图片")
            frame_label.setFixedSize(image_width, image_height)
            return frame_label
            
    def _get_render_config(self):
        """获取渲染配置"""
        # 从父窗口获取配置
        parent = self.parent()
        while parent and not hasattr(parent, 'config'):
            parent = parent.parent()
            
        if parent and hasattr(parent, 'config'):
            config = parent.config
            render_config = config.get("render_config", {})
            return {
                "render_mode": render_config.get("render_mode", "limit_resolution"),
                "max_width": render_config.get("max_width", 800),
                "max_height": render_config.get("max_height", 600),
                "quality": render_config.get("quality", 85)
            }
        else:
            # 默认配置
            return {
                "render_mode": "limit_resolution",
                "max_width": 800,
                "max_height": 600,
                "quality": 85
            }
            
    def _limit_resolution(self, img, render_config):
        """限制图像分辨率"""
        h, w = img.shape[:2]
        max_width = render_config["max_width"]
        max_height = render_config["max_height"]
        
        if w > max_width or h > max_height:
            # 计算缩放比例
            scale = min(max_width / w, max_height / h)
            new_width = int(w * scale)
            new_height = int(h * scale)
            
            # 使用高质量缩放
            img = cv2.resize(img, (new_width, new_height),
                           interpolation=cv2.INTER_LANCZOS4)
            
        return img
            
        
    def _render_algorithm_frame(self, algo_name, frame_num, image_width, image_height, loader):
        """按需渲染算法帧"""
        # 构建渲染结果保存路径：算法目录/序列名称/帧号.jpg
        from pathlib import Path
        
        # 获取算法目录
        parent = self.parent()
        while parent and not hasattr(parent, 'config'):
            parent = parent.parent()
            
        if not parent or not hasattr(parent, 'config'):
            return self._render_realtime(algo_name, frame_num, image_width, image_height, loader)
            
        config = parent.config
        algorithms = config.get("algorithms", {})
        algo_path = algorithms.get(algo_name, "")
        
        if not algo_path:
            return self._render_realtime(algo_name, frame_num, image_width, image_height, loader)
            
        # 创建序列目录
        seq_dir = Path(algo_path) / self.current_sequence
        seq_dir.mkdir(parents=True, exist_ok=True)
        
        # 检查是否已渲染
        rendered_path = seq_dir / f"{frame_num:08d}.jpg"
        if rendered_path.exists():
            # 从缓存加载
            try:
                pixmap = QPixmap(str(rendered_path))
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
                    return frame_label
            except Exception as e:
                LOGGER.error(f"加载渲染图像失败: {e}")
        
        # 需要重新渲染
        return self._render_and_save_frame(algo_name, frame_num, image_width, image_height, loader, rendered_path)

    def _render_and_save_frame(self, algo_name, frame_num, image_width, image_height, loader, output_path):
        """渲染并保存帧"""
        # 使用实时渲染逻辑
        frame_label = self._render_realtime(algo_name, frame_num, image_width, image_height, loader)
        
        # 保存渲染结果（如果渲染成功）
        if hasattr(frame_label, 'pixmap') and frame_label.pixmap():
            try:
                # 将QPixmap保存为图像文件
                frame_label.pixmap().save(str(output_path))
                LOGGER.debug(f"已保存渲染结果: {output_path}")
            except Exception as e:
                LOGGER.error(f"保存渲染结果失败: {e}")
                
        return frame_label

    def _render_gt_frame(self, frame_num, image_width, image_height):
        """渲染GT帧"""
        if not hasattr(self, 'video_loaders') or not self.video_loaders:
            frame_label = QLabel("无加载器")
            frame_label.setFixedSize(image_width, image_height)
            return frame_label
            
        # 获取第一个视频加载器来加载原始图像
        first_loader = next(iter(self.video_loaders.values()))
        image_path = first_loader.get_frame_path(frame_num)
        if not image_path or not os.path.exists(image_path):
            frame_label = QLabel("无图片")
            frame_label.setFixedSize(image_width, image_height)
            return frame_label
            
        # 读取图像
        img = cv2.imread(image_path)
        if img is None:
            frame_label = QLabel("加载失败")
            frame_label.setFixedSize(image_width, image_height)
            return frame_label
            
        # 绘制GT结果
        if self.show_gt and self.gt_loaded:
            gt_results = self.gt_reader.convert_to_mot_format(frame_num)
            if gt_results:
                LOGGER.debug(f"开始绘制 {len(gt_results)} 个GT结果")
                # 使用绿色绘制GT
                img = self.plotter.draw_results_on_frame(
                    img, gt_results, "GT",
                    color=(0, 255, 0),  # 绿色
                    thickness=3  # 更粗的线
                )
                LOGGER.debug("GT绘制完成")
        
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
            frame_label.setToolTip(f"帧 {frame_num + 1} (GT)")
            return frame_label
        else:
            frame_label = QLabel("转换失败")
            frame_label.setFixedSize(image_width, image_height)
            return frame_label

    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        self.update_preview()
