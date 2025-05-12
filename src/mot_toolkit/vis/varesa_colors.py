"""瓦蕾莎主题配色方案实现
基于原神角色元神配色方案，适合视觉化展示
"""

from typing import List, Tuple, Dict, Any
from .base_colors import BaseColorScheme


class VARESAColorScheme(BaseColorScheme):
    """瓦蕾莎主题配色方案"""

    @property
    def name(self) -> str:
        return "VARESA Color Scheme"

    @property
    def colors(self) -> List[Tuple[int, int, int]]:
        return [
            (233, 134, 137),  # 粉红色
            (104, 217, 200),  # 薄荷绿
            (250, 235, 189),  # 淡黄色
            (68, 57, 65),  # 深灰色
            (141, 60, 144),  # 紫色
        ]

    @property
    def pink(self) -> Tuple[int, int, int]:
        """粉红色 - 适用于主要元素、突出显示"""
        return self.colors[0]

    @property
    def mint(self) -> Tuple[int, int, int]:
        """薄荷绿 - 适用于背景、次要元素"""
        return self.colors[1]

    @property
    def light_yellow(self) -> Tuple[int, int, int]:
        """淡黄色 - 适用于装饰元素、高亮区域"""
        return self.colors[2]

    @property
    def dark_gray(self) -> Tuple[int, int, int]:
        """深灰色 - 适用于文本、轮廓线"""
        return self.colors[3]

    @property
    def purple(self) -> Tuple[int, int, int]:
        """紫色 - 适用于强调色、特殊元素"""
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
