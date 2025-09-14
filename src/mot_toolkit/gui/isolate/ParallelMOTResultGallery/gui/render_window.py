"""高清渲染导出窗口"""

import os
from pathlib import Path
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
)
from PySide6.QtCore import Qt, QThread, Signal
from mot_toolkit.utils.logs import get_logger

LOGGER = get_logger()


class RenderWorker(QThread):
    """渲染工作线程"""
    
    progress_updated = Signal(int, int, str)  # current, total, message
    finished = Signal(bool, str)  # success, message
    
    def __init__(self, config, sequence_name, output_dir):
        super().__init__()
        self.config = config
        self.sequence_name = sequence_name
        self.output_dir = output_dir
        self._is_running = True
        
    def run(self):
        """执行渲染任务"""
        try:
            from mot_toolkit.gui.isolate.ParallelMOTResultGallery.core.result_plotter import ResultPlotter
            
            plotter = ResultPlotter()
            algorithms = self.config.get("algorithms", {})
            sequence_paths = self.config.get("sequence_paths", {})
            
            if not algorithms or not sequence_paths:
                self.finished.emit(False, "没有算法或序列数据")
                return
                
            if self.sequence_name not in sequence_paths:
                self.finished.emit(False, f"序列 {self.sequence_name} 不存在")
                return
                
            seq_path = sequence_paths[self.sequence_name]
            
            total_tasks = len(algorithms)
            current_task = 0
            
            for algo_name, algo_path in algorithms.items():
                if not self._is_running:
                    self.finished.emit(False, "渲染被用户取消")
                    return
                    
                current_task += 1
                task_info = f"渲染: {algo_name} - {self.sequence_name}"
                self.progress_updated.emit(current_task, total_tasks, task_info)
                
                # 创建输出目录
                output_algo_dir = Path(self.output_dir) / algo_name
                output_algo_dir.mkdir(parents=True, exist_ok=True)
                
                # 使用结果绘制器渲染序列
                success = plotter.plot_sequence(
                    algo_path, seq_path, str(output_algo_dir), 
                    self.sequence_name, self.config.get("render_config", {})
                )
                
                if not success:
                    LOGGER.warning(f"渲染失败: {algo_name} - {self.sequence_name}")
                    
            self.finished.emit(True, f"渲染完成，共处理 {total_tasks} 个算法")
            
        except Exception as e:
            self.finished.emit(False, f"渲染失败: {str(e)}")
            
    def stop(self):
        """停止渲染"""
        self._is_running = False


class RenderWindow(QDialog):
    """高清渲染导出窗口"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("高清渲染导出")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.resize(600, 400)
        
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
        
        self.output_label = QLabel("输出目录: 未选择")
        info_layout.addWidget(self.output_label)
        
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
        
        self.select_output_btn = QPushButton("选择输出目录")
        self.select_output_btn.clicked.connect(self.select_output_directory)
        button_layout.addWidget(self.select_output_btn)
        
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
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        
        if directory:
            self.output_dir = directory
            self.output_label.setText(f"输出目录: {directory}")
            
    def start_render(self):
        """开始渲染"""
        if not self.sequence_name:
            QMessageBox.warning(self, "警告", "请先选择序列")
            return
            
        if not self.output_dir:
            QMessageBox.warning(self, "警告", "请先选择输出目录")
            return
            
        if not self.config.get("algorithms"):
            QMessageBox.warning(self, "警告", "没有算法数据")
            return
            
        # 禁用按钮
        self.start_btn.setEnabled(False)
        self.select_output_btn.setEnabled(False)
        
        # 创建渲染工作线程
        self.render_worker = RenderWorker(self.config, self.sequence_name, self.output_dir)
        self.render_worker.progress_updated.connect(self.on_progress_updated)
        self.render_worker.finished.connect(self.on_render_finished)
        self.render_worker.start()
        
        self.log_text.append("开始高清渲染...")
        
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