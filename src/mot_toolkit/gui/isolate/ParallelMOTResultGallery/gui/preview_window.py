"""预览窗口"""

import os
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QSlider,
    QSpinBox,
    QGroupBox,
    QMessageBox,
    QProgressDialog,
    QSplitter,
)
from PySide6.QtCore import Qt, QTimer, QThread
from PySide6.QtGui import QPixmap, QImage, QCloseEvent

from core.video_loader import VideoFrameLoader
from core.result_plotter import ResultPlotter, PlotThread
from gui.continuous_preview import ContinuousPreviewWidget


class PreviewWindow(QMainWindow):
    """预览窗口 - 用于显示并行对比结果"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MOT结果对比 - 预览")
        self.setGeometry(200, 200, 1200, 800)

        self.config = {}
        self.current_sequence = ""
        self.current_frame = 0
        self.is_playing = False
        self.total_frames = 0

        self.video_loaders = {}  # {algorithm_name: VideoFrameLoader}
        self.frame_cache = {}  # {algorithm_name: {frame_idx: image_path}}
        self.plotter = ResultPlotter()

        self.init_ui()
        self.setup_timer()
        self.setup_plotter()

    def init_ui(self):
        """初始化UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # 控制面板
        control_group = QGroupBox("控制面板")
        control_layout = QHBoxLayout(control_group)

        # 序列选择
        self.sequence_label = QLabel("当前序列:")
        control_layout.addWidget(self.sequence_label)

        # 帧控制
        self.frame_label = QLabel("帧: 0/0")
        control_layout.addWidget(self.frame_label)

        self.frame_spin = QSpinBox()
        self.frame_spin.setMinimum(1)
        self.frame_spin.valueChanged.connect(self.on_frame_changed)
        control_layout.addWidget(self.frame_spin)

        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setMinimum(1)
        self.frame_slider.valueChanged.connect(self.on_frame_changed)
        control_layout.addWidget(self.frame_slider)

        # 播放控制
        self.play_btn = QPushButton("播放")
        self.play_btn.clicked.connect(self.toggle_play)
        control_layout.addWidget(self.play_btn)

        # 绘制按钮
        self.plot_btn = QPushButton("绘制结果")
        self.plot_btn.clicked.connect(self.plot_results)
        control_layout.addWidget(self.plot_btn)

        layout.addWidget(control_group)

        # 创建分割器
        self.splitter = QSplitter(Qt.Vertical)
        
        # 传统预览区域
        self.traditional_preview = QWidget()
        traditional_layout = QVBoxLayout(self.traditional_preview)
        
        # 传统预览区域
        preview_group = QGroupBox("传统预览")
        preview_layout = QHBoxLayout(preview_group)
        preview_layout.setSpacing(10)
        self.preview_labels = {}  # {algorithm_name: QLabel}
        self.algo_labels = {}  # {algorithm_name: QLabel}
        traditional_layout.addWidget(preview_group)
        
        # 连续帧预览区域
        self.continuous_preview = ContinuousPreviewWidget()
        continuous_group = QGroupBox("连续帧预览")
        continuous_layout = QVBoxLayout(continuous_group)
        continuous_layout.addWidget(self.continuous_preview)
        
        # 添加到分割器
        self.splitter.addWidget(self.traditional_preview)
        self.splitter.addWidget(continuous_group)
        
        layout.addWidget(self.splitter)

    def setup_timer(self):
        """设置播放定时器"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)

    def setup_plotter(self):
        """设置绘制器"""
        self.plotter.progress_updated.connect(self.on_plot_progress)
        self.plotter.plot_completed.connect(self.on_plot_completed)
        self.plotter.plot_error.connect(self.on_plot_error)

    def set_config(self, config: dict):
        """设置配置"""
        self.config = config
        self.setup_video_loaders()
        self.preview_frames = config.get("preview_frames", 5)
        if hasattr(self, 'continuous_preview'):
            self.continuous_preview.set_preview_frames(self.preview_frames)

    def set_sequence(self, sequence: str):
        """设置当前序列"""
        self.current_sequence = sequence
        self.sequence_label.setText(f"当前序列: {sequence}")
        self.load_sequence_data()

    def setup_video_loaders(self):
        """设置视频加载器"""
        self.video_loaders.clear()
        
        algorithms = self.config.get("algorithms", {})
        sequence_paths = self.config.get("sequence_paths", {})
        
        for algo_name, algo_path in algorithms.items():
            if self.current_sequence in sequence_paths:
                seq_path = sequence_paths[self.current_sequence]
                loader = VideoFrameLoader()
                if loader.set_video(seq_path):
                    self.video_loaders[algo_name] = loader

    def load_sequence_data(self):
        """加载序列数据"""
        if not self.current_sequence:
            return
            
        self.setup_video_loaders()
        self.setup_preview_area()
        
        # 获取总帧数
        if self.video_loaders:
            first_loader = next(iter(self.video_loaders.values()))
            self.total_frames = first_loader.get_total_frames()
            max_frame = max(1, self.total_frames - self.config.get("preview_frames", 5) + 1)
            self.frame_spin.setMaximum(max_frame)
            self.frame_slider.setMaximum(max_frame)
            self.frame_label.setText(f"帧: 0/{max_frame}")
        
        self.current_frame = 0
        self.update_display()
        
        # 更新连续帧预览
        if hasattr(self, 'continuous_preview'):
            self.continuous_preview.set_video_loaders(self.video_loaders)
            self.continuous_preview.set_total_frames(self.total_frames)
            self.continuous_preview.set_current_frame(self.current_frame)
            self.continuous_preview.set_preview_frames(self.config.get("preview_frames", 5))

    def setup_preview_area(self):
        """设置预览区域"""
        # 清除旧的预览
        if hasattr(self, 'preview_labels'):
            for label in self.preview_labels.values():
                label.setParent(None)
        if hasattr(self, 'algo_labels'):
            for label in self.algo_labels.values():
                label.setParent(None)
            
        self.preview_labels = {}
        self.algo_labels = {}
        
        # 获取传统预览区域的布局
        preview_group = self.findChild(QGroupBox, "preview_group")
        if preview_group:
            preview_layout = preview_group.layout()
            if preview_layout:
                # 清除旧的控件
                for i in reversed(range(preview_layout.count())):
                    widget = preview_layout.itemAt(i).widget()
                    if widget:
                        widget.setParent(None)
                
                # 创建新的预览标签
                algorithms = list(self.video_loaders.keys())
                for algo_name in algorithms:
                    # 算法名称标签
                    algo_label = QLabel(algo_name)
                    algo_label.setAlignment(Qt.AlignCenter)
                    algo_label.setStyleSheet("font-weight: bold; font-size: 14px;")
                    preview_layout.addWidget(algo_label)
                    self.algo_labels[algo_name] = algo_label
                    
                    # 预览图像标签
                    preview_label = QLabel()
                    preview_label.setAlignment(Qt.AlignCenter)
                    preview_label.setMinimumSize(300, 200)
                    preview_label.setStyleSheet("border: 1px solid gray;")
                    preview_layout.addWidget(preview_label)
                    self.preview_labels[algo_name] = preview_label

    def update_display(self):
        """更新显示"""
        if not self.current_sequence or not self.video_loaders:
            return
            
        self.frame_label.setText(f"帧: {self.current_frame + 1}/{self.total_frames}")
        self.frame_spin.setValue(self.current_frame + 1)
        self.frame_slider.setValue(self.current_frame + 1)
        
        for algo_name, loader in self.video_loaders.items():
            if algo_name in self.preview_labels:
                image_path = loader.get_frame_path(self.current_frame)
                if image_path and os.path.exists(image_path):
                    pixmap = QPixmap(image_path)
                    if not pixmap.isNull():
                        # 缩放以适应标签
                        scaled_pixmap = pixmap.scaled(
                            self.preview_labels[algo_name].size(),
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation
                        )
                        self.preview_labels[algo_name].setPixmap(scaled_pixmap)
                        
                        # 显示文件名和帧数
                        filename = os.path.basename(image_path)
                        self.preview_labels[algo_name].setToolTip(
                            f"文件: {filename}\n帧: {self.current_frame + 1}/{self.total_frames}"
                        )

    def plot_results(self):
        """绘制结果"""
        if not self.config.get("algorithms") or not self.config.get("sequence_paths"):
            QMessageBox.warning(self, "警告", "请先添加算法和设置数据集")
            return
        
        # 选择输出目录
        from PySide6.QtWidgets import QFileDialog
        output_dir = QFileDialog.getExistingDirectory(
            self, "选择输出目录", "", QFileDialog.ShowDirsOnly
        )
        
        if not output_dir:
            return
        
        # 显示进度对话框
        self.progress_dialog = QProgressDialog("正在绘制结果...", "取消", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.show()
        
        # 启动绘制线程
        self.plot_thread = PlotThread(self.plotter, self.config, output_dir)
        self.plot_thread.finished.connect(self.progress_dialog.close)
        self.plot_thread.start()
        
        QMessageBox.information(
            self, "绘制", f"结果绘制已开始，将保存到: {output_dir}"
        )

    def on_plot_progress(self, current, total):
        """绘制进度更新"""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.setMaximum(total)
            self.progress_dialog.setValue(current)

    def on_plot_completed(self, output_dir):
        """绘制完成"""
        QMessageBox.information(
            self, "完成", f"结果绘制完成！\n输出目录: {output_dir}"
        )

    def on_plot_error(self, error_msg):
        """绘制错误"""
        QMessageBox.warning(self, "错误", f"绘制失败: {error_msg}")

    def on_frame_changed(self, frame):
        """帧改变处理"""
        self.current_frame = frame - 1
        self.update_display()
        
        # 更新连续帧预览
        if hasattr(self, 'continuous_preview'):
            self.continuous_preview.set_current_frame(self.current_frame)

    def next_frame(self):
        """下一帧"""
        if self.current_frame < self.total_frames - 1:
            self.current_frame += 1
            self.update_display()
        else:
            self.stop_play()

    def toggle_play(self):
        """切换播放状态"""
        if self.is_playing:
            self.stop_play()
        else:
            self.start_play()

    def start_play(self):
        """开始播放"""
        if self.total_frames > 0:
            self.is_playing = True
            self.play_btn.setText("暂停")
            self.timer.start(100)  # 100ms间隔

    def stop_play(self):
        """停止播放"""
        self.is_playing = False
        self.play_btn.setText("播放")
        self.timer.stop()

    def closeEvent(self, event: QCloseEvent):
        """关闭事件"""
        self.stop_play()
        if hasattr(self, 'plot_thread') and self.plot_thread.isRunning():
            self.plot_thread.quit()
            self.plot_thread.wait()
        super().closeEvent(event)
