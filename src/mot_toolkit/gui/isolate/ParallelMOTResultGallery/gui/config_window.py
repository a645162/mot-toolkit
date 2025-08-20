"""配置窗口"""

import os
import json

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QFileDialog,
    QGroupBox,
    QComboBox,
    QMessageBox,
    QCheckBox,
    QScrollArea,
    QWidget,
    QSpinBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent

from mot_toolkit.gui.isolate.ParallelMOTResultGallery.core import MOTResultLoader
from mot_toolkit.gui.isolate.ParallelMOTResultGallery.core.dataset_manager import DatasetManager


class ConfigWindow(QDialog):
    """配置窗口 - 用于设置算法目录和数据集路径"""

    config_changed = Signal(dict)  # 配置改变信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("配置设置")
        self.setModal(True)
        self.setFixedSize(700, 600)

        self.mot_loader = MOTResultLoader()
        self.dataset_manager = DatasetManager()
        self.dataset_path = ""
        self.selected_splits = ["train", "val", "test"]

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)

        # 算法目录组
        algo_group = QGroupBox("算法结果目录")
        algo_layout = QVBoxLayout(algo_group)

        # 目录列表
        self.dir_list = QListWidget()
        self.dir_list.itemDoubleClicked.connect(self.edit_algorithm_name)
        algo_layout.addWidget(self.dir_list)

        # 按钮组
        button_layout = QHBoxLayout()

        self.add_btn = QPushButton("添加目录")
        self.add_btn.clicked.connect(self.add_algorithm_directory)
        button_layout.addWidget(self.add_btn)

        self.remove_btn = QPushButton("移除选中")
        self.remove_btn.clicked.connect(self.remove_selected_directory)
        button_layout.addWidget(self.remove_btn)

        self.rename_btn = QPushButton("重命名")
        self.rename_btn.clicked.connect(self.edit_algorithm_name)
        button_layout.addWidget(self.rename_btn)

        algo_layout.addLayout(button_layout)

        # 数据集路径组
        dataset_group = QGroupBox("数据集路径")
        dataset_layout = QVBoxLayout(dataset_group)

        self.dataset_label = QLabel("未设置")
        dataset_layout.addWidget(self.dataset_label)

        dataset_btn_layout = QHBoxLayout()

        self.set_dataset_btn = QPushButton("设置数据集路径")
        self.set_dataset_btn.clicked.connect(self.set_dataset_path)
        dataset_btn_layout.addWidget(self.set_dataset_btn)

        self.auto_detect_btn = QPushButton("自动检测")
        self.auto_detect_btn.clicked.connect(self.auto_detect_dataset)
        dataset_btn_layout.addWidget(self.auto_detect_btn)

        dataset_layout.addLayout(dataset_btn_layout)

        # Split选择组
        split_group = QGroupBox("数据集Split选择")
        split_layout = QVBoxLayout(split_group)
        
        # 创建滚动区域用于split复选框
        split_scroll = QScrollArea()
        split_scroll.setWidgetResizable(True)
        split_scroll.setMaximumHeight(100)
        
        self.split_widget = QWidget()
        self.split_layout = QVBoxLayout(self.split_widget)
        self.split_checkboxes = {}
        
        split_scroll.setWidget(self.split_widget)
        split_layout.addWidget(split_scroll)

        # 预览设置组
        preview_group = QGroupBox("预览设置")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_frames_spin = QSpinBox()
        self.preview_frames_spin.setRange(1, 10)
        self.preview_frames_spin.setValue(5)
        self.preview_frames_spin.setSuffix(" 张")
        preview_layout.addWidget(QLabel("连续帧预览数量:"))
        preview_layout.addWidget(self.preview_frames_spin)

        # 序列选择组
        seq_group = QGroupBox("可用序列")
        seq_layout = QVBoxLayout(seq_group)

        self.sequence_combo = QComboBox()
        seq_layout.addWidget(self.sequence_combo)

        # 底部按钮
        bottom_layout = QHBoxLayout()

        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self.accept)
        bottom_layout.addWidget(self.ok_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(self.cancel_btn)

        # 添加到主布局
        layout.addWidget(algo_group)
        layout.addWidget(dataset_group)
        layout.addWidget(split_group)
        layout.addWidget(preview_group)
        layout.addWidget(seq_group)
        layout.addLayout(bottom_layout)

    def add_algorithm_directory(self):
        """添加算法目录"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择算法结果目录",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )

        if directory:
            algorithm_name = (
                os.path.basename(directory)
                or f"算法{len(self.mot_loader.get_algorithms()) + 1}"
            )

            print(f"[DEBUG] 尝试添加算法目录: {directory}")
            success = self.mot_loader.add_algorithm_directory(directory, algorithm_name)
            print(f"[DEBUG] 添加算法结果: {success}")
            print(f"[DEBUG] 当前算法列表: {self.mot_loader.get_algorithms()}")
            
            if success:
                item = QListWidgetItem(f"{algorithm_name} - {directory}")
                item.setData(Qt.UserRole, (algorithm_name, directory))
                self.dir_list.addItem(item)
                self.update_sequences()
                
                # 立即保存配置
                config = self.get_config()
                self.config_changed.emit(config)
                print("[DEBUG] 添加算法后立即发送配置信号")
            else:
                QMessageBox.warning(self, "警告", "目录中没有找到有效的MOT结果文件")

    def remove_selected_directory(self):
        """移除选中的目录"""
        current_item = self.dir_list.currentItem()
        if current_item:
            algorithm_name, _ = current_item.data(Qt.UserRole)
            print(f"[DEBUG] 移除算法: {algorithm_name}")
            self.mot_loader.remove_algorithm(algorithm_name)
            self.dir_list.takeItem(self.dir_list.row(current_item))
            self.update_sequences()
            
            # 立即保存配置
            config = self.get_config()
            self.config_changed.emit(config)
            print("[DEBUG] 移除算法后立即发送配置信号")

    def edit_algorithm_name(self):
        """编辑算法名称"""
        current_item = self.dir_list.currentItem()
        if current_item:
            from PySide6.QtWidgets import QInputDialog
            
            old_name, old_path = current_item.data(Qt.UserRole)
            new_name, ok = QInputDialog.getText(
                self,
                "重命名算法",
                "请输入新的算法名称：",
                text=old_name
            )
            
            if ok and new_name and new_name != old_name:
                # 更新显示
                current_item.setText(f"{new_name} - {old_path}")
                current_item.setData(Qt.UserRole, (new_name, old_path))
                
                # 更新MOT加载器
                self.mot_loader.remove_algorithm(old_name)
                self.mot_loader.add_algorithm_directory(old_path, new_name)
                
                self.update_sequences()
                
                # 立即保存配置
                config = self.get_config()
                self.config_changed.emit(config)

    def set_dataset_path(self):
        """设置数据集路径"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择数据集目录",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )

        if directory:
            self.dataset_path = directory
            self.dataset_label.setText(directory)
            self.dataset_manager.set_dataset_path(directory)
            self.update_split_checkboxes()
            self.update_sequences()

    def auto_detect_dataset(self):
        """自动检测数据集"""
        if not self.dataset_path:
            QMessageBox.warning(self, "警告", "请先设置数据集路径")
            return

        available_splits = self.dataset_manager.get_available_splits()
        if available_splits:
            sequences = self.dataset_manager.get_sequences()
            QMessageBox.information(
                self, "成功",
                f"检测到DanceTrack格式，可用split: {', '.join(available_splits)}\n"
                f"共{len(sequences)}个序列"
            )
            self.update_split_checkboxes()
            self.update_sequences()
        else:
            QMessageBox.warning(self, "警告", "未检测到标准数据集格式")

    def update_split_checkboxes(self):
        """更新split复选框"""
        # 清除现有复选框
        for checkbox in self.split_checkboxes.values():
            checkbox.deleteLater()
        self.split_checkboxes.clear()

        # 获取可用split
        available_splits = self.dataset_manager.get_available_splits()
        
        for split in available_splits:
            checkbox = QCheckBox(split)
            checkbox.setChecked(split in self.selected_splits)
            checkbox.stateChanged.connect(self.on_split_changed)
            self.split_checkboxes[split] = checkbox
            self.split_layout.addWidget(checkbox)

    def on_split_changed(self):
        """split选择改变时的处理"""
        selected_splits = []
        for split, checkbox in self.split_checkboxes.items():
            if checkbox.isChecked():
                selected_splits.append(split)
        
        print(f"[DEBUG] on_split_changed: 选择的splits = {selected_splits}")
        self.selected_splits = selected_splits
        self.dataset_manager.set_selected_splits(selected_splits)
        self.update_sequences()
        
        # 立即保存配置
        config = self.get_config()
        print(f"[DEBUG] on_split_changed: 发送配置信号")
        self.config_changed.emit(config)

    def update_sequences(self):
        """更新序列列表"""
        self.sequence_combo.clear()
        sequences = self.dataset_manager.get_sequences()
        self.sequence_combo.addItems(sequences)

    def get_config(self) -> dict:
        """获取当前配置"""
        algorithms = {}
        for i in range(self.dir_list.count()):
            item = self.dir_list.item(i)
            name, path = item.data(Qt.UserRole)
            algorithms[name] = path

        config = {
            "algorithms": algorithms,
            "dataset_path": self.dataset_path,
            "selected_splits": self.selected_splits,
            "sequence_paths": self.dataset_manager.sequence_paths,
            "preview_frames": self.preview_frames_spin.value(),
        }
        print(f"[DEBUG] ConfigWindow.get_config() 返回配置: {json.dumps(config, indent=2, ensure_ascii=False)}")
        print(f"[DEBUG] 算法列表: {list(algorithms.keys())}")
        return config

    def set_config(self, config: dict):
        """设置配置"""
        print(f"[DEBUG] ConfigWindow.set_config() 接收到配置: {json.dumps(config, indent=2, ensure_ascii=False)}")
        print(f"[DEBUG] 配置中的算法: {list(config.get('algorithms', {}).keys())}")
        
        self.mot_loader = MOTResultLoader()
        self.dir_list.clear()

        algorithms = config.get("algorithms", {})
        for name, path in algorithms.items():
            print(f"[DEBUG] 设置算法: {name} -> {path}")
            if self.mot_loader.add_algorithm_directory(path, name):
                item = QListWidgetItem(f"{name} - {path}")
                item.setData(Qt.UserRole, (name, path))
                self.dir_list.addItem(item)
                print(f"[DEBUG] 成功添加算法到列表: {name}")
            else:
                print(f"[DEBUG] 添加算法失败: {name}")

        self.dataset_path = config.get("dataset_path", "")
        self.dataset_label.setText(self.dataset_path or "未设置")
        
        # 设置dataset manager
        self.dataset_manager.set_dataset_path(self.dataset_path)
        
        # 设置选择的splits
        self.selected_splits = config.get("selected_splits", ["train", "val", "test"])
        self.dataset_manager.set_selected_splits(self.selected_splits)
        
        print(f"[DEBUG] ConfigWindow.set_config() 设置selected_splits: {self.selected_splits}")
        
        # 更新UI
        self.update_split_checkboxes()
        self.update_sequences()
        
        # 设置预览帧数
        preview_frames = config.get("preview_frames", 5)
        self.preview_frames_spin.setValue(preview_frames)

    def closeEvent(self, event: QCloseEvent):
        """关闭事件"""
        print("[DEBUG] ConfigWindow.closeEvent: 窗口关闭，发送最终配置")
        config = self.get_config()
        print(f"[DEBUG] ConfigWindow.closeEvent: 最终配置 = {json.dumps(config, indent=2, ensure_ascii=False)}")
        self.config_changed.emit(config)
        super().closeEvent(event)
