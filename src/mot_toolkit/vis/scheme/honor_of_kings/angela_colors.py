"""安琪拉主题配色方案实现
基于王者荣耀角色安琪拉提取的暖色系专业配色方案
"""

from typing import List, Tuple, Dict, Any
from mot_toolkit.vis.common.base_colors import BaseColorScheme


class AngelaColorScheme(BaseColorScheme):
    """安琪拉主题配色方案"""

    @property
    def name(self) -> str:
        return "Angela Color Scheme"

    @property
    def colors(self) -> List[Tuple[int, int, int]]:
        return [
            (38, 34, 46),  # 近黑色
            (91, 82, 82),  # 深灰色
            (162, 151, 130),  # 灰棕色
            (251, 244, 189),  # 浅黄色
            (246, 222, 154),  # 淡黄色
            (236, 198, 126),  # 金黄色
            (222, 170, 103),  # 深金黄色
        ]

    @property
    def black(self) -> Tuple[int, int, int]:
        """近黑色 - 适用于深色背景、主要文字"""
        return self.colors[0]

    @property
    def dark_gray(self) -> Tuple[int, int, int]:
        """深灰色 - 适用于次要文字、边框"""
        return self.colors[1]

    @property
    def gray_brown(self) -> Tuple[int, int, int]:
        """灰棕色 - 适用于中性元素、过渡色"""
        return self.colors[2]

    @property
    def light_yellow(self) -> Tuple[int, int, int]:
        """浅黄色 - 适用于高亮背景、主要区域"""
        return self.colors[3]

    @property
    def pale_yellow(self) -> Tuple[int, int, int]:
        """淡黄色 - 适用于次要高亮、辅助区域"""
        return self.colors[4]

    @property
    def gold(self) -> Tuple[int, int, int]:
        """金黄色 - 适用于重点元素、强调色"""
        return self.colors[5]

    @property
    def dark_gold(self) -> Tuple[int, int, int]:
        """深金黄色 - 适用于关键数据、特殊标记"""
        return self.colors[6]

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
