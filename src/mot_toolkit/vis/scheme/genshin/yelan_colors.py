"""夜兰主题配色方案实现
基于官方角色配色提取的专业配色方案
"""

from typing import List, Tuple, Dict, Any
from mot_toolkit.vis.common.base_colors import BaseColorScheme


class YelanColorScheme(BaseColorScheme):
    """夜兰主题配色方案"""

    @property
    def name(self) -> str:
        return "Yelan Color Scheme"

    @property
    def colors(self) -> List[Tuple[int, int, int]]:
        return [
            (24, 27, 48),  # 深色调，近黑色
            (115, 109, 123),  # 灰色调
            (244, 240, 238),  # 近白色
            (136, 169, 202),  # 浅蓝色
            (45, 51, 126),  # 深蓝色
        ]

    @property
    def dark_navy(self) -> Tuple[int, int, int]:
        """深色调 - 适用于图表背景、边框线"""
        return self.colors[0]

    @property
    def gray(self) -> Tuple[int, int, int]:
        """灰色调 - 适用于次要元素、文本"""
        return self.colors[1]

    @property
    def off_white(self) -> Tuple[int, int, int]:
        """近白色 - 适用于背景、对比元素"""
        return self.colors[2]

    @property
    def light_blue(self) -> Tuple[int, int, int]:
        """浅蓝色 - 适用于主要数据系列、图表元素"""
        return self.colors[3]

    @property
    def deep_blue(self) -> Tuple[int, int, int]:
        """深蓝色 - 适用于强调色、重点数据"""
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
