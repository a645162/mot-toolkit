"""大乔主题配色方案实现
基于王者荣耀角色大乔(白鹤梁神女)提取的专业配色方案
"""

from typing import List, Tuple, Dict, Any
from mot_toolkit.vis.common.base_colors import BaseColorScheme


class DaQiaoColorScheme(BaseColorScheme):
    """大乔主题配色方案"""

    @property
    def name(self) -> str:
        return "Da Qiao Color Scheme"

    @property
    def colors(self) -> List[Tuple[int, int, int]]:
        return [
            (160, 56, 22),  # 棕红色
            (241, 177, 84),  # 橙黄色
            (243, 211, 137),  # 浅黄色
            (183, 211, 190),  # 浅绿色
            (81, 131, 140),  # 青蓝色
        ]

    @property
    def brown_red(self) -> Tuple[int, int, int]:
        """棕红色 - 适用于强调色、重点数据"""
        return self.colors[0]

    @property
    def orange_yellow(self) -> Tuple[int, int, int]:
        """橙黄色 - 适用于主要数据系列、高亮元素"""
        return self.colors[1]

    @property
    def light_yellow(self) -> Tuple[int, int, int]:
        """浅黄色 - 适用于背景色、次要填充"""
        return self.colors[2]

    @property
    def light_green(self) -> Tuple[int, int, int]:
        """浅绿色 - 适用于辅助元素、过渡色"""
        return self.colors[3]

    @property
    def teal_blue(self) -> Tuple[int, int, int]:
        """青蓝色 - 适用于边框、文字、坐标轴"""
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
