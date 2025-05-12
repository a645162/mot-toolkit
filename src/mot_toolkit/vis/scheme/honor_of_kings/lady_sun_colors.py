"""孙尚香主题配色方案实现
基于"水果甜心"孙尚香皮肤的清新时尚配色方案
"""

from typing import List, Tuple, Dict, Any
from mot_toolkit.vis.common.base_colors import BaseColorScheme


class LadySunColorScheme(BaseColorScheme):
    """孙尚香主题配色方案"""

    @property
    def name(self) -> str:
        return "Lady Sun Color Scheme"

    @property
    def colors(self) -> List[Tuple[int, int, int]]:
        return [
            (166, 221, 231),  # 浅青色
            (246, 225, 175),  # 浅黄色
            (236, 186, 189),  # 浅粉色
            (70, 111, 135),  # 深蓝色
            (222, 179, 108),  # 金黄色
            (214, 87, 92),  # 红色
        ]

    @property
    def light_cyan(self) -> Tuple[int, int, int]:
        """浅青色 - 适用于背景、次要元素"""
        return self.colors[0]

    @property
    def light_yellow(self) -> Tuple[int, int, int]:
        """浅黄色 - 适用于高亮区域、明亮元素"""
        return self.colors[1]

    @property
    def light_pink(self) -> Tuple[int, int, int]:
        """浅粉色 - 适用于柔和过渡、辅助色"""
        return self.colors[2]

    @property
    def dark_blue(self) -> Tuple[int, int, int]:
        """深蓝色 - 适用于文字、边框、线条"""
        return self.colors[3]

    @property
    def gold(self) -> Tuple[int, int, int]:
        """金黄色 - 适用于强调元素、装饰"""
        return self.colors[4]

    @property
    def red(self) -> Tuple[int, int, int]:
        """红色 - 适用于关键点、警示信息"""
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
                "Diverging": [self.colors[3], self.colors[5]],
                "Categorical": self.colors,
            }
        elif style == "seaborn":
            return {"palette_main": self.colors, "palette_reversed": self.colors[::-1]}
        elif style == "plotly":
            return {"colors": self.hex_colors()}
        else:
            return dict(zip([f"C{i}" for i in range(len(self.colors))], self.colors))
