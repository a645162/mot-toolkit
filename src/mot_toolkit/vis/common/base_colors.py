"""颜色方案基础模块
定义颜色方案的基类和基本工具函数
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional
import random
import colorsys


class BaseColorScheme(ABC):
    """颜色方案基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """方案名称"""
        pass

    @property
    @abstractmethod
    def colors(self) -> List[Tuple[int, int, int]]:
        """RGB颜色列表"""
        pass

    def hex_colors(self) -> List[str]:
        """转换为HEX颜色码"""
        return [rgb_to_hex(r, g, b) for r, g, b in self.colors]

    @abstractmethod
    def get_color_map(self, style: str = "matplotlib") -> Dict[str, Any]:
        """生成颜色映射"""
        pass

    @staticmethod
    def _calculate_color_brightness(hex_color: str) -> float:
        """计算颜色的亮度值 (0-255)

        参数:
            hex_color: HEX颜色值，如 "#FF0000"

        返回:
            亮度值，使用感知亮度公式：0.299*R + 0.587*G + 0.114*B
        """
        # 移除 # 符号并转换为 RGB
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:
            raise ValueError(f"无效的HEX颜色格式: {hex_color}")

        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # 使用感知亮度公式
        brightness = 0.299 * r + 0.587 * g + 0.114 * b
        return brightness

    @staticmethod
    def get_smart_colors_from_schemes(
        count: int,
        color_schemes: List["BaseColorScheme"],
        seed: Optional[int] = None,
        prefer_dark: Optional[bool] = None,
    ) -> List[str]:
        """从多个配色方案中智能取色

        参数:
            count: 需要的颜色数量
            color_schemes: 配色方案列表
            seed: 随机种子，用于可重复的随机结果
            prefer_dark: 颜色偏好设置
                - True: 偏好深色
                - False: 偏好浅色
                - None: 无偏好（默认）

        返回:
            HEX颜色列表，按以下逻辑：
            - 如果颜色多了：根据偏好排序后选择前n个，同时保持多样性
            - 如果颜色少了：使用所有颜色，然后根据偏好补充不够的颜色
            - 如果颜色个数正好相同：用所有的颜色
        """
        if seed is not None:
            random.seed(seed)

        # 合并所有颜色方案的颜色
        all_colors = []
        for scheme in color_schemes:
            all_colors.extend(scheme.hex_colors())

        if not all_colors:
            raise ValueError("没有可用的颜色")

        total_colors = len(all_colors)

        if count == total_colors:
            # 颜色个数正好相同，用所有的颜色
            print(f"🎨 颜色数量正好匹配 ({total_colors} 种)，使用所有颜色")
            return all_colors
        elif count < total_colors:
            # 颜色多了，根据偏好智能选择
            if prefer_dark is not None:
                # 计算每个颜色的亮度
                color_brightness = []
                for color in all_colors:
                    brightness = BaseColorScheme._calculate_color_brightness(color)
                    color_brightness.append((color, brightness))

                # 根据偏好排序
                if prefer_dark:
                    # 偏好深色：按亮度从低到高排序
                    color_brightness.sort(key=lambda x: x[1])
                    preference_msg = "偏好深色"
                else:
                    # 偏好浅色：按亮度从高到低排序
                    color_brightness.sort(key=lambda x: x[1], reverse=True)
                    preference_msg = "偏好浅色"

                # 为了保持颜色多样性，我们不是简单地取前N个
                # 而是分层采样：优先选择偏好的颜色，但也包含一些对比色
                preferred_count = max(1, int(count * 0.7))  # 70%使用偏好颜色
                diverse_count = count - preferred_count  # 30%保持多样性

                selected_colors = []

                # 选择偏好的颜色
                for i in range(min(preferred_count, len(color_brightness))):
                    selected_colors.append(color_brightness[i][0])

                # 从剩余颜色中随机选择以保持多样性
                if diverse_count > 0:
                    remaining_colors = [
                        color for color, _ in color_brightness[preferred_count:]
                    ]
                    if remaining_colors:
                        diverse_colors = random.sample(
                            remaining_colors, min(diverse_count, len(remaining_colors))
                        )
                        selected_colors.extend(diverse_colors)

                # 如果还不够，从所有颜色中随机补充
                while len(selected_colors) < count:
                    selected_colors.append(random.choice(all_colors))

                print(
                    f"🎨 从 {total_colors} 种颜色中{preference_msg}选择 {count} 种 (70%偏好色+30%多样性)"
                )
                return selected_colors[:count]
            else:
                # 无偏好，随机取出n个
                selected_colors = random.sample(all_colors, count)
                print(f"🎨 从 {total_colors} 种颜色中随机选择 {count} 种")
                return selected_colors
        else:
            # 颜色少了，使用所有颜色，然后根据偏好补充不够的颜色
            selected_colors = list(all_colors)  # 先使用所有颜色
            needed = count - total_colors

            if prefer_dark is not None and needed > 0:
                # 根据偏好选择补充颜色
                color_brightness = []
                for color in all_colors:
                    brightness = BaseColorScheme._calculate_color_brightness(color)
                    color_brightness.append((color, brightness))

                if prefer_dark:
                    # 偏好深色：优先选择深色进行重复
                    color_brightness.sort(key=lambda x: x[1])
                    preference_msg = "偏好深色"
                else:
                    # 偏好浅色：优先选择浅色进行重复
                    color_brightness.sort(key=lambda x: x[1], reverse=True)
                    preference_msg = "偏好浅色"

                # 按偏好顺序补充颜色
                for i in range(needed):
                    preferred_color = color_brightness[i % len(color_brightness)][0]
                    selected_colors.append(preferred_color)

                print(
                    f"🎨 使用所有 {total_colors} 种颜色，{preference_msg}补充 {needed} 种"
                )
            else:
                # 无偏好，随机补充
                for _ in range(needed):
                    selected_colors.append(random.choice(all_colors))
                print(f"🎨 使用所有 {total_colors} 种颜色，随机补充 {needed} 种")

            return selected_colors

            print(
                f"🎨 使用所有 {total_colors} 种颜色，随机补充 {needed} 种，总共 {count} 种"
            )
            return selected_colors

    @staticmethod
    def create_merged_scheme(
        *schemes: "BaseColorScheme", name: Optional[str] = None
    ) -> "MergedColorScheme":
        """创建合并的配色方案对象

        参数:
            *schemes: 可变数量的颜色方案实例
            name: 合并后的配色方案名称，如果不提供会自动生成

        返回:
            合并后的配色方案对象
        """
        if not schemes:
            raise ValueError("至少需要提供一个配色方案")

        # 合并所有颜色
        merged_colors = []
        for scheme in schemes:
            merged_colors.extend(scheme.colors)

        # 生成名称
        if name is None:
            scheme_names = [scheme.name for scheme in schemes]
            name = "Merged_" + "_".join(scheme_names)

        return MergedColorScheme(
            source_schemes=list(schemes), merged_colors=merged_colors, name=name
        )

    def bgr_colors(self) -> List[Tuple[int, int, int]]:
        """返回BGR格式的颜色列表"""
        bgr_list = []
        for r, g, b in self.colors:
            # 将RGB转换为BGR
            bgr_list.append((b, g, r))
        return bgr_list

    def expand_colors(
        self, multiplier: int = 3, method: str = "auto"
    ) -> List[Tuple[int, int, int]]:
        """扩展颜色数量

        参数:
            multiplier: 颜色倍数，默认3倍
            method: 扩展方法，可选 'hue_shift', 'brightness', 'saturation', 'auto'

        返回:
            扩展后的RGB颜色列表
        """
        if multiplier <= 1:
            return self.colors

        expanded_colors = list(self.colors)  # 保留原始颜色
        original_count = len(self.colors)
        target_count = original_count * multiplier

        # 根据方法生成新颜色
        if method == "auto":
            # 自动模式：混合多种方法
            methods = ["hue_shift", "brightness", "saturation"]
            colors_per_method = (target_count - original_count) // len(methods)

            for i, m in enumerate(methods):
                if i == len(methods) - 1:  # 最后一个方法处理剩余颜色
                    remaining = target_count - len(expanded_colors)
                    expanded_colors.extend(
                        self._generate_colors_by_method(m, remaining)
                    )
                else:
                    expanded_colors.extend(
                        self._generate_colors_by_method(m, colors_per_method)
                    )
        else:
            needed_colors = target_count - original_count
            expanded_colors.extend(
                self._generate_colors_by_method(method, needed_colors)
            )

        return expanded_colors[:target_count]

    def _generate_colors_by_method(
        self, method: str, count: int
    ) -> List[Tuple[int, int, int]]:
        """根据指定方法生成颜色"""
        if count <= 0:
            return []

        new_colors = []
        base_colors = self.colors

        for i in range(count):
            # 选择基础颜色
            base_idx = i % len(base_colors)
            r, g, b = base_colors[base_idx]

            # 转换为HSV进行调整
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)

            if method == "hue_shift":
                # 色相偏移
                shift = (i + 1) * 0.15  # 每次偏移15%
                h = (h + shift) % 1.0
            elif method == "brightness":
                # 亮度调整
                factor = 0.7 + (i % 3) * 0.15  # 0.7, 0.85, 1.0的循环
                v = min(1.0, v * factor)
            elif method == "saturation":
                # 饱和度调整
                factor = 0.6 + (i % 4) * 0.13  # 0.6, 0.73, 0.86, 0.99的循环
                s = min(1.0, s * factor)

            # 转换回RGB
            new_r, new_g, new_b = colorsys.hsv_to_rgb(h, s, v)
            new_colors.append((int(new_r * 255), int(new_g * 255), int(new_b * 255)))

        return new_colors

    def get_random_colors(
        self, count: int, expand_if_needed: bool = True, seed: Optional[int] = None
    ) -> List[Tuple[int, int, int]]:
        """随机获取指定数量的颜色

        参数:
            count: 需要的颜色数量
            expand_if_needed: 如果颜色不够是否自动扩展
            seed: 随机种子，用于可重复的随机结果

        返回:
            随机选择的RGB颜色列表
        """
        if seed is not None:
            random.seed(seed)

        available_colors = self.colors

        # 如果需要的颜色数量超过可用颜色，且允许扩展
        if count > len(available_colors) and expand_if_needed:
            # 计算需要扩展的倍数
            multiplier = (count // len(available_colors)) + 2
            available_colors = self.expand_colors(multiplier=multiplier)

        # 随机选择颜色
        if count >= len(available_colors):
            # 如果需要的数量大于等于可用数量，返回所有颜色
            return available_colors[:count]
        else:
            # 随机选择
            return random.sample(available_colors, count)

    def get_random_hex_colors(
        self, count: int, expand_if_needed: bool = True, seed: Optional[int] = None
    ) -> List[str]:
        """随机获取指定数量的HEX颜色

        参数:
            count: 需要的颜色数量
            expand_if_needed: 如果颜色不够是否自动扩展
            seed: 随机种子，用于可重复的随机结果

        返回:
            随机选择的HEX颜色列表
        """
        rgb_colors = self.get_random_colors(count, expand_if_needed, seed)
        return [rgb_to_hex(r, g, b) for r, g, b in rgb_colors]

    def expand_hex_colors(self, multiplier: int = 3, method: str = "auto") -> List[str]:
        """扩展颜色数量并返回HEX格式

        参数:
            multiplier: 颜色倍数，默认3倍
            method: 扩展方法

        返回:
            扩展后的HEX颜色列表
        """
        expanded_rgb = self.expand_colors(multiplier, method)
        return [rgb_to_hex(r, g, b) for r, g, b in expanded_rgb]

    def get_dark_colors(
        self, threshold: float = 0.5, expand_if_needed: bool = True
    ) -> List[Tuple[int, int, int]]:
        """获取深色颜色

        参数:
            threshold: 明度阈值，小于此值被认为是深色 (0-1范围)
            expand_if_needed: 如果深色颜色不够是否扩展颜色池

        返回:
            深色RGB颜色列表
        """
        # 获取可用颜色
        available_colors = self.colors
        if expand_if_needed:
            # 扩展颜色以获得更多选择
            available_colors = self.expand_colors(multiplier=3)

        dark_colors = []
        for r, g, b in available_colors:
            # 计算颜色的亮度 (使用HSV中的V值)
            _, _, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            if v <= threshold:
                dark_colors.append((r, g, b))

        # 如果没有找到足够的深色，降低阈值或通过调暗现有颜色来生成
        if not dark_colors and expand_if_needed:
            dark_colors = self._generate_dark_colors(available_colors)

        return dark_colors

    def get_light_colors(
        self, threshold: float = 0.5, expand_if_needed: bool = True
    ) -> List[Tuple[int, int, int]]:
        """获取浅色颜色

        参数:
            threshold: 明度阈值，大于此值被认为是浅色 (0-1范围)
            expand_if_needed: 如果浅色颜色不够是否扩展颜色池

        返回:
            浅色RGB颜色列表
        """
        # 获取可用颜色
        available_colors = self.colors
        if expand_if_needed:
            # 扩展颜色以获得更多选择
            available_colors = self.expand_colors(multiplier=3)

        light_colors = []
        for r, g, b in available_colors:
            # 计算颜色的亮度 (使用HSV中的V值)
            _, _, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            if v >= threshold:
                light_colors.append((r, g, b))

        # 如果没有找到足够的浅色，通过调亮现有颜色来生成
        if not light_colors and expand_if_needed:
            light_colors = self._generate_light_colors(available_colors)

        return light_colors

    def get_dark_hex_colors(
        self, threshold: float = 0.5, expand_if_needed: bool = True
    ) -> List[str]:
        """获取深色颜色的HEX格式

        参数:
            threshold: 明度阈值，小于此值被认为是深色 (0-1范围)
            expand_if_needed: 如果深色颜色不够是否扩展颜色池

        返回:
            深色HEX颜色列表
        """
        dark_rgb = self.get_dark_colors(threshold, expand_if_needed)
        return [rgb_to_hex(r, g, b) for r, g, b in dark_rgb]

    def get_light_hex_colors(
        self, threshold: float = 0.5, expand_if_needed: bool = True
    ) -> List[str]:
        """获取浅色颜色的HEX格式

        参数:
            threshold: 明度阈值，大于此值被认为是浅色 (0-1范围)
            expand_if_needed: 如果浅色颜色不够是否扩展颜色池

        返回:
            浅色HEX颜色列表
        """
        light_rgb = self.get_light_colors(threshold, expand_if_needed)
        return [rgb_to_hex(r, g, b) for r, g, b in light_rgb]

    def _generate_dark_colors(
        self, base_colors: List[Tuple[int, int, int]]
    ) -> List[Tuple[int, int, int]]:
        """通过调暗基础颜色生成深色颜色"""
        dark_colors = []
        for r, g, b in base_colors:
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)

            # 降低亮度，保持色相和饱和度
            dark_v = min(0.4, v * 0.6)  # 将亮度降低到0.4以下

            new_r, new_g, new_b = colorsys.hsv_to_rgb(h, s, dark_v)
            dark_colors.append((int(new_r * 255), int(new_g * 255), int(new_b * 255)))
        return dark_colors

    def _generate_light_colors(
        self, base_colors: List[Tuple[int, int, int]]
    ) -> List[Tuple[int, int, int]]:
        """通过调亮基础颜色生成浅色颜色"""
        light_colors = []
        for r, g, b in base_colors:
            h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)

            # 提高亮度，适当降低饱和度以获得更柔和的浅色
            light_v = max(0.7, min(1.0, v * 1.4))  # 将亮度提高到0.7以上
            light_s = s * 0.7  # 降低饱和度使颜色更柔和

            new_r, new_g, new_b = colorsys.hsv_to_rgb(h, light_s, light_v)
            light_colors.append((int(new_r * 255), int(new_g * 255), int(new_b * 255)))
        return light_colors

    def get_colors_by_brightness(
        self, brightness_range: Tuple[float, float] = (0.3, 0.7)
    ) -> List[Tuple[int, int, int]]:
        """根据亮度范围获取颜色

        参数:
            brightness_range: 亮度范围元组 (最小值, 最大值)，范围0-1

        返回:
            符合亮度范围的RGB颜色列表
        """
        min_brightness, max_brightness = brightness_range
        available_colors = self.expand_colors(multiplier=3)

        filtered_colors = []
        for r, g, b in available_colors:
            _, _, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            if min_brightness <= v <= max_brightness:
                filtered_colors.append((r, g, b))

        return filtered_colors

    def get_colors_by_saturation(
        self, saturation_range: Tuple[float, float] = (0.4, 0.8)
    ) -> List[Tuple[int, int, int]]:
        """根据饱和度范围获取颜色

        参数:
            saturation_range: 饱和度范围元组 (最小值, 最大值)，范围0-1

        返回:
            符合饱和度范围的RGB颜色列表
        """
        min_saturation, max_saturation = saturation_range
        available_colors = self.expand_colors(multiplier=3)

        filtered_colors = []
        for r, g, b in available_colors:
            _, s, _ = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            if min_saturation <= s <= max_saturation:
                filtered_colors.append((r, g, b))

        return filtered_colors

    def create_extended_scheme(
        self, multiplier: int = 3, method: str = "auto"
    ) -> "ExtendedColorScheme":
        """创建扩展配色方案

        参数:
            multiplier: 颜色倍数，默认3倍
            method: 扩展方法，可选 'hue_shift', 'brightness', 'saturation', 'auto'

        返回:
            扩展配色方案实例
        """
        extended_colors = self.expand_colors(multiplier, method)
        return ExtendedColorScheme(
            original_scheme=self,
            extended_colors=extended_colors,
            extension_method=method,
            multiplier=multiplier,
        )

    def create_dark_extended_scheme(
        self, multiplier: int = 3, threshold: float = 0.5
    ) -> "ExtendedColorScheme":
        """创建深色扩展配色方案

        参数:
            multiplier: 颜色倍数，默认3倍
            threshold: 深色阈值，默认0.5

        返回:
            深色扩展配色方案实例
        """
        # 先扩展颜色，再筛选深色
        expanded_colors = self.expand_colors(multiplier, "auto")

        # 筛选深色颜色
        dark_colors = []
        for r, g, b in expanded_colors:
            _, _, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            if v <= threshold:
                dark_colors.append((r, g, b))

        # 如果深色颜色不够，通过调暗现有颜色生成
        if len(dark_colors) < len(self.colors):
            additional_dark = self._generate_dark_colors(expanded_colors)
            dark_colors.extend(additional_dark)
            # 去重并限制数量
            dark_colors = list(dict.fromkeys(dark_colors))[
                : multiplier * len(self.colors)
            ]

        return ExtendedColorScheme(
            original_scheme=self,
            extended_colors=dark_colors,
            extension_method=f"dark_threshold_{threshold}",
            multiplier=multiplier,
        )

    def create_light_extended_scheme(
        self, multiplier: int = 3, threshold: float = 0.5
    ) -> "ExtendedColorScheme":
        """创建浅色扩展配色方案

        参数:
            multiplier: 颜色倍数，默认3倍
            threshold: 浅色阈值，默认0.5

        返回:
            浅色扩展配色方案实例
        """
        # 先扩展颜色，再筛选浅色
        expanded_colors = self.expand_colors(multiplier, "auto")

        # 筛选浅色颜色
        light_colors = []
        for r, g, b in expanded_colors:
            _, _, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            if v >= threshold:
                light_colors.append((r, g, b))

        # 如果浅色颜色不够，通过调亮现有颜色生成
        if len(light_colors) < len(self.colors):
            additional_light = self._generate_light_colors(expanded_colors)
            light_colors.extend(additional_light)
            # 去重并限制数量
            light_colors = list(dict.fromkeys(light_colors))[
                : multiplier * len(self.colors)
            ]

        return ExtendedColorScheme(
            original_scheme=self,
            extended_colors=light_colors,
            extension_method=f"light_threshold_{threshold}",
            multiplier=multiplier,
        )

    def create_random_extended_scheme(
        self, count: int, seed: Optional[int] = None
    ) -> "ExtendedColorScheme":
        """创建随机扩展配色方案

        参数:
            count: 需要的颜色数量
            seed: 随机种子

        返回:
            随机扩展配色方案实例
        """
        if seed is not None:
            random.seed(seed)

        # 计算需要的倍数
        multiplier = max(2, (count // len(self.colors)) + 1)
        expanded_colors = self.expand_colors(multiplier, "auto")

        # 随机选择指定数量的颜色
        if count >= len(expanded_colors):
            selected_colors = expanded_colors
        else:
            selected_colors = random.sample(expanded_colors, count)

        return ExtendedColorScheme(
            original_scheme=self,
            extended_colors=selected_colors,
            extension_method=f"random_seed_{seed}" if seed else "random",
            multiplier=multiplier,
        )


class ExtendedColorScheme(BaseColorScheme):
    """扩展的配色方案类

    基于原始配色方案生成扩展后的新配色方案实例
    """

    def __init__(
        self,
        original_scheme: "BaseColorScheme",
        extended_colors: List[Tuple[int, int, int]],
        extension_method: str = "auto",
        multiplier: int = 3,
    ):
        """初始化扩展配色方案

        参数:
            original_scheme: 原始配色方案
            extended_colors: 扩展后的颜色列表
            extension_method: 扩展方法
            multiplier: 扩展倍数
        """
        self._original_scheme = original_scheme
        self._extended_colors = extended_colors
        self._extension_method = extension_method
        self._multiplier = multiplier

        # 生成扩展后的方案名称
        self._name = f"{original_scheme.name}_Extended_{extension_method}_{multiplier}x"

    @property
    def name(self) -> str:
        """扩展配色方案名称"""
        return self._name

    @property
    def colors(self) -> List[Tuple[int, int, int]]:
        """扩展后的RGB颜色列表"""
        return self._extended_colors

    @property
    def original_scheme(self) -> "BaseColorScheme":
        """原始配色方案"""
        return self._original_scheme

    @property
    def extension_method(self) -> str:
        """扩展方法"""
        return self._extension_method

    @property
    def multiplier(self) -> int:
        """扩展倍数"""
        return self._multiplier

    def get_color_map(self, style: str = "matplotlib") -> Dict[str, Any]:
        """生成扩展配色方案的颜色映射"""
        if style == "matplotlib":
            return {
                "colors": self.hex_colors(),
                "name": self.name,
                "type": "extended",
                "original": self._original_scheme.name,
                "method": self._extension_method,
                "multiplier": self._multiplier,
            }
        else:
            # 可以根据需要添加其他样式
            return self._original_scheme.get_color_map(style)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """RGB颜色转HEX颜色码

    参数:
        r: 红色分量 (0-255)
        g: 绿色分量 (0-255)
        b: 蓝色分量 (0-255)

    返回:
        HEX格式的颜色码，如 "#5184B2"
    """
    return f"#{r:02x}{g:02x}{b:02x}".upper()


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """HEX颜色码转RGB颜色

    参数:
        hex_color: HEX颜色码，如 "#5184B2"

    返回:
        RGB元组，如 (81, 132, 178)
    """
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


class MergedColorScheme(BaseColorScheme):
    """合并的配色方案类

    将多个配色方案合并为一个新的配色方案实例
    """

    def __init__(
        self,
        source_schemes: List[BaseColorScheme],
        merged_colors: List[Tuple[int, int, int]],
        name: str,
    ):
        """初始化合并配色方案

        参数:
            source_schemes: 源配色方案列表
            merged_colors: 合并后的颜色列表
            name: 合并后的方案名称
        """
        self._source_schemes = source_schemes
        self._merged_colors = merged_colors
        self._name = name

    @property
    def name(self) -> str:
        """合并配色方案名称"""
        return self._name

    @property
    def colors(self) -> List[Tuple[int, int, int]]:
        """合并后的RGB颜色列表"""
        return self._merged_colors

    @property
    def source_schemes(self) -> List[BaseColorScheme]:
        """源配色方案列表"""
        return self._source_schemes

    def get_color_map(self, style: str = "matplotlib") -> Dict[str, Any]:
        """生成合并配色方案的颜色映射"""
        if style == "matplotlib":
            return {
                "colors": self.hex_colors(),
                "name": self.name,
                "type": "merged",
                "source_schemes": [scheme.name for scheme in self._source_schemes],
                "total_colors": len(self._merged_colors),
            }
        else:
            # 可以根据需要添加其他样式
            return {"colors": self.colors, "name": self.name, "type": "merged"}
