"""预渲染窗口 - 支持多进程渲染和全局进度条"""

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
)
from PySide6.QtCore import Qt, QThread, Signal
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed

from mot_toolkit.utils.logs import get_logger

LOGGER = get_logger()


class PreRenderWorker(QThread):
    """预渲染工作线程 - 使用多进程"""
    
    progress_updated = Signal(int, int, str)  # current, total, message
    finished = Signal(bool, str)  # success, message
    
    def __init__(self, config, current_sequence=None):
        super().__init__()
        self.config = config
        self.current_sequence = current_sequence
        self._is_running = True
        self._executor = None
        self._futures = []
        
    def run(self):
        """执行预渲染任务"""
        try:
            # 获取缓存目录
            cache_dir = self._get_cache_directory()
            if not cache_dir:
                self.finished.emit(False, "缓存目录未设置")
                return
                
            # 创建缓存目录
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            # 获取所有任务
            tasks = self._prepare_tasks()
            total_tasks = len(tasks)
            
            if total_tasks == 0:
                self.finished.emit(False, "没有可渲染的任务")
                return
                
            # 使用多进程池执行任务（CPU核心数/2）
            max_workers = max(1, multiprocessing.cpu_count() // 2)
            completed = 0
            
            # 创建执行器并保存引用
            self._executor = ProcessPoolExecutor(max_workers=max_workers)
            
            try:
                # 提交所有任务，单序列模式跳过已存在的帧
                self._futures = [
                    self._executor.submit(render_single_task, task, str(cache_dir), True)
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
                        result = future.result()
                        completed += 1
                        self.progress_updated.emit(
                            completed,
                            total_tasks,
                            f"完成: {task['algorithm']} - {task['sequence']}"
                        )
                    except Exception as e:
                        LOGGER.error(f"任务执行失败: {e}")
            finally:
                # 确保执行器被正确关闭
                if self._executor:
                    self._executor.shutdown(wait=False)
                        
            if self._is_running:
                self.finished.emit(True, f"预渲染完成，共处理 {completed}/{total_tasks} 个任务")
            else:
                self.finished.emit(False, "预渲染被用户取消")
                
        except Exception as e:
            self.finished.emit(False, f"预渲染失败: {str(e)}")
            
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
        """准备渲染任务 - 只渲染当前序列"""
        tasks = []
        algorithms = self.config.get("algorithms", {})
        sequence_paths = self.config.get("sequence_paths", {})

        # 如果指定了当前序列，只渲染该序列
        if self.current_sequence and self.current_sequence in sequence_paths:
            for algo_name, algo_path in algorithms.items():
                tasks.append({
                    "algorithm": algo_name,
                    "sequence": self.current_sequence,
                    "sequence_path": sequence_paths[self.current_sequence],
                    "algorithm_path": algo_path
                })
        else:
            # 如果没有指定序列，渲染所有序列（保持向后兼容）
            for algo_name, algo_path in algorithms.items():
                for seq_name, seq_path in sequence_paths.items():
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


class PreRenderWindow(QDialog):
    """预渲染窗口"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("预渲染 - 当前序列")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.resize(500, 250)
        
        self.config = {}
        self.current_sequence = None
        self.worker = None
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 信息组
        info_group = QGroupBox("预渲染信息")
        info_layout = QVBoxLayout(info_group)
        
        self.sequence_label = QLabel("当前序列: 未设置")
        info_layout.addWidget(self.sequence_label)
        
        self.cache_dir_label = QLabel("缓存目录: 计算中...")
        info_layout.addWidget(self.cache_dir_label)
        
        self.task_count_label = QLabel("任务数量: 计算中...")
        info_layout.addWidget(self.task_count_label)
        
        layout.addWidget(info_group)
        
        # 进度组
        progress_group = QGroupBox("渲染进度")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("准备开始...")
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_group)
        
        # 按钮组
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("开始预渲染")
        self.start_btn.clicked.connect(self.start_pre_render)
        button_layout.addWidget(self.start_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(self.cancel_btn)
        
        self.open_dir_btn = QPushButton("打开缓存目录")
        self.open_dir_btn.clicked.connect(self.open_cache_directory)
        self.open_dir_btn.setEnabled(False)
        button_layout.addWidget(self.open_dir_btn)
        
        layout.addLayout(button_layout)
        
    def set_config(self, config, current_sequence=None):
        """设置配置和当前序列"""
        self.config = config
        self.current_sequence = current_sequence
        self.update_info()
        
    def update_info(self):
        """更新信息显示"""
        # 显示当前序列
        if self.current_sequence:
            self.sequence_label.setText(f"当前序列: {self.current_sequence}")
            self.setWindowTitle(f"预渲染 - {self.current_sequence}")
        else:
            self.sequence_label.setText("当前序列: 所有序列")
            self.setWindowTitle("预渲染 - 所有序列")
        
        # 计算缓存目录
        cache_dir = self._get_cache_directory()
        self.cache_dir_label.setText(f"缓存目录: {cache_dir}")
        
        # 计算任务数量
        algorithms = self.config.get("algorithms", {})
        if self.current_sequence:
            # 只渲染当前序列，任务数量等于算法数量
            task_count = len(algorithms)
        else:
            # 渲染所有序列
            sequence_paths = self.config.get("sequence_paths", {})
            task_count = len(algorithms) * len(sequence_paths)
        self.task_count_label.setText(f"任务数量: {task_count}")
        
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
        
    def _check_cache_complete(self):
        """检查缓存是否完整（100%渲染完成）"""
        cache_dir = self._get_cache_directory()
        if not cache_dir.exists():
            return False
            
        algorithms = self.config.get("algorithms", {})
        sequence_paths = self.config.get("sequence_paths", {})
        
        for algo_name in algorithms.keys():
            for seq_name in sequence_paths.keys():
                algo_cache_dir = cache_dir / algo_name / seq_name
                if not algo_cache_dir.exists():
                    return False
                    
                # 检查该序列是否所有帧都已渲染
                from mot_toolkit.gui.isolate.ParallelMOTResultGallery.core.video_loader import VideoFrameLoader
                video_loader = VideoFrameLoader()
                if video_loader.set_video(sequence_paths[seq_name]):
                    total_frames = video_loader.get_total_frames()
                    rendered_frames = len(list(algo_cache_dir.glob("*.jpg")))
                    if rendered_frames < total_frames:
                        return False
                        
        return True
        
    def start_pre_render(self):
        """开始预渲染"""
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "警告", "预渲染正在进行中")
            return
            
        self.worker = PreRenderWorker(self.config, self.current_sequence)
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.finished.connect(self.on_finished)
        
        self.start_btn.setEnabled(False)
        self.cancel_btn.setText("停止")
        self.cancel_btn.clicked.disconnect()
        self.cancel_btn.clicked.connect(self.stop_pre_render)
        
        self.worker.start()
        
    def stop_pre_render(self):
        """停止预渲染"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
            
    def on_progress_updated(self, current, total, message):
        """进度更新"""
        progress = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"{message} ({current}/{total})")
        
    def on_finished(self, success, message):
        """预渲染完成"""
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


def render_single_task(task, cache_dir_str, skip_existing=True):
    """独立的渲染任务函数 - 用于多进程，单序列模式只跳过已存在的帧"""
    import os
    import cv2
    import time
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
        
        # 初始化绘制器
        plotter = ResultPlotter()
        
        # 初始化视频加载器
        video_loader = VideoFrameLoader()
        if not video_loader.set_video(task["sequence_path"]):
            logger.error(f"无法加载视频: {task['sequence_path']}")
            return False
            
        # 初始化结果加载器
        from mot_toolkit.gui.isolate.ParallelMOTResultGallery.core.mot_loader import MOTResultLoader
        result_loader = MOTResultLoader()
        if not result_loader.add_algorithm_directory(task["algorithm_path"], task["algorithm"]):
            logger.error(f"无法加载算法结果: {task['algorithm_path']}")
            return False
            
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
            
            # 如果文件已存在且有效，跳过渲染（单序列模式只跳过帧）
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
        return True
        
    except Exception as e:
        logger.error(f"渲染任务失败 {task['algorithm']} - {task['sequence']}: {e}")
        return False