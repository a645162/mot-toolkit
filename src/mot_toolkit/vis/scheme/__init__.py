from typing import List

from . import genshin, honor_of_kings

from .lingya_colors import LINGYAColorScheme
from .suzume_colors_blue import SuzumeBlueColorScheme
# from .suzume_colors_purple import SuzumePurpleColorScheme

all_package = [genshin, honor_of_kings]
# all_package = []

other_color = [
    LINGYAColorScheme,
    SuzumeBlueColorScheme,
    # SuzumePurpleColorScheme,
]


def init_all() -> List:
    """
    初始化所有配色方案
    """

    return_list = []

    for color_scheme in all_package:
        return_list.extend(color_scheme.init_all())

    for color_scheme in other_color:
        return_list.append(color_scheme())

    return return_list
