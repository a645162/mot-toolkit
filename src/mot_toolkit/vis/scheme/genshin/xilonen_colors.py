"""希诺宁主题配色方案实现
基于原神角色希诺宁官方配色提取的专业配色方案
"""

from typing import List, Tuple, Dict, Any
from mot_toolkit.vis.common.base_colors import BaseColorScheme


class XilonenColorScheme(BaseColorScheme):
    """希诺宁主题配色方案"""

    @property
    def name(self) -> str:
        return "Xilonen Color Scheme"

    @property
    def colors(self) -> List[Tuple[int, int, int]]:
        return [
            (68, 62, 60),  # 深色调，近黑色
            (229, 134, 45),  # 橙色调
            (240, 210, 84),  # 黄色调
            (249, 239, 214),  # 浅米色
            (98, 204, 185),  # 薄荷绿
            (66, 136, 126),  # 深绿色
        ]

    @property
    def dark_gray(self) -> Tuple[int, int, int]:
        """深色调 - 适用于图表背景、边框线"""
        return self.colors[0]

    @property
    def orange(self) -> Tuple[int, int, int]:
        """橙色调 - 适用于突出显示、警告元素"""
        return self.colors[1]

    @property
    def yellow(self) -> Tuple[int, int, int]:
        """黄色调 - 适用于高亮、次要强调色"""
        return self.colors[2]

    @property
    def light_beige(self) -> Tuple[int, int, int]:
        """浅米色 - 适用于背景、对比元素"""
        return self.colors[3]

    @property
    def mint_green(self) -> Tuple[int, int, int]:
        """薄荷绿 - 适用于主要数据系列、图表元素"""
        return self.colors[4]

    @property
    def deep_green(self) -> Tuple[int, int, int]:
        """深绿色 - 适用于强调色、重点数据"""
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
