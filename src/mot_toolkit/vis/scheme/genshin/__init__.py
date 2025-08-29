from typing import List

from .sigewinne_colors import SIGEWINNEColorScheme
from .varesa_colors import VARESAColorScheme
from .ayaka_colors import AyakaColorScheme
from .kazuha_colors import KazuhaColorScheme
from .kokomi_colors import KokomiColorScheme
from .march_seventh_colors import MarchSeventhColorScheme
from .shenhe_colors import ShenheColorScheme
from .yelan_colors import YelanColorScheme
from .xilonen_colors import XilonenColorScheme


all = [
    SIGEWINNEColorScheme,
    VARESAColorScheme,
    AyakaColorScheme,
    KazuhaColorScheme,
    KokomiColorScheme,
    MarchSeventhColorScheme,
    ShenheColorScheme,
    YelanColorScheme,
    XilonenColorScheme,
]


def init_all() -> List:
    """
    初始化所有配色方案
    """

    return_list = []

    for color_scheme in all:
        return_list.append(color_scheme())

    return return_list
