"""玲芽之旅主题配色方案实现（粉紫色系）
基于《铃芽之旅》电影夜空场景提取的配色方案
"""

from typing import List, Tuple, Dict, Any
from mot_toolkit.vis.common.base_colors import BaseColorScheme


class SuzumePurpleColorScheme(BaseColorScheme):
    """玲芽之旅主题配色方案（粉紫色系）"""

    @property
    def name(self) -> str:
        return "Suzume Purple Color Scheme"

    @property
    def colors(self) -> List[Tuple[int, int, int]]:
        return [
            (17, 50, 93),  # 深蓝色
            (54, 80, 131),  # 中蓝色
            (115, 107, 157),  # 紫色
            (183, 131, 175),  # 浅紫/粉色
            (245, 166, 115),  # 橙色
            (252, 219, 114),  # 浅黄色
        ]

    @property
    def deep_blue(self) -> Tuple[int, int, int]:
        """深蓝色 - 适用于背景、图表底色"""
        return self.colors[0]

    @property
    def medium_blue(self) -> Tuple[int, int, int]:
        """中蓝色 - 适用于主要元素、标题区域"""
        return self.colors[1]

    @property
    def purple(self) -> Tuple[int, int, int]:
        """紫色 - 适用于强调元素、主数据系列"""
        return self.colors[2]

    @property
    def light_purple(self) -> Tuple[int, int, int]:
        """浅紫/粉色 - 适用于次要数据、突出元素"""
        return self.colors[3]

    @property
    def orange(self) -> Tuple[int, int, int]:
        """橙色 - 适用于高亮数据、对比元素"""
        return self.colors[4]

    @property
    def light_yellow(self) -> Tuple[int, int, int]:
        """浅黄色 - 适用于文本标注、装饰元素"""
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
