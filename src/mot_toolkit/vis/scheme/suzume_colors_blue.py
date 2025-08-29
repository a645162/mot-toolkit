"""玲芽之旅主题配色方案实现（蓝绿色系）
基于《铃芽之旅》电影日景场景提取的配色方案
"""

from typing import List, Tuple, Dict, Any
from mot_toolkit.vis.common.base_colors import BaseColorScheme


class SuzumeBlueColorScheme(BaseColorScheme):
    """玲芽之旅主题配色方案（蓝绿色系）"""

    @property
    def name(self) -> str:
        return "Suzume Blue Color Scheme"

    @property
    def colors(self) -> List[Tuple[int, int, int]]:
        return [
            (42, 68, 88),  # 深蓝色
            (51, 100, 133),  # 中蓝色
            (62, 134, 181),  # 浅蓝色
            (149, 167, 126),  # 青绿色
            (229, 190, 121),  # 浅黄色
        ]

    @property
    def deep_blue(self) -> Tuple[int, int, int]:
        """深蓝色 - 适用于背景、图表边框"""
        return self.colors[0]

    @property
    def medium_blue(self) -> Tuple[int, int, int]:
        """中蓝色 - 适用于主要元素、图表线条"""
        return self.colors[1]

    @property
    def light_blue(self) -> Tuple[int, int, int]:
        """浅蓝色 - 适用于主数据系列、水体表达"""
        return self.colors[2]

    @property
    def teal_green(self) -> Tuple[int, int, int]:
        """青绿色 - 适用于辅助数据、自然元素"""
        return self.colors[3]

    @property
    def light_yellow(self) -> Tuple[int, int, int]:
        """浅黄色 - 适用于高亮元素、阳光效果"""
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
