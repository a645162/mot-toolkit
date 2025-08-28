"""可视化设置窗口 - 提供丰富的绘制选项配置"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
    QColorDialog,
    QMessageBox,
    QComboBox,
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, Signal

from mot_toolkit.utils.logs import get_logger

LOGGER = get_logger()


class VisualizationSettingsWindow(QDialog):
    """可视化设置窗口 - 提供丰富的绘制选项配置"""
    
    settings_changed = Signal(dict)  # 配置改变信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("可视化设置")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.resize(500, 600)
        
        self.config = {}
        
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 边界框设置组
        bbox_group = QGroupBox("边界框设置")
        bbox_layout = QVBoxLayout(bbox_group)
        
        self.show_bbox_checkbox = QCheckBox("显示边界框")
        self.show_bbox_checkbox.setChecked(True)
        bbox_layout.addWidget(self.show_bbox_checkbox)
        
        bbox_thickness_layout = QHBoxLayout()
        bbox_thickness_layout.addWidget(QLabel("边界框线宽:"))
        self.bbox_thickness_spin = QSpinBox()
        self.bbox_thickness_spin.setRange(1, 10)
        self.bbox_thickness_spin.setValue(2)
        bbox_thickness_layout.addWidget(self.bbox_thickness_spin)
        bbox_layout.addLayout(bbox_thickness_layout)
        
        self.show_fill_checkbox = QCheckBox("显示填充")
        self.show_fill_checkbox.setChecked(True)
        bbox_layout.addWidget(self.show_fill_checkbox)
        
        fill_alpha_layout = QHBoxLayout()
        fill_alpha_layout.addWidget(QLabel("填充透明度:"))
        self.fill_alpha_spin = QDoubleSpinBox()
        self.fill_alpha_spin.setRange(0.0, 1.0)
        self.fill_alpha_spin.setSingleStep(0.1)
        self.fill_alpha_spin.setValue(0.3)
        fill_alpha_layout.addWidget(self.fill_alpha_spin)
        bbox_layout.addLayout(fill_alpha_layout)
        
        layout.addWidget(bbox_group)
        
        # 文本设置组
        text_group = QGroupBox("文本设置")
        text_layout = QVBoxLayout(text_group)
        
        self.show_id_checkbox = QCheckBox("显示跟踪ID")
        self.show_id_checkbox.setChecked(True)
        text_layout.addWidget(self.show_id_checkbox)
        
        self.show_confidence_checkbox = QCheckBox("显示置信度")
        self.show_confidence_checkbox.setChecked(False)
        text_layout.addWidget(self.show_confidence_checkbox)
        
        text_size_layout = QHBoxLayout()
        text_size_layout.addWidget(QLabel("文本大小:"))
        self.text_size_spin = QDoubleSpinBox()
        self.text_size_spin.setRange(0.5, 2.0)
        self.text_size_spin.setSingleStep(0.1)
        self.text_size_spin.setValue(0.7)
        text_size_layout.addWidget(self.text_size_spin)
        text_layout.addLayout(text_size_layout)
        
        layout.addWidget(text_group)
        
        # 颜色设置组
        color_group = QGroupBox("颜色设置")
        color_layout = QVBoxLayout(color_group)
        
        # 算法颜色模式
        color_mode_layout = QHBoxLayout()
        color_mode_layout.addWidget(QLabel("颜色模式:"))
        self.color_mode_combo = QComboBox()
        self.color_mode_combo.addItems(["按算法", "按跟踪ID", "固定颜色"])
        color_mode_layout.addWidget(self.color_mode_combo)
        color_layout.addLayout(color_mode_layout)
        
        # 固定颜色选择
        fixed_color_layout = QHBoxLayout()
        fixed_color_layout.addWidget(QLabel("固定颜色:"))
        self.fixed_color_btn = QPushButton("选择颜色")
        self.fixed_color_btn.clicked.connect(self.select_fixed_color)
        fixed_color_layout.addWidget(self.fixed_color_btn)
        self.fixed_color_preview = QLabel()
        self.fixed_color_preview.setFixedSize(30, 30)
        self.fixed_color_preview.setStyleSheet("background-color: rgb(255, 0, 255);")
        fixed_color_layout.addWidget(self.fixed_color_preview)
        color_layout.addLayout(fixed_color_layout)
        
        # GT颜色选择
        gt_color_layout = QHBoxLayout()
        gt_color_layout.addWidget(QLabel("GT颜色:"))
        self.gt_color_btn = QPushButton("选择颜色")
        self.gt_color_btn.clicked.connect(self.select_gt_color)
        gt_color_layout.addWidget(self.gt_color_btn)
        self.gt_color_preview = QLabel()
        self.gt_color_preview.setFixedSize(30, 30)
        self.gt_color_preview.setStyleSheet("background-color: rgb(0, 255, 0);")
        gt_color_layout.addWidget(self.gt_color_preview)
        color_layout.addLayout(gt_color_layout)
        
        layout.addWidget(color_group)
        
        # 高级设置组
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QVBoxLayout(advanced_group)
        
        self.show_trajectory_checkbox = QCheckBox("显示轨迹线")
        self.show_trajectory_checkbox.setChecked(False)
        advanced_layout.addWidget(self.show_trajectory_checkbox)
        
        trajectory_length_layout = QHBoxLayout()
        trajectory_length_layout.addWidget(QLabel("轨迹长度:"))
        self.trajectory_length_spin = QSpinBox()
        self.trajectory_length_spin.setRange(1, 50)
        self.trajectory_length_spin.setValue(10)
        trajectory_length_layout.addWidget(self.trajectory_length_spin)
        trajectory_length_layout.addWidget(QLabel("帧"))
        advanced_layout.addLayout(trajectory_length_layout)
        
        self.show_center_points_checkbox = QCheckBox("显示中心点")
        self.show_center_points_checkbox.setChecked(False)
        advanced_layout.addWidget(self.show_center_points_checkbox)
        
        # 从OpenCV预览窗口添加的功能
        self.different_color_checkbox = QCheckBox("不同目标使用不同颜色")
        self.different_color_checkbox.setChecked(True)
        advanced_layout.addWidget(self.different_color_checkbox)
        
        self.with_text_checkbox = QCheckBox("显示详细文本")
        self.with_text_checkbox.setChecked(False)
        advanced_layout.addWidget(self.with_text_checkbox)
        
        self.center_point_trajectory_checkbox = QCheckBox("中心点轨迹")
        self.center_point_trajectory_checkbox.setChecked(True)
        advanced_layout.addWidget(self.center_point_trajectory_checkbox)
        
        layout.addWidget(advanced_group)
        
        # 按钮组
        button_layout = QHBoxLayout()
        
        self.apply_btn = QPushButton("应用")
        self.apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_btn)
        
        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.reset_btn = QPushButton("重置")
        self.reset_btn.clicked.connect(self.reset_settings)
        button_layout.addWidget(self.reset_btn)
        
        layout.addLayout(button_layout)
        
        # 初始化默认配置
        self.reset_settings()
        
    def set_config(self, config):
        """设置配置"""
        self.config = config.copy()
        self.update_ui_from_config()
        
    def update_ui_from_config(self):
        """根据配置更新UI"""
        # 边界框设置
        self.show_bbox_checkbox.setChecked(self.config.get("show_bbox", True))
        self.bbox_thickness_spin.setValue(self.config.get("bbox_thickness", 2))
        self.show_fill_checkbox.setChecked(self.config.get("show_fill", True))
        self.fill_alpha_spin.setValue(self.config.get("fill_alpha", 0.3))
        
        # 文本设置
        self.show_id_checkbox.setChecked(self.config.get("show_id", True))
        self.show_confidence_checkbox.setChecked(self.config.get("show_confidence", False))
        self.text_size_spin.setValue(self.config.get("text_size", 0.7))
        
        # 颜色设置
        color_mode = self.config.get("color_mode", "按算法")
        index = self.color_mode_combo.findText(color_mode)
        if index >= 0:
            self.color_mode_combo.setCurrentIndex(index)
        
        # 固定颜色
        fixed_color = self.config.get("fixed_color", (255, 0, 255))
        self.fixed_color_preview.setStyleSheet(f"background-color: rgb({fixed_color[0]}, {fixed_color[1]}, {fixed_color[2]});")
        
        # GT颜色
        gt_color = self.config.get("gt_color", (0, 255, 0))
        self.gt_color_preview.setStyleSheet(f"background-color: rgb({gt_color[0]}, {gt_color[1]}, {gt_color[2]});")
        
        # 高级设置
        self.show_trajectory_checkbox.setChecked(self.config.get("show_trajectory", False))
        self.trajectory_length_spin.setValue(self.config.get("trajectory_length", 10))
        self.show_center_points_checkbox.setChecked(self.config.get("show_center_points", False))
        self.different_color_checkbox.setChecked(self.config.get("different_color", True))
        self.with_text_checkbox.setChecked(self.config.get("with_text", False))
        self.center_point_trajectory_checkbox.setChecked(self.config.get("center_point_trajectory", True))
        
    def get_config(self):
        """获取当前配置"""
        config = {
            # 边界框设置
            "show_bbox": self.show_bbox_checkbox.isChecked(),
            "bbox_thickness": self.bbox_thickness_spin.value(),
            "show_fill": self.show_fill_checkbox.isChecked(),
            "fill_alpha": self.fill_alpha_spin.value(),
            
            # 文本设置
            "show_id": self.show_id_checkbox.isChecked(),
            "show_confidence": self.show_confidence_checkbox.isChecked(),
            "text_size": self.text_size_spin.value(),
            
            # 颜色设置
            "color_mode": self.color_mode_combo.currentText(),
            "fixed_color": self.config.get("fixed_color", (255, 0, 255)),
            "gt_color": self.config.get("gt_color", (0, 255, 0)),
            
            # 高级设置
            "show_trajectory": self.show_trajectory_checkbox.isChecked(),
            "trajectory_length": self.trajectory_length_spin.value(),
            "show_center_points": self.show_center_points_checkbox.isChecked(),
            "different_color": self.different_color_checkbox.isChecked(),
            "with_text": self.with_text_checkbox.isChecked(),
            "center_point_trajectory": self.center_point_trajectory_checkbox.isChecked(),
        }
        return config
        
    def select_fixed_color(self):
        """选择固定颜色"""
        current_color = QColor(*self.config.get("fixed_color", (255, 0, 255)))
        color = QColorDialog.getColor(current_color, self, "选择固定颜色")
        if color.isValid():
            self.config["fixed_color"] = (color.red(), color.green(), color.blue())
            self.fixed_color_preview.setStyleSheet(
                f"background-color: rgb({color.red()}, {color.green()}, {color.blue()});"
            )
            
    def select_gt_color(self):
        """选择GT颜色"""
        current_color = QColor(*self.config.get("gt_color", (0, 255, 0)))
        color = QColorDialog.getColor(current_color, self, "选择GT颜色")
        if color.isValid():
            self.config["gt_color"] = (color.red(), color.green(), color.blue())
            self.gt_color_preview.setStyleSheet(
                f"background-color: rgb({color.red()}, {color.green()}, {color.blue()});"
            )
            
    def apply_settings(self):
        """应用设置"""
        new_config = self.get_config()
        self.settings_changed.emit(new_config)
        QMessageBox.information(self, "成功", "可视化设置已应用")
        
    def reset_settings(self):
        """重置为默认设置"""
        default_config = {
            "show_bbox": True,
            "bbox_thickness": 2,
            "show_fill": True,
            "fill_alpha": 0.3,
            "show_id": True,
            "show_confidence": False,
            "text_size": 0.7,
            "color_mode": "按算法",
            "fixed_color": (255, 0, 255),
            "gt_color": (0, 255, 0),
            "show_trajectory": False,
            "trajectory_length": 10,
            "show_center_points": False,
            "different_color": True,
            "with_text": False,
            "center_point_trajectory": True,
        }
        self.config = default_config.copy()
        self.update_ui_from_config()
        
    def accept(self):
        """确定按钮点击"""
        new_config = self.get_config()
        self.settings_changed.emit(new_config)
        super().accept()
        
    def reject(self):
        """取消按钮点击"""
        # 恢复原始配置
        if hasattr(self, '_original_config'):
            self.config = self._original_config.copy()
            self.update_ui_from_config()
        super().reject()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    window = VisualizationSettingsWindow()
    window.show()
    sys.exit(app.exec())