"""王者荣耀瑶主题配色方案实现
基于王者荣耀角色瑶的图片提取的专业配色方案
"""

from typing import List, Tuple, Dict, Any
from mot_toolkit.vis.common.base_colors import BaseColorScheme


class YaoColorScheme(BaseColorScheme):
    """王者荣耀瑶主题配色方案"""

    @property
    def name(self) -> str:
        return "Honor of Kings Yao Color Scheme"

    @property
    def colors(self) -> List[Tuple[int, int, int]]:
        return [
            (55, 127, 153),  # 青色
            (98, 178, 182),  # 浅青绿
            (242, 195, 203),  # 浅粉色
            (246, 166, 156),  # 粉橙色
            (163, 84, 83),  # 红褐色
        ]

    @property
    def teal(self) -> Tuple[int, int, int]:
        """青色 - 适用于图表背景、深色区域、主标题"""
        return self.colors[0]

    @property
    def light_teal(self) -> Tuple[int, int, int]:
        """浅青绿色 - 适用于数据系列主色、次要背景"""
        return self.colors[1]

    @property
    def light_pink(self) -> Tuple[int, int, int]:
        """浅粉色 - 适用于辅助元素、浅色区域、次要数据"""
        return self.colors[2]

    @property
    def coral(self) -> Tuple[int, int, int]:
        """粉橙色 - 适用于高亮数据、交互元素"""
        return self.colors[3]

    @property
    def burgundy(self) -> Tuple[int, int, int]:
        """红褐色 - 适用于强调色、重点突出、对比元素"""
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
