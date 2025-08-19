#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多目标跟踪结果并行对比可视化工具

主程序入口
"""

import sys
import json
import os
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QGroupBox,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent

from gui.config_window import ConfigWindow
from gui.preview_window import PreviewWindow
from core.dataset_manager import DatasetManager


class MainWindow(QMainWindow):
    """主窗口 - 用于选择序列和启动预览"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MOT结果对比工具 - 主控制")
        self.setGeometry(100, 100, 400, 300)

        # 配置
        self.config = {
            "algorithms": {},
            "dataset_path": "",
            "selected_splits": ["train", "val", "test"],
            "sequence_paths": {}
        }
        self.config_file = Path(__file__).parent / "config.json"
        self.dataset_manager = DatasetManager()

        # 子窗口
        self.config_window = None
        self.preview_window = None

        self.init_ui()
        self.load_config()

    def init_ui(self):
        """初始化UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # 配置信息组
        config_group = QGroupBox("当前配置")
        config_layout = QVBoxLayout(config_group)

        self.algo_count_label = QLabel("算法数量: 0")
        config_layout.addWidget(self.algo_count_label)

        self.dataset_label = QLabel("数据集路径: 未设置")
        config_layout.addWidget(self.dataset_label)

        self.splits_label = QLabel("选择Split: 未设置")
        config_layout.addWidget(self.splits_label)

        self.sequences_label = QLabel("可用序列: 0")
        config_layout.addWidget(self.sequences_label)

        # 序列选择组
        seq_group = QGroupBox("序列选择")
        seq_layout = QVBoxLayout(seq_group)

        self.sequence_combo = QComboBox()
        self.sequence_combo.currentTextChanged.connect(self.on_sequence_changed)
        seq_layout.addWidget(self.sequence_combo)

        # 按钮组
        button_layout = QHBoxLayout()

        self.config_btn = QPushButton("配置设置")
        self.config_btn.clicked.connect(self.open_config)
        button_layout.addWidget(self.config_btn)

        self.preview_btn = QPushButton("开始预览")
        self.preview_btn.clicked.connect(self.open_preview)
        button_layout.addWidget(self.preview_btn)

        # 添加到主布局
        layout.addWidget(config_group)
        layout.addWidget(seq_group)
        layout.addLayout(button_layout)

    def load_config(self):
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                self.update_ui_from_config()
            except Exception as e:
                QMessageBox.warning(self, "警告", f"加载配置文件失败: {e}")

    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"保存配置文件失败: {e}")

    def update_ui_from_config(self):
        """根据配置更新UI"""
        self.algo_count_label.setText(f"算法数量: {len(self.config['algorithms'])}")
        self.dataset_label.setText(
            f"数据集路径: {self.config['dataset_path'] or '未设置'}"
        )
        
        # 更新dataset manager
        self.dataset_manager.set_dataset_path(self.config.get('dataset_path', ''))
        selected_splits = self.config.get('selected_splits', ['train', 'val', 'test'])
        self.dataset_manager.set_selected_splits(selected_splits)
        
        self.splits_label.setText(
            f"选择Split: {', '.join(selected_splits) if selected_splits else '未设置'}"
        )
        
        sequences = self.dataset_manager.get_sequences()
        self.sequences_label.setText(f"可用序列: {len(sequences)}")

        self.sequence_combo.clear()
        self.sequence_combo.addItems(sequences)

    def open_config(self):
        """打开配置窗口"""
        if not self.config_window:
            self.config_window = ConfigWindow(self)
            self.config_window.config_changed.connect(self.on_config_changed)

        self.config_window.set_config(self.config)
        self.config_window.show()
        self.config_window.raise_()
        self.config_window.activateWindow()

    def on_config_changed(self, config: dict):
        """配置改变时的处理"""
        self.config = config
        self.update_ui_from_config()
        self.save_config()
        
        # 确保dataset manager同步更新
        if self.config.get('dataset_path'):
            self.dataset_manager.set_dataset_path(self.config['dataset_path'])
            selected_splits = self.config.get('selected_splits', ['train', 'val', 'test'])
            self.dataset_manager.set_selected_splits(selected_splits)
            # 强制刷新序列列表
            sequences = self.dataset_manager.get_sequences()
            self.sequence_combo.clear()
            self.sequence_combo.addItems(sequences)

    def open_preview(self):
        """打开预览窗口"""
        if not self.config["algorithms"]:
            QMessageBox.warning(self, "警告", "请先添加算法结果目录")
            return

        if not self.config["dataset_path"]:
            QMessageBox.warning(self, "警告", "请先设置数据集路径")
            return

        if not self.sequence_combo.currentText():
            QMessageBox.warning(self, "警告", "请先选择序列")
            return

        if not self.preview_window:
            self.preview_window = PreviewWindow(self)

        self.preview_window.set_config(self.config)
        self.preview_window.set_sequence(self.sequence_combo.currentText())
        self.preview_window.show()
        self.preview_window.raise_()
        self.preview_window.activateWindow()

    def on_sequence_changed(self, sequence: str):
        """序列改变时的处理"""
        if sequence and self.preview_window and self.preview_window.isVisible():
            self.preview_window.set_sequence(sequence)

    def closeEvent(self, event: QCloseEvent):
        """关闭事件"""
        if self.config_window:
            self.config_window.close()
        if self.preview_window:
            self.preview_window.close()

        self.save_config()
        super().closeEvent(event)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
