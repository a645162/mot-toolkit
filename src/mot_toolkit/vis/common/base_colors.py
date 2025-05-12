"""颜色方案基础模块
定义颜色方案的基类和基本工具函数
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any


class BaseColorScheme(ABC):
    """颜色方案基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """方案名称"""
        pass

    @property
    @abstractmethod
    def colors(self) -> List[Tuple[int, int, int]]:
        """RGB颜色列表"""
        pass

    def hex_colors(self) -> List[str]:
        """转换为HEX颜色码"""
        return [rgb_to_hex(r, g, b) for r, g, b in self.colors]

    @abstractmethod
    def get_color_map(self, style: str = "matplotlib") -> Dict[str, Any]:
        """生成颜色映射"""
        pass


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """RGB颜色转HEX颜色码

    参数:
        r: 红色分量 (0-255)
        g: 绿色分量 (0-255)
        b: 蓝色分量 (0-255)

    返回:
        HEX格式的颜色码，如 "#5184B2"
    """
    return f"#{r:02x}{g:02x}{b:02x}".upper()


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """HEX颜色码转RGB颜色

    参数:
        hex_color: HEX颜色码，如 "#5184B2"

    返回:
        RGB元组，如 (81, 132, 178)
    """
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
