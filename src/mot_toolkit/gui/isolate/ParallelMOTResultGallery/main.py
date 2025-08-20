#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多目标跟踪结果并行对比可视化工具

主程序入口
"""

import sys
import json
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
from PySide6.QtGui import QCloseEvent

from mot_toolkit.gui.isolate.ParallelMOTResultGallery.gui.config_window import (
    ConfigWindow,
)
from mot_toolkit.gui.isolate.ParallelMOTResultGallery.gui.preview_window import (
    PreviewWindow,
)
from mot_toolkit.gui.isolate.ParallelMOTResultGallery.core.dataset_manager import (
    DatasetManager,
)


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
            "sequence_paths": {},
        }
        self.config_file = Path(__file__).parent / "config.json"
        self.dataset_manager = DatasetManager()

        # 子窗口 - 只保留配置窗口
        self.config_window = None
        self.preview_windows = []

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
                print(f"[DEBUG] 正在从 {self.config_file} 加载配置")
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                # 确保新配置项存在
                if "preview_frames" not in self.config:
                    self.config["preview_frames"] = 5
                print(
                    f"[DEBUG] 加载到的配置: {json.dumps(self.config, indent=2, ensure_ascii=False)}"
                )
                self.update_ui_from_config()
            except Exception as e:
                print(f"[ERROR] 加载配置文件失败: {e}")
                QMessageBox.warning(self, "警告", f"加载配置文件失败: {e}")
        else:
            # 默认配置
            self.config = {
                "algorithms": {},
                "dataset_path": "",
                "selected_splits": ["train", "val", "test"],
                "sequence_paths": {},
                "preview_frames": 5,
            }

    def save_config(self):
        """保存配置"""
        try:
            print(f"[DEBUG] 正在保存配置到: {self.config_file}")
            print(
                f"[DEBUG] 配置内容: {json.dumps(self.config, indent=2, ensure_ascii=False)}"
            )
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print("[DEBUG] 配置保存成功")
        except Exception as e:
            print(f"[ERROR] 保存配置文件失败: {e}")
            QMessageBox.warning(self, "警告", f"保存配置文件失败: {e}")

    def update_ui_from_config(self):
        """根据配置更新UI"""
        self.algo_count_label.setText(f"算法数量: {len(self.config['algorithms'])}")
        self.dataset_label.setText(
            f"数据集路径: {self.config['dataset_path'] or '未设置'}"
        )

        # 更新dataset manager
        self.dataset_manager.set_dataset_path(self.config.get("dataset_path", ""))
        selected_splits = self.config.get("selected_splits", ["train", "val", "test"])
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
        print("[DEBUG] MainWindow.on_config_changed: 接收到配置")
        self.config = config
        self.update_ui_from_config()
        self.save_config()

        # 确保dataset manager同步更新
        if self.config.get("dataset_path"):
            self.dataset_manager.set_dataset_path(self.config["dataset_path"])
            selected_splits = self.config.get(
                "selected_splits", ["train", "val", "test"]
            )
            print(
                f"[DEBUG] MainWindow.on_config_changed: 设置selected_splits = {selected_splits}"
            )
            self.dataset_manager.set_selected_splits(selected_splits)
            # 强制刷新序列列表
            sequences = self.dataset_manager.get_sequences()
            self.sequence_combo.clear()
            self.sequence_combo.addItems(sequences)

    def open_preview(self):
        """打开预览窗口 - 支持多个独立窗口"""
        if not self.config["algorithms"]:
            QMessageBox.warning(self, "警告", "请先添加算法结果目录")
            return

        if not self.config["dataset_path"]:
            QMessageBox.warning(self, "警告", "请先设置数据集路径")
            return

        if not self.sequence_combo.currentText():
            QMessageBox.warning(self, "警告", "请先选择序列")
            return

        # 创建新的独立预览窗口
        preview_window = PreviewWindow()
        preview_window.set_config(self.config)
        preview_window.set_sequence(self.sequence_combo.currentText())

        # 设置窗口位置偏移，避免重叠
        base_x, base_y = self.x(), self.y()
        offset = (
            len(
                [
                    w
                    for w in QApplication.topLevelWidgets()
                    if isinstance(w, PreviewWindow)
                ]
            )
            * 50
        )
        preview_window.move(base_x + 50 + offset, base_y + 50 + offset)

        preview_window.show()
        preview_window.raise_()
        preview_window.activateWindow()

        self.preview_windows.append(preview_window)

        # GC
        for _window in self.preview_windows:
            if not _window.isVisible():
                self.preview_windows.remove(_window)

    def on_sequence_changed(self, sequence: str):
        """序列改变时的处理 - 不再管理预览窗口"""
        pass

    def closeEvent(self, event: QCloseEvent):
        """关闭事件"""
        if self.config_window:
            self.config_window.close()
        # 不再管理预览窗口，让它们独立存在

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
