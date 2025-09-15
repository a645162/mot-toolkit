"""高清渲染导出窗口 - 支持多进程网格布局输出"""

import os
import cv2
import numpy as np
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QFileDialog,
    QMessageBox,
    QTextEdit,
    QGroupBox,
    QLineEdit,
    QSpinBox,
)
from PySide6.QtCore import Qt, QThread, Signal
from mot_toolkit.utils.logs import get_logger

LOGGER = get_logger()


def process_frame_group(args):
    """处理单个帧组的函数（用于多进程）"""
    try:
        config, sequence_name, start_frame, preview_frames, output_dir = args
        
        from mot_toolkit.gui.isolate.ParallelMOTResultGallery.core.video_loader import VideoFrameLoader
        from mot_toolkit.gui.isolate.ParallelMOTResultGallery.core.result_plotter import ResultPlotter
        
        algorithms = config.get("algorithms", {})
        sequence_paths = config.get("sequence_paths", {})
        render_config = config.get("render_config", {})
        
        if sequence_name not in sequence_paths:
            return start_frame, False, f"序列 {sequence_name} 不存在"
            
        seq_path = sequence_paths[sequence_name]
        
        # 创建视频加载器
        loader = VideoFrameLoader()
        if not loader.set_video(seq_path):
            return start_frame, False, "无法加载序列视频"
            
        total_frames = loader.get_total_frames()
        if total_frames == 0:
            return start_frame, False, "序列中没有帧"
            
        # 创建结果绘制器并设置配置
        plotter = ResultPlotter()
        bbox_config = config.get("bbox_config", {})
        # 确保配置正确设置
        plotter_config = {
            "show_bbox": bbox_config.get("show_bbox", True),
            "show_id": bbox_config.get("show_id", True),
            "bbox_thickness": bbox_config.get("bbox_thickness", 2),
            "fill_alpha": bbox_config.get("fill_alpha", 0.3),
            "show_fill": bbox_config.get("show_fill", True),
        }
        plotter.set_config(plotter_config)
        LOGGER.debug(f"绘制器配置: {plotter_config}")
        
        # 创建网格图像
        grid_image = create_grid_image(
            algorithms, loader, plotter, sequence_name, 
            start_frame, preview_frames, render_config
        )
        
        if grid_image is not None:
            # 保存网格图像
            output_path = Path(output_dir) / f"grid_{start_frame:08d}.jpg"
            cv2.imwrite(str(output_path), grid_image, 
                       [cv2.IMWRITE_JPEG_QUALITY, render_config.get("quality", 85)])
            return start_frame, True, f"成功保存网格图像: {output_path.name}"
        else:
            return start_frame, False, f"创建网格图像失败: 起始帧 {start_frame}"
            
    except Exception as e:
        return start_frame, False, f"处理帧组 {start_frame} 失败: {str(e)}"


def create_grid_image(algorithms, loader, plotter, sequence_name, start_frame, preview_frames, render_config):
    """创建网格图像"""
    try:
        # 获取所有算法的帧图像
        all_frames = []
        
        for algo_name, algo_path in algorithms.items():
            algo_frames = []
            for i in range(preview_frames):
                frame_num = start_frame + i
                if frame_num >= loader.get_total_frames():
                    break
                    
                # 获取原始图像
                frame = loader.get_frame(frame_num)
                if frame is None:
                    continue
                    
                # 应用渲染配置
                if render_config.get("render_mode") == "limit_resolution":
                    frame = limit_resolution(frame, render_config)
                
                # 获取跟踪结果
                results = get_tracking_results(algo_path, algo_name, sequence_name, frame_num)
                
                # 绘制跟踪结果
                if results:
                    frame = plotter.draw_results_on_frame(frame, results, algo_name)
                
                algo_frames.append(frame)
            
            if algo_frames:
                all_frames.append(algo_frames)
        
        if not all_frames:
            return None
            
        # 创建网格布局
        rows = len(all_frames)  # 每个算法一行
        cols = min(len(frames) for frames in all_frames)  # 取最小的帧数
        
        # 获取第一张图像的尺寸
        sample_height, sample_width = all_frames[0][0].shape[:2]
        
        # 创建网格画布
        grid_height = rows * sample_height
        grid_width = cols * sample_width
        grid_image = np.zeros((grid_height, grid_width, 3), dtype=np.uint8)
        
        # 填充网格
        for row, algo_frames in enumerate(all_frames):
            for col in range(cols):
                if col < len(algo_frames):
                    frame = algo_frames[col]
                    y_start = row * sample_height
                    y_end = y_start + sample_height
                    x_start = col * sample_width
                    x_end = x_start + sample_width
                    
                    # 调整图像尺寸以匹配网格单元格
                    if frame.shape[:2] != (sample_height, sample_width):
                        frame = cv2.resize(frame, (sample_width, sample_height))
                        
                    grid_image[y_start:y_end, x_start:x_end] = frame
        
        return grid_image
        
    except Exception as e:
        LOGGER.error(f"创建网格图像失败: {e}")
        return None


