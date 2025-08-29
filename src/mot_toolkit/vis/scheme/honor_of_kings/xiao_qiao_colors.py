"""小乔主题配色方案实现
基于王者荣耀角色小乔提取的明亮活泼专业配色方案
"""

from typing import List, Tuple, Dict, Any
from mot_toolkit.vis.common.base_colors import BaseColorScheme


class XiaoQiaoColorScheme(BaseColorScheme):
    """小乔主题配色方案"""

    @property
    def name(self) -> str:
        return "Xiao Qiao Color Scheme"

    @property
    def colors(self) -> List[Tuple[int, int, int]]:
        return [
            (219, 130, 48),  # 橙色
            (238, 217, 96),  # 黄色
            (151, 208, 228),  # 浅蓝
            (95, 150, 151),  # 青绿
            (63, 68, 108),  # 深蓝
        ]

    @property
    def orange(self) -> Tuple[int, int, int]:
        """橙色 - 适用于重点突出、主要数据系列"""
        return self.colors[0]

    @property
    def yellow(self) -> Tuple[int, int, int]:
        """黄色 - 适用于高亮元素、次要数据系列"""
        return self.colors[1]

    @property
    def light_blue(self) -> Tuple[int, int, int]:
        """浅蓝色 - 适用于背景、填充、温和元素"""
        return self.colors[2]

    @property
    def teal(self) -> Tuple[int, int, int]:
        """青绿色 - 适用于辅助数据、中性元素"""
        return self.colors[3]

    @property
    def dark_blue(self) -> Tuple[int, int, int]:
        """深蓝色 - 适用于文字、边框、底色"""
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
