"""枫原万叶主题配色方案实现
基于官方角色配色提取的专业配色方案
"""

from typing import List, Tuple, Dict, Any
from mot_toolkit.vis.common.base_colors import BaseColorScheme


class KazuhaColorScheme(BaseColorScheme):
    """枫原万叶主题配色方案"""

    @property
    def name(self) -> str:
        return "Kazuha Color Scheme"

    @property
    def colors(self) -> List[Tuple[int, int, int]]:
        return [
            (33, 25, 24),  # 深黑褐色调
            (100, 26, 17),  # 深红棕色调
            (195, 56, 40),  # 鲜红色调
            (231, 218, 205),  # 浅米色调
            (170, 221, 214),  # 浅青色调
        ]

    @property
    def dark_brown(self) -> Tuple[int, int, int]:
        """深黑褐色调 - 适用于图表背景、边框线"""
        return self.colors[0]

    @property
    def deep_red_brown(self) -> Tuple[int, int, int]:
        """深红棕色调 - 适用于次要元素、文本"""
        return self.colors[1]

    @property
    def vibrant_red(self) -> Tuple[int, int, int]:
        """鲜红色调 - 适用于强调色、重点数据"""
        return self.colors[2]

    @property
    def pale_cream(self) -> Tuple[int, int, int]:
        """浅米色调 - 适用于背景、对比元素"""
        return self.colors[3]

    @property
    def light_teal(self) -> Tuple[int, int, int]:
        """浅青色调 - 适用于主要数据系列、图表元素"""
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
