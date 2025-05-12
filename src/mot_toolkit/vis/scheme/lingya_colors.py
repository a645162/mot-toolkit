"""玲芽之旅主题配色方案实现
基于动漫风格图片中提取的自然色彩配色方案
"""

from typing import List, Tuple, Dict, Any
from mot_toolkit.vis.common.base_colors import BaseColorScheme


class LINGYAColorScheme(BaseColorScheme):
    """玲芽之旅主题配色方案"""

    @property
    def name(self) -> str:
        return "LINGYA Color Scheme"

    @property
    def colors(self) -> List[Tuple[int, int, int]]:
        return [
            (42, 68, 88),  # 深蓝灰
            (62, 134, 181),  # 中蓝
            (149, 167, 126),  # 青绿
            (229, 190, 121),  # 浅黄
            (51, 100, 133),  # 靛蓝
        ]

    @property
    def deep_navy(self) -> Tuple[int, int, int]:
        """深蓝灰色 - 适用于图表背景、标题文字"""
        return self.colors[0]

    @property
    def medium_blue(self) -> Tuple[int, int, int]:
        """中蓝色 - 适用于主要数据系列、强调元素"""
        return self.colors[1]

    @property
    def teal_green(self) -> Tuple[int, int, int]:
        """青绿色 - 适用于次要数据系列、辅助元素"""
        return self.colors[2]

    @property
    def light_yellow(self) -> Tuple[int, int, int]:
        """浅黄色 - 适用于突出显示、对比元素"""
        return self.colors[3]

    @property
    def indigo(self) -> Tuple[int, int, int]:
        """靛蓝色 - 适用于边框、分隔线、装饰元素"""
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
                "Diverging": [self.colors[0], self.colors[3]],
                "Categorical": self.colors,
            }
        elif style == "seaborn":
            return {"palette_main": self.colors, "palette_reversed": self.colors[::-1]}
        elif style == "plotly":
            return {"colors": self.hex_colors()}
        else:
            return dict(zip([f"C{i}" for i in range(len(self.colors))], self.colors))
