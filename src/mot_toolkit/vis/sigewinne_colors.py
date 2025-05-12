"""希格雯主题配色方案实现
基于图片内容提取的低饱和度专业配色方案
"""

from typing import List, Tuple, Dict, Any
from .base_colors import BaseColorScheme


class SIGEWINNEColorScheme(BaseColorScheme):
    """希格雯主题配色方案"""

    @property
    def name(self) -> str:
        return "SIGEWINNE Color Scheme"

    @property
    def colors(self) -> List[Tuple[int, int, int]]:
        return [
            (81, 132, 178),  # 深蓝
            (170, 212, 248),  # 浅蓝
            (242, 245, 250),  # 白
            (241, 167, 181),  # 浅粉
            (213, 82, 118),  # 深粉
        ]

    @property
    def dark_blue(self) -> Tuple[int, int, int]:
        """深蓝色 - 适用于图表背景、坐标轴线"""
        return self.colors[0]

    @property
    def light_blue(self) -> Tuple[int, int, int]:
        """浅蓝色 - 适用于数据系列主色（柱状图）"""
        return self.colors[1]

    @property
    def white(self) -> Tuple[int, int, int]:
        """白色 - 适用于文字、网格线、装饰元素"""
        return self.colors[2]

    @property
    def light_pink(self) -> Tuple[int, int, int]:
        """浅粉色 - 适用于数据系列辅助色"""
        return self.colors[3]

    @property
    def dark_pink(self) -> Tuple[int, int, int]:
        """深粉色 - 适用于强调色（重点数据标注）"""
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
