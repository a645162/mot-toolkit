from typing import List

from .angela_colors import AngelaColorScheme
from .yao_colors import YaoColorScheme

all = [YaoColorScheme]


def init_all() -> List:
    """
    初始化所有配色方案
    """

    return_list = []

    for color_scheme in all:
        return_list.append(color_scheme())

    return return_list
