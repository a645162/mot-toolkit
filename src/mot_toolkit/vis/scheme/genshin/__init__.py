from typing import List

from .sigewinne_colors import SIGEWINNEColorScheme
from .varesa_colors import VARESAColorScheme

all = [SIGEWINNEColorScheme, VARESAColorScheme]


def init_all() -> List:
    """
    初始化所有配色方案
    """

    return_list = []

    for color_scheme in all:
        return_list.append(color_scheme())

    return return_list
