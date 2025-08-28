"""多序列预渲染窗口 - 一次性渲染所有序列"""

import os
import tempfile
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QMessageBox,
    QGroupBox,
    QCheckBox,
    QComboBox,
)
from PySide6.QtCore import Qt, QThread, Signal
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed

from mot_toolkit.utils.logs import get_logger

LOGGER = get_logger()


def check_sequence_rendered(algo_cache_dir, sequence_path, algorithm_name=None):
    """检查序列是否已经完成渲染 - 通过render.json标记，支持动态算法检测"""
    if not algo_cache_dir.exists():
        return False
        
    # 检查render.json完成标记
    render_marker = algo_cache_dir / "render.json"
    if render_marker.exists():
        try:
            import json
            import time
            with open(render_marker, 'r', encoding='utf-8') as f:
                marker_data = json.load(f)
                
                # 检查是否完成
                completed = marker_data.get("completed", False)
                
                # 如果标记文件超过30天，认为需要重新检查（支持算法更新）
                timestamp = marker_data.get("timestamp", 0)
                if completed and time.time() - timestamp > 2592000:  # 30天
                    LOGGER.info(f"渲染标记文件过期，重新检查: {algo_cache_dir}")
                    completed = False
                
                return completed
        except:
            return False
            
    # 如果没有标记文件，使用传统方法检查
    from mot_toolkit.gui.isolate.ParallelMOTResultGallery.core.video_loader import VideoFrameLoader
    
    video_loader = VideoFrameLoader()
    if not video_loader.set_video(sequence_path):
        return False
        
    total_frames = video_loader.get_total_frames()
    
    # 检查所有帧是否都存在且有效
    jpg_files = list(algo_cache_dir.glob("*.jpg"))
    existing_frames = 0
    
    for jpg_file in jpg_files:
        try:
            # 检查文件是否有效（可读取）
            import cv2
            img = cv2.imread(str(jpg_file))
            if img is not None:
                existing_frames += 1
        except:
            continue
    
    # 允许95%的完成率，避免因为少数损坏文件导致重新渲染
    completion_ratio = existing_frames / total_frames if total_frames > 0 else 0
    return completion_ratio >= 0.95


