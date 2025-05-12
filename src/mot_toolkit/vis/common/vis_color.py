"""颜色方案模块入口文件
提供用于数据可视化的颜色方案和工具函数
"""

from .base_colors import BaseColorScheme, rgb_to_hex, hex_to_rgb
from .sigewinne_colors import SIGEWINNEColorScheme
from .utils import apply_to_matplotlib, example_usage

__all__ = [
    "BaseColorScheme",
    "SIGEWINNEColorScheme",
    "rgb_to_hex",
    "hex_to_rgb",
    "apply_to_matplotlib",
    "example_usage",
]
