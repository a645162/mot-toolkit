"""申鹤主题配色方案实现
基于官方角色配色提取的专业配色方案
"""

from typing import List, Tuple, Dict, Any
from mot_toolkit.vis.common.base_colors import BaseColorScheme


class ShenheColorScheme(BaseColorScheme):
    """申鹤主题配色方案"""

    @property
    def name(self) -> str:
        return "Shenhe Color Scheme"

    @property
    def colors(self) -> List[Tuple[int, int, int]]:
        return [
            (35, 43, 54),  # 深海军蓝色调
            (81, 124, 137),  # 青蓝色调
            (180, 191, 208),  # 淡蓝灰色调
            (134, 148, 173),  # 蓝灰色调
            (156, 49, 41),  # 红褐色调
        ]

    @property
    def dark_navy(self) -> Tuple[int, int, int]:
        """深海军蓝色调 - 适用于图表背景、边框线"""
        return self.colors[0]

    @property
    def teal_blue(self) -> Tuple[int, int, int]:
        """青蓝色调 - 适用于主要数据系列、图表元素"""
        return self.colors[1]

    @property
    def pale_blue_gray(self) -> Tuple[int, int, int]:
        """淡蓝灰色调 - 适用于背景、次要元素"""
        return self.colors[2]

    @property
    def blue_gray(self) -> Tuple[int, int, int]:
        """蓝灰色调 - 适用于次要数据系列、辅助元素"""
        return self.colors[3]

    @property
    def red_brown(self) -> Tuple[int, int, int]:
        """红褐色调 - 适用于强调色、重点数据"""
        return self.colors[4]

    def get_color_map(self, style: str = "matplotlib") -> Dict[str, Any]:
        """生成颜色映射

        参数:
            style: 可视化库类型，支持 'matplotlib', 'seaborn', 'plotly'

        返回:
            根据不同库格式的颜色映射
        """
        if style == "matplotlib":
            return {
                "Sequential": self.colors,
                "Diverging": [self.colors[0], self.colors[-1]],
                "Categorical": self.colors,
            }
        elif style == "seaborn":
            return {"palette_main": self.colors, "palette_reversed": self.colors[::-1]}
        elif style == "plotly":
            return {"colors": self.hex_colors()}
        else:
            return dict(zip([f"C{i}" for i in range(len(self.colors))], self.colors))
