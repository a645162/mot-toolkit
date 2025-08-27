"""预览窗口"""

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QGroupBox,
    QSplitter,
    QMessageBox,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent, QGuiApplication

from mot_toolkit.gui.isolate.ParallelMOTResultGallery.core.video_loader import (
    VideoFrameLoader,
)
from mot_toolkit.gui.isolate.ParallelMOTResultGallery.core.result_plotter import (
    ResultPlotter,
)
from mot_toolkit.gui.isolate.ParallelMOTResultGallery.gui.continuous_preview import (
    ContinuousPreviewWidget,
)
from mot_toolkit.utils.logs import get_logger

LOGGER = get_logger()


class PreviewWindow(QMainWindow):
    """预览窗口 - 用于显示并行对比结果"""

    def __init__(self, parent=None):
        super().__init__(None)  # 不设置parent，独立窗口
        self.setWindowTitle("MOT结果对比 - 预览")
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)

        self.config = {}
        self.current_sequence = ""
        self.current_frame = 0
        self.is_playing = False
        self.total_frames = 0

        self.video_loaders = {}  # {algorithm_name: VideoFrameLoader}
        self.frame_cache = {}  # {algorithm_name: {frame_idx: image_path}}
        self.result_loaders = {}  # {algorithm_name: MOTResultLoader}
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

        # 复制信息按钮
        self.copy_btn = QPushButton("复制信息")
        self.copy_btn.clicked.connect(self.copy_sequence_info)
        control_layout.addWidget(self.copy_btn)

        layout.addWidget(control_group)

        # 创建分割器
        self.splitter = QSplitter(Qt.Vertical)

        # 连续帧预览区域
        self.continuous_preview = ContinuousPreviewWidget()
        continuous_group = QGroupBox("连续帧预览")
        continuous_layout = QVBoxLayout(continuous_group)
        continuous_layout.addWidget(self.continuous_preview)

        # 添加到分割器
        self.splitter.addWidget(continuous_group)

        layout.addWidget(self.splitter)

    def setup_timer(self):
        """设置播放定时器"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)

    def setup_plotter(self):
        """设置绘制器"""
        pass

    def set_config(self, config: dict):
        """设置配置"""
        self.config = config
        self.setup_video_loaders()
        self.preview_frames = config.get("preview_frames", 5)

        # 设置绘制配置
        bbox_config = config.get("bbox_config", {})
        self.plotter.set_config(bbox_config)

        if hasattr(self, "continuous_preview"):
            self.continuous_preview.set_preview_frames(self.preview_frames)

    def set_sequence(self, sequence: str):
        """设置当前序列"""
        self.current_sequence = sequence
        self.sequence_label.setText(f"当前序列: {sequence}")
        self.load_sequence_data()

    def setup_video_loaders(self):
        """设置视频加载器"""
        self.video_loaders.clear()
        self.result_loaders.clear()

        algorithms = self.config.get("algorithms", {})
        sequence_paths = self.config.get("sequence_paths", {})

        for algo_name, algo_path in algorithms.items():
            if self.current_sequence in sequence_paths:
                seq_path = sequence_paths[self.current_sequence]
                loader = VideoFrameLoader()
                if loader.set_video(seq_path):
                    self.video_loaders[algo_name] = loader

                # 设置结果加载器
                from core.mot_loader import MOTResultLoader

                result_loader = MOTResultLoader()
                if result_loader.add_algorithm_directory(algo_path, algo_name):
                    self.result_loaders[algo_name] = result_loader

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
            max_frame = max(
                1, self.total_frames - self.config.get("preview_frames", 5) + 1
            )
            self.frame_spin.setMaximum(max_frame)
            self.frame_slider.setMaximum(max_frame)
            self.frame_label.setText(f"帧: 0/{max_frame}")

        self.current_frame = 0
        self.update_display()

        # 更新连续帧预览
        if hasattr(self, "continuous_preview"):
            self.continuous_preview.set_video_loaders(self.video_loaders)
            self.continuous_preview.set_result_loaders(self.result_loaders)
            self.continuous_preview.set_total_frames(self.total_frames)
            self.continuous_preview.set_current_frame(self.current_frame)
            self.continuous_preview.set_sequence(self.current_sequence)
            self.continuous_preview.set_preview_frames(
                self.config.get("preview_frames", 5)
            )

    def setup_preview_area(self):
        """设置预览区域 - 已移除传统预览"""
        pass

    def update_display(self):
        """更新显示 - 简化版本，只更新控制面板"""
        if not self.current_sequence or not self.video_loaders:
            LOGGER.debug("[PreviewWindow] 没有序列或视频加载器")
            return

        max_frame = max(1, self.total_frames - self.config.get("preview_frames", 5) + 1)
        self.frame_label.setText(f"帧: {self.current_frame + 1}/{max_frame}")
        self.frame_spin.setValue(self.current_frame + 1)
        self.frame_slider.setValue(self.current_frame + 1)

        LOGGER.debug(
            f"[PreviewWindow] 更新显示: 序列={self.current_sequence}, 帧={self.current_frame}"
        )

    def plot_results(self):
        """绘制结果 - 已移除"""
        pass

    def on_plot_progress(self, current, total):
        """绘制进度更新 - 已移除"""
        pass

    def on_plot_completed(self, output_dir):
        """绘制完成 - 已移除"""
        pass

    def on_plot_error(self, error_msg):
        """绘制错误 - 已移除"""
        pass

    def on_frame_changed(self, frame):
        """帧改变处理"""
        self.current_frame = frame - 1
        self.update_display()

        # 更新连续帧预览
        if hasattr(self, "continuous_preview"):
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

    def copy_sequence_info(self):
        """复制序列信息到剪贴板"""
        if not self.current_sequence:
            QMessageBox.warning(self, "警告", "请先选择序列")
            return
            
        # 获取当前序列名称
        sequence_name = self.current_sequence
        
        # 获取第一张图的名称
        first_frame_name = f"{self.current_frame + 1:08d}.jpg"
        
        # 获取连续帧数
        continuous_frames = self.config.get("preview_frames", 5)
        
        # 格式化信息为每行一种
        info_text = f"序列名称: {sequence_name}\n第一张图: {first_frame_name}\n连续帧数: {continuous_frames}"
        
        # 复制到剪贴板
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(info_text)
        
        # 弹框显示
        QMessageBox.information(
            self,
            "复制成功",
            f"已复制以下信息到剪贴板：\n\n{info_text}"
        )
        
        LOGGER.info(f"已复制到剪贴板:\n{info_text}")

    def closeEvent(self, event: QCloseEvent):
        """关闭事件"""
        self.stop_play()
        if hasattr(self, "plot_thread") and self.plot_thread.isRunning():
            self.plot_thread.quit()
            self.plot_thread.wait()
        super().closeEvent(event)
