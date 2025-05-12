"""神里绫华主题配色方案实现
基于官方角色配色提取的专业配色方案
"""

from typing import List, Tuple, Dict, Any
from mot_toolkit.vis.common.base_colors import BaseColorScheme


class AyakaColorScheme(BaseColorScheme):
    """神里绫华主题配色方案"""

    @property
    def name(self) -> str:
        return "Ayaka Color Scheme"

    @property
    def colors(self) -> List[Tuple[int, int, int]]:
        return [
            (71, 85, 142),  # 蓝色调
            (105, 130, 185),  # 亮蓝色调
            (188, 202, 224),  # 淡蓝色调
            (241, 239, 236),  # 近白色调
            (174, 107, 129),  # 粉紫色调
            (130, 45, 74),  # 深红紫色调
        ]

    @property
    def blue(self) -> Tuple[int, int, int]:
        """蓝色调 - 适用于主要图表背景、边框线"""
        return self.colors[0]

    @property
    def bright_blue(self) -> Tuple[int, int, int]:
        """亮蓝色调 - 适用于主要数据系列、图表元素"""
        return self.colors[1]

    @property
    def light_blue(self) -> Tuple[int, int, int]:
        """淡蓝色调 - 适用于次要元素、辅助数据"""
        return self.colors[2]

    @property
    def off_white(self) -> Tuple[int, int, int]:
        """近白色调 - 适用于背景、对比元素"""
        return self.colors[3]

    @property
    def pink_purple(self) -> Tuple[int, int, int]:
        """粉紫色调 - 适用于强调色、次要重点"""
        return self.colors[4]

    @property
    def deep_burgundy(self) -> Tuple[int, int, int]:
        """深红紫色调 - 适用于主要强调色、重点数据"""
        return self.colors[5]

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
