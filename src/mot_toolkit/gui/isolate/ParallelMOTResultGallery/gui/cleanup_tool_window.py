"""清理工具窗口 - 提供各种清理功能"""

import os
import shutil
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
    QFileDialog,
    QLineEdit,
)
from PySide6.QtCore import Qt, QThread, Signal
from mot_toolkit.utils.logs import get_logger

LOGGER = get_logger()


class CleanupWorker(QThread):
    """清理工作线程"""
    
    progress_updated = Signal(int, int, str)  # current, total, message
    finished = Signal(bool, str)  # success, message
    
    def __init__(self, cleanup_type, target_path=None, config=None):
        super().__init__()
        self.cleanup_type = cleanup_type
        self.target_path = target_path
        self.config = config
        self._is_running = True
        
    def run(self):
        """执行清理任务"""
        try:
            if self.cleanup_type == "directory_jpg":
                result = self.cleanup_directory_jpg()
            elif self.cleanup_type == "gt":
                result = self.cleanup_gt()
            elif self.cleanup_type == "all_algorithms":
                result = self.cleanup_all_algorithms()
            else:
                self.finished.emit(False, f"未知的清理类型: {self.cleanup_type}")
                return
                
            self.finished.emit(result[0], result[1])
                
        except Exception as e:
            self.finished.emit(False, f"清理失败: {str(e)}")
            
    def cleanup_directory_jpg(self):
        """清理目录下的所有jpg图片"""
        if not self.target_path:
            return False, "目标目录未设置"
            
        target_dir = Path(self.target_path)
        if not target_dir.exists():
            return False, f"目录不存在: {target_dir}"
            
        # 查找所有jpg文件
        jpg_files = list(target_dir.rglob("*.jpg"))
        total_files = len(jpg_files)
        
        if total_files == 0:
            return True, "没有找到jpg文件"
            
        # 删除文件
        deleted_count = 0
        for i, jpg_file in enumerate(jpg_files):
            if not self._is_running:
                return False, "清理被用户取消"
                
            try:
                jpg_file.unlink()
                deleted_count += 1
                self.progress_updated.emit(i + 1, total_files, f"删除: {jpg_file.name}")
            except Exception as e:
                LOGGER.error(f"删除文件失败 {jpg_file}: {e}")
                
        return True, f"删除完成: {deleted_count}/{total_files} 个jpg文件"
        
    def cleanup_gt(self):
        """清理GT相关文件"""
        if not self.config or not self.config.get("dataset_path"):
            return False, "数据集路径未设置"
            
        dataset_path = Path(self.config["dataset_path"])
        if not dataset_path.exists():
            return False, f"数据集路径不存在: {dataset_path}"
            
        # 查找所有gt目录和文件
        gt_dirs = list(dataset_path.rglob("gt"))
        total_dirs = len(gt_dirs)
        
        if total_dirs == 0:
            return True, "没有找到gt目录"
            
        deleted_files = 0
        processed_dirs = 0
        
        for i, gt_dir in enumerate(gt_dirs):
            if not self._is_running:
                return False, "清理被用户取消"
                
            processed_dirs += 1
            self.progress_updated.emit(processed_dirs, total_dirs, f"处理: {gt_dir}")
            
            # 删除gt目录下的所有文件（保留目录结构）
            if gt_dir.exists() and gt_dir.is_dir():
                for file in gt_dir.iterdir():
                    if file.is_file():
                        try:
                            file.unlink()
                            deleted_files += 1
                        except Exception as e:
                            LOGGER.error(f"删除文件失败 {file}: {e}")
                            
        return True, f"GT清理完成: 处理 {processed_dirs} 个目录，删除 {deleted_files} 个文件"
        
    def cleanup_all_algorithms(self):
        """清理所有算法预渲染结果"""
        if not self.config:
            return False, "配置未设置"
            
        cache_dir = self._get_cache_directory()
        if not cache_dir.exists():
            return True, "缓存目录不存在，无需清理"
            
        # 查找所有算法目录
        algorithm_dirs = []
        if cache_dir.exists():
            for algo_dir in cache_dir.iterdir():
                if algo_dir.is_dir():
                    algorithm_dirs.append(algo_dir)
                    
        total_dirs = len(algorithm_dirs)
        
        if total_dirs == 0:
            return True, "没有找到算法目录"
            
        deleted_files = 0
        processed_dirs = 0
        
        for i, algo_dir in enumerate(algorithm_dirs):
            if not self._is_running:
                return False, "清理被用户取消"
                
            processed_dirs += 1
            self.progress_updated.emit(processed_dirs, total_dirs, f"清理: {algo_dir.name}")
            
            # 删除算法目录下的所有jpg文件
            jpg_files = list(algo_dir.rglob("*.jpg"))
            for jpg_file in jpg_files:
                try:
                    jpg_file.unlink()
                    deleted_files += 1
                except Exception as e:
                    LOGGER.error(f"删除文件失败 {jpg_file}: {e}")
                    
        return True, f"算法清理完成: 处理 {processed_dirs} 个算法，删除 {deleted_files} 个jpg文件"
        
    def _get_cache_directory(self):
        """获取缓存目录"""
        cache_dir = self.config.get("cache_dir")
        if not cache_dir:
            import tempfile
            cache_dir = Path(tempfile.gettempdir()) / "ParallelMOTResultGallery"
            
        dataset_path = self.config.get("dataset_path")
        if dataset_path:
            dataset_path = Path(dataset_path)
            if len(dataset_path.parts) >= 2:
                dataset_name = "_".join(dataset_path.parts[-2:])
            else:
                dataset_name = dataset_path.name
            cache_dir = cache_dir / dataset_name
            
        return Path(cache_dir)
        
    def stop(self):
        """停止清理"""
        self._is_running = False