def create_render_marker(algo_cache_dir, total_frames, rendered_frames, algorithm_name=None):
    """创建渲染完成标记文件，包含算法信息和时间戳"""
    try:
        import json
        import time
        render_marker = algo_cache_dir / "render.json"
        marker_data = {
            "completed": rendered_frames >= total_frames,
            "total_frames": total_frames,
            "rendered_frames": rendered_frames,
            "timestamp": time.time(),
            "algorithm": algorithm_name or "unknown",
            "version": "1.1"  # 标记文件版本，用于后续兼容性检查
        }
        with open(render_marker, 'w', encoding='utf-8') as f:
            json.dump(marker_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger = get_logger()
        logger.error(f"创建渲染标记失败: {e}")


def render_single_sequence_task(task, cache_dir_str, skip_existing=True):
    """独立的序列渲染任务函数 - 用于多进程，以序列为单位"""
    import os
    import cv2
    from pathlib import Path
    from mot_toolkit.gui.isolate.ParallelMOTResultGallery.core.video_loader import VideoFrameLoader
    from mot_toolkit.gui.isolate.ParallelMOTResultGallery.core.result_plotter import ResultPlotter
    from mot_toolkit.datatype.dataset.danceteck_gt import DanceTrackGTReader, find_gt_file
    from mot_toolkit.utils.logs import get_logger
    
    logger = get_logger()
    cache_dir = Path(cache_dir_str)
    
    try:
        # 创建算法和序列的缓存目录
        algo_cache_dir = cache_dir / task["algorithm"] / task["sequence"]
        algo_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 如果跳过已存在的文件且序列已渲染完成，直接返回
        if skip_existing and check_sequence_rendered(algo_cache_dir, task["sequence_path"], task["algorithm"]):
            logger.info(f"跳过已渲染的序列: {task['algorithm']} - {task['sequence']}")
            return True, task["sequence"], "已存在，跳过"
            
        # 初始化绘制器
        plotter = ResultPlotter()
        
        # 初始化视频加载器
        video_loader = VideoFrameLoader()
        if not video_loader.set_video(task["sequence_path"]):
            logger.error(f"无法加载视频: {task['sequence_path']}")
            return False, task["sequence"], "视频加载失败"
            
        # 初始化结果加载器
        from mot_toolkit.gui.isolate.ParallelMOTResultGallery.core.mot_loader import MOTResultLoader
        result_loader = MOTResultLoader()
        if not result_loader.add_algorithm_directory(task["algorithm_path"], task["algorithm"]):
            logger.error(f"无法加载算法结果: {task['algorithm_path']}")
            return False, task["sequence"], "算法结果加载失败"
            
        # 初始化GT读取器（如果存在GT文件）
        gt_reader = DanceTrackGTReader()
        gt_file = find_gt_file(task["sequence_path"])
        show_gt = gt_file is not None
        if show_gt:
            gt_reader.load_gt_file(gt_file)
            
        total_frames = video_loader.get_total_frames()
        rendered_count = 0
        
        # 渲染每一帧
        for frame_num in range(total_frames):
            output_path = algo_cache_dir / f"{frame_num:08d}.jpg"
            
            # 如果文件已存在且有效，跳过渲染
            if skip_existing and output_path.exists():
                try:
                    # 检查文件是否有效
                    img = cv2.imread(str(output_path))
                    if img is not None:
                        rendered_count += 1
                        continue
                except:
                    pass
            
            # 获取原始图像
            image_path = video_loader.get_frame_path(frame_num)
            if not image_path or not os.path.exists(image_path):
                continue
                
            img = cv2.imread(image_path)
            if img is None:
                continue
                
            # 获取跟踪结果
            results = result_loader.get_results_for_frame(
                task["sequence"], task["algorithm"], frame_num
            )
            
            # 绘制跟踪结果
            if results:
                img = plotter.draw_results_on_frame(img, results, task["algorithm"])
                
            # 绘制GT结果（如果存在）
            if show_gt:
                gt_results = gt_reader.convert_to_mot_format(frame_num)
                if gt_results:
                    img = plotter.draw_results_on_frame(
                        img, gt_results, "GT",
                        color=(0, 255, 0),  # 绿色
                        thickness=3  # 更粗的线
                    )
            
            # 保存渲染后的图像
            cv2.imwrite(str(output_path), img)
            rendered_count += 1
            
        logger.info(f"完成渲染: {task['algorithm']} - {task['sequence']}, 共 {rendered_count}/{total_frames} 帧")
        
        # 创建渲染完成标记，包含算法信息
        create_render_marker(algo_cache_dir, total_frames, rendered_count, task["algorithm"])
        
        return True, task["sequence"], f"完成 {rendered_count}/{total_frames} 帧"
        
    except Exception as e:
        logger.error(f"渲染任务失败 {task['algorithm']} - {task['sequence']}: {e}")
        return False, task["sequence"], f"失败: {str(e)}"


class MultiSequencePreRenderWorker(QThread):
    """多序列预渲染工作线程 - 使用多进程，以序列为单位"""
    
    progress_updated = Signal(int, int, str, str)  # current, total, sequence, status
    finished = Signal(bool, str)  # success, message
    
    def __init__(self, config, skip_existing=True, selected_sequences=None):
        super().__init__()
        self.config = config
        self.skip_existing = skip_existing
        self.selected_sequences = selected_sequences or []
        self._is_running = True
        self._executor = None
        self._futures = []
        
    def run(self):
        """执行多序列预渲染任务"""
        try:
            # 获取缓存目录
            cache_dir = self._get_cache_directory()
            if not cache_dir:
                self.finished.emit(False, "缓存目录未设置")
                return
                
            # 创建缓存目录
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            # 准备所有任务（以序列为单位）
            tasks = self._prepare_tasks()
            total_tasks = len(tasks)
            
            if total_tasks == 0:
                self.finished.emit(False, "没有可渲染的任务")
                return
                
            # 使用多进程池执行任务，使用配置中的进程数
            max_workers = self.config.get("process_count", max(1, multiprocessing.cpu_count() // 2))
            completed = 0
            
            # 创建执行器并保存引用
            self._executor = ProcessPoolExecutor(max_workers=max_workers)
            
            try:
                # 提交所有任务
                self._futures = [
                    self._executor.submit(
                        render_single_sequence_task,
                        task,
                        str(cache_dir),
                        self.skip_existing
                    )
                    for task in tasks
                ]
                
                future_to_task = dict(zip(self._futures, tasks))
                
                # 处理完成的任务
                for future in as_completed(future_to_task):
                    if not self._is_running:
                        # 用户取消，终止所有任务
                        for f in self._futures:
                            if not f.done():
                                f.cancel()
                        break
                        
                    task = future_to_task[future]
                    try:
                        success, sequence, status = future.result()
                        completed += 1
                        self.progress_updated.emit(
                            completed,
                            total_tasks,
                            sequence,
                            status
                        )
                    except Exception as e:
                        completed += 1
                        self.progress_updated.emit(
                            completed,
                            total_tasks,
                            task["sequence"],
                            f"异常: {str(e)}"
                        )
            finally:
                # 确保执行器被正确关闭
                if self._executor:
                    self._executor.shutdown(wait=False)
                        
            if self._is_running:
                self.finished.emit(True, f"多序列预渲染完成，共处理 {completed}/{total_tasks} 个序列")
            else:
                self.finished.emit(False, "多序列预渲染被用户取消")
                
        except Exception as e:
            self.finished.emit(False, f"多序列预渲染失败: {str(e)}")
            
    def _get_cache_directory(self):
        """获取缓存目录"""
        cache_dir = self.config.get("cache_dir")
        if not cache_dir:
            # 使用默认缓存目录
            cache_dir = Path(tempfile.gettempdir()) / "ParallelMOTResultGallery"
            
        # 根据数据集路径创建子目录
        dataset_path = self.config.get("dataset_path")
        if dataset_path:
            dataset_path = Path(dataset_path)
            # 获取最后两级目录名
            if len(dataset_path.parts) >= 2:
                dataset_name = "_".join(dataset_path.parts[-2:])
            else:
                dataset_name = dataset_path.name
            cache_dir = cache_dir / dataset_name
            
        return Path(cache_dir)
        
    def _prepare_tasks(self):
        """准备渲染任务"""
        tasks = []
        algorithms = self.config.get("algorithms", {})
        sequence_paths = self.config.get("sequence_paths", {})
        
        # 如果没有选择特定序列，则渲染所有序列
        target_sequences = self.selected_sequences if self.selected_sequences else sequence_paths.keys()
        
        for algo_name, algo_path in algorithms.items():
            for seq_name, seq_path in sequence_paths.items():
                if seq_name in target_sequences:
                    tasks.append({
                        "algorithm": algo_name,
                        "sequence": seq_name,
                        "sequence_path": seq_path,
                        "algorithm_path": algo_path
                    })
                
        return tasks
        
    def stop(self):
        """停止预渲染 - 终止所有子进程"""
        self._is_running = False
        
        # 取消所有未完成的任务
        if hasattr(self, '_futures'):
            for future in self._futures:
                if not future.done():
                    future.cancel()
        
        # 强制关闭执行器
        if hasattr(self, '_executor') and self._executor:
            try:
                self._executor.shutdown(wait=False, cancel_futures=True)
            except:
                # 如果shutdown失败，尝试强制终止
                import os
                import signal
                # 获取所有子进程并终止
                for process in self._executor._processes.values():
                    try:
                        os.kill(process.pid, signal.SIGTERM)
                    except:
                        pass


class MultiSequencePreRenderWindow(QDialog):
    """多序列预渲染窗口"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("多序列预渲染 - 批量处理")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.resize(600, 400)
        
        self.config = {}
        self.worker = None
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 信息组
        info_group = QGroupBox("多序列预渲染信息")
        info_layout = QVBoxLayout(info_group)
        
        self.cache_dir_label = QLabel("缓存目录: 计算中...")
        info_layout.addWidget(self.cache_dir_label)
        
        self.task_count_label = QLabel("序列任务数量: 计算中...")
        info_layout.addWidget(self.task_count_label)
        
        # 序列选择组
        seq_group = QGroupBox("序列选择")
        seq_layout = QVBoxLayout(seq_group)
        
        self.sequence_combo = QComboBox()
        self.sequence_combo.addItem("所有序列")
        self.sequence_combo.currentTextChanged.connect(self.on_sequence_selection_changed)
        seq_layout.addWidget(QLabel("选择要渲染的序列:"))
        seq_layout.addWidget(self.sequence_combo)
        
        # 选项组
        options_layout = QHBoxLayout()
        self.skip_existing_checkbox = QCheckBox("跳过已存在的序列")
        self.skip_existing_checkbox.setChecked(True)
        options_layout.addWidget(self.skip_existing_checkbox)
        
        self.force_rerender_checkbox = QCheckBox("强制重新渲染")
        self.force_rerender_checkbox.setChecked(False)
        self.force_rerender_checkbox.stateChanged.connect(self.on_force_rerender_changed)
        options_layout.addWidget(self.force_rerender_checkbox)

        info_layout.addLayout(options_layout)
        layout.addWidget(info_group)
        layout.addWidget(seq_group)
        
        # 进度组
        progress_group = QGroupBox("渲染进度 (以序列为单位)")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("准备开始...")
        progress_layout.addWidget(self.status_label)
        
        self.current_sequence_label = QLabel("当前序列: -")
        progress_layout.addWidget(self.current_sequence_label)
        
        layout.addWidget(progress_group)
        
        # 按钮组
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("开始多序列预渲染")
        self.start_btn.clicked.connect(self.start_multi_sequence_pre_render)
        button_layout.addWidget(self.start_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(self.cancel_btn)
        
        self.open_dir_btn = QPushButton("打开缓存目录")
        self.open_dir_btn.clicked.connect(self.open_cache_directory)
        self.open_dir_btn.setEnabled(False)
        button_layout.addWidget(self.open_dir_btn)
        
        layout.addLayout(button_layout)
        
    def set_config(self, config):
        """设置配置"""
        self.config = config
        self.update_info()
        self.update_sequence_list()
        
    def update_info(self):
        """更新信息显示"""
        # 计算缓存目录
        cache_dir = self._get_cache_directory()
        self.cache_dir_label.setText(f"缓存目录: {cache_dir}")
        
        # 计算任务数量
        algorithms = self.config.get("algorithms", {})
        sequence_paths = self.config.get("sequence_paths", {})
        task_count = len(algorithms) * len(sequence_paths)
        self.task_count_label.setText(f"序列任务数量: {task_count}")
        
    def update_sequence_list(self):
        """更新序列列表"""
        self.sequence_combo.clear()
        self.sequence_combo.addItem("所有序列")
        
        sequence_paths = self.config.get("sequence_paths", {})
        for seq_name in sequence_paths.keys():
            self.sequence_combo.addItem(seq_name)
            
    def on_sequence_selection_changed(self, selected_sequence):
        """序列选择改变时的处理"""
        # 这里可以添加特定序列选择的逻辑
        pass
        
    def on_force_rerender_changed(self, state):
        """强制重新渲染选项改变时的处理"""
        if state == Qt.Checked:
            self.skip_existing_checkbox.setChecked(False)
            self.skip_existing_checkbox.setEnabled(False)
        else:
            self.skip_existing_checkbox.setEnabled(True)
        
    def _get_cache_directory(self):
        """获取缓存目录"""
        cache_dir = self.config.get("cache_dir")
        if not cache_dir:
            cache_dir = Path(tempfile.gettempdir()) / "ParallelMOTResultGallery"
            
        dataset_path = self.config.get("dataset_path")
        if dataset_path:
            dataset_path = Path(dataset_path)
            if len(dataset_path.parts) >= 2:
                dataset_name = "_".join(dataset_path.parts[-2:])
            else:
                dataset_name = dataset_path.name
            cache_dir = cache_dir / dataset_name
            
        return cache_dir
        
    def start_multi_sequence_pre_render(self):
        """开始多序列预渲染"""
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "警告", "多序列预渲染正在进行中")
            return
            
        skip_existing = self.skip_existing_checkbox.isChecked() and not self.force_rerender_checkbox.isChecked()
        
        # 获取选择的序列
        selected_sequence = self.sequence_combo.currentText()
        selected_sequences = None
        if selected_sequence != "所有序列":
            selected_sequences = [selected_sequence]
            
        self.worker = MultiSequencePreRenderWorker(self.config, skip_existing, selected_sequences)
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.finished.connect(self.on_finished)
        
        self.start_btn.setEnabled(False)
        self.cancel_btn.setText("停止")
        self.cancel_btn.clicked.disconnect()
        self.cancel_btn.clicked.connect(self.stop_multi_sequence_pre_render)
        
        self.worker.start()
        
    def stop_multi_sequence_pre_render(self):
        """停止多序列预渲染"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
            
    def on_progress_updated(self, current, total, sequence, status):
        """进度更新"""
        progress = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"进度: {current}/{total} 序列")
        self.current_sequence_label.setText(f"当前序列: {sequence} - {status}")
        
    def on_finished(self, success, message):
        """多序列预渲染完成"""
        self.start_btn.setEnabled(True)
        self.cancel_btn.setText("关闭")
        self.cancel_btn.clicked.disconnect()
        self.cancel_btn.clicked.connect(self.close)
        self.open_dir_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "成功", message)
        else:
            QMessageBox.warning(self, "失败", message)
            
    def open_cache_directory(self):
        """打开缓存目录"""
        cache_dir = self._get_cache_directory()
        try:
            os.startfile(str(cache_dir))  # Windows
        except:
            try:
                import subprocess
                subprocess.run(["open", str(cache_dir)])  # macOS
            except:
                try:
                    subprocess.run(["xdg-open", str(cache_dir)])  # Linux
                except:
                    QMessageBox.warning(self, "错误", "无法打开缓存目录")
                    
    def closeEvent(self, event):
        """关闭事件"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        super().closeEvent(event)