def get_tracking_results(algo_path, algo_name, sequence_name, frame_num):
    """获取跟踪结果"""
    try:
        from mot_toolkit.gui.isolate.ParallelMOTResultGallery.core.mot_loader import MOTResultLoader
        result_loader = MOTResultLoader()
        
        # 在多进程环境中，需要重新初始化结果加载器
        # 直接解析结果文件而不是使用加载器
        result_file = Path(algo_path) / f"{sequence_name}.txt"
        if not result_file.exists():
            return []
            
        # 解析MOT结果文件
        results = []
        with open(result_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                parts = line.split(',')
                if len(parts) < 6:
                    continue
                    
                try:
                    file_frame_num = int(parts[0])
                    if file_frame_num == frame_num + 1:  # MOT格式通常从1开始
                        track_id = int(parts[1])
                        x1 = float(parts[2])
                        y1 = float(parts[3])
                        width = float(parts[4])
                        height = float(parts[5])
                        confidence = float(parts[6]) if len(parts) > 6 else 1.0
                        
                        results.append({
                            "track_id": track_id,
                            "x1": x1,
                            "y1": y1,
                            "x2": x1 + width,
                            "y2": y1 + height,
                            "width": width,
                            "height": height,
                            "confidence": confidence,
                        })
                except (ValueError, IndexError):
                    continue
                    
        return results
        
    except Exception as e:
        LOGGER.error(f"获取跟踪结果失败: {e}")
        return []


def limit_resolution(img, render_config):
    """限制图像分辨率"""
    h, w = img.shape[:2]
    max_width = render_config.get("max_width", 800)
    max_height = render_config.get("max_height", 600)
    
    if w > max_width or h > max_height:
        scale = min(max_width / w, max_height / h)
        new_width = int(w * scale)
        new_height = int(h * scale)
        img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
    
    return img


class MultiProcessRenderWorker(QThread):
    """多进程渲染工作线程"""
    
    progress_updated = Signal(int, int, str)  # current, total, message
    finished = Signal(bool, str)  # success, message
    
    def __init__(self, config, sequence_name, output_dir, preview_frames, max_workers=None):
        super().__init__()
        self.config = config
        self.sequence_name = sequence_name
        self.output_dir = output_dir
        self.preview_frames = preview_frames
        self.max_workers = max_workers or os.cpu_count()
        self._is_running = True
        
    def run(self):
        """执行多进程网格渲染任务"""
        try:
            from mot_toolkit.gui.isolate.ParallelMOTResultGallery.core.video_loader import VideoFrameLoader
            
            sequence_paths = self.config.get("sequence_paths", {})
            
            if self.sequence_name not in sequence_paths:
                self.finished.emit(False, f"序列 {self.sequence_name} 不存在")
                return
                
            seq_path = sequence_paths[self.sequence_name]
            
            # 创建视频加载器获取总帧数
            loader = VideoFrameLoader()
            if not loader.set_video(seq_path):
                self.finished.emit(False, "无法加载序列视频")
                return
                
            total_frames = loader.get_total_frames()
            if total_frames == 0:
                self.finished.emit(False, "序列中没有帧")
                return
            
            # 创建输出目录
            output_dir = Path(self.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 准备任务参数
            total_groups = max(1, total_frames - self.preview_frames + 1)
            tasks = [
                (self.config, self.sequence_name, start_frame, self.preview_frames, self.output_dir)
                for start_frame in range(total_groups)
            ]
            
            # 使用多进程处理
            successful = 0
            failed = 0
            
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_task = {
                    executor.submit(process_frame_group, task): task[2] 
                    for task in tasks
                }
                
                for i, future in enumerate(as_completed(future_to_task)):
                    if not self._is_running:
                        break
                        
                    start_frame = future_to_task[future]
                    try:
                        result_start_frame, success, message = future.result()
                        if success:
                            successful += 1
                        else:
                            failed += 1
                            LOGGER.warning(message)
                            
                        # 更新进度
                        progress_info = f"处理帧组 {i + 1}/{total_groups} - {message}"
                        self.progress_updated.emit(i + 1, total_groups, progress_info)
                        
                    except Exception as e:
                        failed += 1
                        error_msg = f"处理帧组 {start_frame} 时发生异常: {str(e)}"
                        self.progress_updated.emit(i + 1, total_groups, error_msg)
                        LOGGER.error(error_msg)
            
            if not self._is_running:
                self.finished.emit(False, "渲染被用户取消")
            else:
                result_msg = f"渲染完成: 成功 {successful}, 失败 {failed}, 总计 {total_groups}"
                self.finished.emit(successful > 0, result_msg)
                
        except Exception as e:
            self.finished.emit(False, f"渲染失败: {str(e)}")
            
    def stop(self):
        """停止渲染"""
        self._is_running = False


class RenderWindow(QDialog):
    """高清渲染导出窗口 - 多进程网格布局版本"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("高清网格渲染导出 (多进程)")
        self.setModal(True)
        self.setMinimumWidth(700)
        self.resize(700, 500)
        
        self.config = {}
        self.sequence_name = ""
        self.output_dir = ""
        self.render_worker = None
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 序列信息组
        info_group = QGroupBox("渲染信息")
        info_layout = QVBoxLayout(info_group)
        
        self.sequence_label = QLabel("序列: 未选择")
        info_layout.addWidget(self.sequence_label)
        
        # 输出目录设置
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出目录:"))
        
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("请输入或选择输出目录")
        output_layout.addWidget(self.output_edit)
        
        self.select_output_btn = QPushButton("选择目录")
        self.select_output_btn.clicked.connect(self.select_output_directory)
        output_layout.addWidget(self.select_output_btn)
        
        info_layout.addLayout(output_layout)
        
        # 预览帧数设置
        frames_layout = QHBoxLayout()
        frames_layout.addWidget(QLabel("连续帧数:"))
        
        self.frames_spin = QSpinBox()
        self.frames_spin.setRange(1, 20)
        self.frames_spin.setValue(5)
        frames_layout.addWidget(self.frames_spin)
        
        # 进程数设置
        frames_layout.addWidget(QLabel("进程数:"))
        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, os.cpu_count() or 4)
        self.workers_spin.setValue(min(4, os.cpu_count() or 4))
        frames_layout.addWidget(self.workers_spin)
        
        info_layout.addLayout(frames_layout)
        
        layout.addWidget(info_group)
        
        # 进度组
        progress_group = QGroupBox("渲染进度")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("准备就绪")
        progress_layout.addWidget(self.status_label)
        
        # 日志输出
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        progress_layout.addWidget(QLabel("日志:"))
        progress_layout.addWidget(self.log_text)
        
        layout.addWidget(progress_group)
        
        # 按钮组
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("开始渲染")
        self.start_btn.clicked.connect(self.start_render)
        button_layout.addWidget(self.start_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
    def set_config(self, config: dict):
        """设置配置"""
        self.config = config
        
    def set_sequence(self, sequence_name: str):
        """设置序列"""
        self.sequence_name = sequence_name
        self.sequence_label.setText(f"序列: {sequence_name}")
        
    def select_output_directory(self):
        """选择输出目录"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择输出目录",
            self.output_edit.text() or "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        
        if directory:
            self.output_edit.setText(directory)
            
    def start_render(self):
        """开始渲染"""
        if not self.sequence_name:
            QMessageBox.warning(self, "警告", "请先选择序列")
            return
            
        output_dir = self.output_edit.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "警告", "请输入输出目录")
            return
            
        if not self.config.get("algorithms"):
            QMessageBox.warning(self, "警告", "没有算法数据")
            return
            
        # 创建输出目录
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法创建输出目录: {e}")
            return
            
        # 禁用按钮
        self.start_btn.setEnabled(False)
        self.select_output_btn.setEnabled(False)
        
        # 创建多进程渲染工作线程
        self.render_worker = MultiProcessRenderWorker(
            self.config, self.sequence_name, output_dir, 
            self.frames_spin.value(), self.workers_spin.value()
        )
        self.render_worker.progress_updated.connect(self.on_progress_updated)
        self.render_worker.finished.connect(self.on_render_finished)
        self.render_worker.start()
        
        self.log_text.append("开始多进程高清网格渲染...")
        self.log_text.append(f"输出目录: {output_dir}")
        self.log_text.append(f"连续帧数: {self.frames_spin.value()}")
        self.log_text.append(f"进程数: {self.workers_spin.value()}")
        
    def on_progress_updated(self, current, total, message):
        """进度更新"""
        progress = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
        self.log_text.append(message)
        
    def on_render_finished(self, success, message):
        """渲染完成"""
        self.start_btn.setEnabled(True)
        self.select_output_btn.setEnabled(True)
        
        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText("渲染完成")
            self.log_text.append("渲染完成！")
            QMessageBox.information(self, "成功", message)
        else:
            self.status_label.setText("渲染失败")
            self.log_text.append(f"错误: {message}")
            QMessageBox.warning(self, "错误", message)
            
    def closeEvent(self, event):
        """关闭事件"""
        if self.render_worker and self.render_worker.isRunning():
            self.render_worker.stop()
            self.render_worker.wait()
        super().closeEvent(event)