class CleanupToolWindow(QDialog):
    """清理工具窗口"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("清理工具")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.resize(500, 400)
        
        self.config = {}
        self.worker = None
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 目录清理组
        dir_group = QGroupBox("目录jpg清理")
        dir_layout = QVBoxLayout(dir_group)
        
        dir_input_layout = QHBoxLayout()
        self.dir_path_edit = QLineEdit()
        self.dir_path_edit.setPlaceholderText("选择要清理的目录...")
        dir_input_layout.addWidget(self.dir_path_edit)
        
        self.dir_browse_btn = QPushButton("浏览")
        self.dir_browse_btn.clicked.connect(self.browse_directory)
        dir_input_layout.addWidget(self.dir_browse_btn)
        
        dir_layout.addLayout(dir_input_layout)
        
        self.clean_dir_btn = QPushButton("清理该目录下的所有jpg")
        self.clean_dir_btn.clicked.connect(lambda: self.start_cleanup("directory_jpg", self.dir_path_edit.text()))
        dir_layout.addWidget(self.clean_dir_btn)
        
        layout.addWidget(dir_group)
        
        # GT清理组
        gt_group = QGroupBox("GT清理")
        gt_layout = QVBoxLayout(gt_group)
        
        gt_info = QLabel("清理数据集中的所有GT文件（保留目录结构）")
        gt_layout.addWidget(gt_info)
        
        self.clean_gt_btn = QPushButton("清理GT文件")
        self.clean_gt_btn.clicked.connect(lambda: self.start_cleanup("gt"))
        gt_layout.addWidget(self.clean_gt_btn)
        
        layout.addWidget(gt_group)
        
        # 算法清理组
        algo_group = QGroupBox("算法预渲染清理")
        algo_layout = QVBoxLayout(algo_group)
        
        algo_info = QLabel("清理所有算法的预渲染结果（jpg文件）")
        algo_layout.addWidget(algo_info)
        
        self.clean_algo_btn = QPushButton("清理所有算法结果")
        self.clean_algo_btn.clicked.connect(lambda: self.start_cleanup("all_algorithms"))
        algo_layout.addWidget(self.clean_algo_btn)
        
        layout.addWidget(algo_group)
        
        # 进度组
        progress_group = QGroupBox("清理进度")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("准备就绪")
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_group)
        
        # 按钮组
        button_layout = QHBoxLayout()
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        
    def set_config(self, config):
        """设置配置"""
        self.config = config
        
    def browse_directory(self):
        """浏览目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择要清理的目录")
        if directory:
            self.dir_path_edit.setText(directory)
            
    def start_cleanup(self, cleanup_type, target_path=None):
        """开始清理"""
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "警告", "清理操作正在进行中")
            return
            
        # 验证输入
        if cleanup_type == "directory_jpg" and not target_path:
            QMessageBox.warning(self, "警告", "请先选择要清理的目录")
            return
            
        self.worker = CleanupWorker(cleanup_type, target_path, self.config)
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.finished.connect(self.on_finished)
        
        # 禁用所有按钮
        self.set_buttons_enabled(False)
        
        self.worker.start()
        
    def on_progress_updated(self, current, total, message):
        """进度更新"""
        progress = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"{message} ({current}/{total})")
        
    def on_finished(self, success, message):
        """清理完成"""
        self.set_buttons_enabled(True)
        self.progress_bar.setValue(0)
        
        if success:
            QMessageBox.information(self, "成功", message)
            self.status_label.setText("清理完成")
        else:
            QMessageBox.warning(self, "失败", message)
            self.status_label.setText("清理失败")
            
    def set_buttons_enabled(self, enabled):
        """设置按钮启用状态"""
        self.clean_dir_btn.setEnabled(enabled)
        self.clean_gt_btn.setEnabled(enabled)
        self.clean_algo_btn.setEnabled(enabled)
        self.dir_browse_btn.setEnabled(enabled)
        
    def closeEvent(self, event):
        """关闭事件"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        super().closeEvent(event)