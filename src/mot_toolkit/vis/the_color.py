import cv2
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from matplotlib.colors import rgb2hex, hex2color
from typing import List, Tuple, Union, Optional
import os


class TheColor:
    """
    TheColor类 - 从图像中提取主题色并生成配色方案

    类似于MATLAB中TheColor工具箱的功能，用于从图像提取颜色主题，
    并生成一套包含多种颜色的配色方案。
    """

    def __init__(self):
        """初始化TheColor类"""
        pass

    @staticmethod
    def load_image(image_path: str) -> np.ndarray:
        """
        加载图像并转换为RGB格式

        参数:
            image_path: 图像文件路径

        返回:
            RGB格式的图像数组
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"找不到图像文件: {image_path}")

        # 读取图像
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"无法加载图像: {image_path}")

        # 将BGR格式转换为RGB格式
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return image_rgb

    def extract_colors(
        self, image: np.ndarray, n_colors: int = 5
    ) -> List[Tuple[int, int, int]]:
        """
        从图像中提取主题色

        参数:
            image: RGB格式的图像数组
            n_colors: 要提取的颜色数量，默认为5

        返回:
            RGB格式的颜色列表
        """
        # 将图像重塑为二维数组，每行代表一个像素
        pixels = image.reshape(-1, 3)

        # 使用K-means聚类算法提取主题色
        kmeans = KMeans(n_clusters=n_colors, random_state=42)
        kmeans.fit(pixels)

        # 获取聚类中心（即主题色）
        colors = kmeans.cluster_centers_.astype(int)

        # 计算每个聚类的像素数量（颜色的权重）
        labels = kmeans.labels_
        counts = np.bincount(labels)

        # 按权重对颜色进行排序
        colors_with_counts = [(colors[i], counts[i]) for i in range(len(colors))]
        sorted_colors = [
            color
            for color, count in sorted(
                colors_with_counts, key=lambda x: x[1], reverse=True
            )
        ]

        # 将RGB值转换为元组
        return [tuple(color) for color in sorted_colors]

    def generate_color_scheme(
        self, base_colors: List[Tuple[int, int, int]], n_colors: int = 20
    ) -> List[Tuple[int, int, int]]:
        """
        基于提取的主题色生成扩展配色方案

        参数:
            base_colors: 基础颜色列表（RGB元组）
            n_colors: 要生成的总颜色数量，默认为20

        返回:
            扩展后的RGB颜色列表
        """
        if not base_colors:
            raise ValueError("基础颜色列表不能为空")

        # 如果基础颜色数量已经足够
        if len(base_colors) >= n_colors:
            return base_colors[:n_colors]

        # 需要额外生成的颜色数量
        n_extra = n_colors - len(base_colors)

        # 用于存储生成的所有颜色
        all_colors = base_colors.copy()

        # 通过改变饱和度和亮度生成更多变体颜色
        for color in base_colors:
            if len(all_colors) >= n_colors:
                break

            # 转换为HSV色彩空间便于调整
            r, g, b = color
            h, s, v = self._rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)

            # 生成不同饱和度的变体
            for sat_factor in [0.7, 0.5]:
                if len(all_colors) >= n_colors:
                    break
                new_s = min(1.0, s * sat_factor)
                new_r, new_g, new_b = self._hsv_to_rgb(h, new_s, v)
                new_color = (int(new_r * 255), int(new_g * 255), int(new_b * 255))
                if new_color not in all_colors:
                    all_colors.append(new_color)

            # 生成不同亮度的变体
            for val_factor in [1.2, 0.8]:
                if len(all_colors) >= n_colors:
                    break
                new_v = min(1.0, v * val_factor)
                new_r, new_g, new_b = self._hsv_to_rgb(h, s, new_v)
                new_color = (int(new_r * 255), int(new_g * 255), int(new_b * 255))
                if new_color not in all_colors:
                    all_colors.append(new_color)

        # 如果仍然颜色不够，通过混合现有颜色生成更多颜色
        while len(all_colors) < n_colors:
            idx1 = np.random.randint(0, len(base_colors))
            idx2 = np.random.randint(0, len(base_colors))
            if idx1 != idx2:
                r1, g1, b1 = base_colors[idx1]
                r2, g2, b2 = base_colors[idx2]
                mix_ratio = np.random.random() * 0.6 + 0.2  # 0.2 到 0.8 之间
                r = int(r1 * mix_ratio + r2 * (1 - mix_ratio))
                g = int(g1 * mix_ratio + g2 * (1 - mix_ratio))
                b = int(b1 * mix_ratio + b2 * (1 - mix_ratio))
                new_color = (r, g, b)
                if new_color not in all_colors:
                    all_colors.append(new_color)

        return all_colors

    def _rgb_to_hsv(self, r: float, g: float, b: float) -> Tuple[float, float, float]:
        """将RGB转换为HSV色彩空间"""
        mx = max(r, g, b)
        mn = min(r, g, b)
        df = mx - mn
        if mx == mn:
            h = 0
        elif mx == r:
            h = (60 * ((g - b) / df) + 360) % 360
        elif mx == g:
            h = (60 * ((b - r) / df) + 120) % 360
        elif mx == b:
            h = (60 * ((r - g) / df) + 240) % 360

        s = 0 if mx == 0 else df / mx
        v = mx
        return h / 360, s, v

    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[float, float, float]:
        """将HSV转换为RGB色彩空间"""
        h = h * 360
        if s == 0.0:
            return v, v, v

        i = int(h / 60) % 6
        f = (h / 60) - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))

        if i == 0:
            return v, t, p
        elif i == 1:
            return q, v, p
        elif i == 2:
            return p, v, t
        elif i == 3:
            return p, q, v
        elif i == 4:
            return t, p, v
        else:
            return v, p, q

    def visualize_colors(
        self,
        colors: List[Tuple[int, int, int]],
        title: str = "提取的颜色方案",
        show_image: Optional[np.ndarray] = None,
        figsize: Tuple[int, int] = (12, 8),
    ) -> None:
        """
        可视化颜色方案

        参数:
            colors: RGB颜色列表
            title: 图表标题
            show_image: 可选，要显示的原始图像
            figsize: 图表大小
        """
        n_colors = len(colors)

        # 创建一个新的图表
        if show_image is not None:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
            ax1.imshow(show_image)
            ax1.set_title("原始图像")
            ax1.axis("off")

            # 在右侧显示颜色条
            height = 20
            color_bar = np.zeros((height * n_colors, 100, 3), dtype=np.uint8)
            for i, color in enumerate(colors):
                color_bar[i * height : (i + 1) * height, :] = color

            ax2.imshow(color_bar)
            ax2.set_title("提取的颜色方案")
            ax2.axis("off")

            hex_colors = [rgb2hex([r / 255, g / 255, b / 255]) for r, g, b in colors]
            for i, hex_color in enumerate(hex_colors):
                y_pos = i * height + height // 2
                ax2.text(110, y_pos, hex_color, va="center", fontsize=8)

        else:
            fig, ax = plt.subplots(figsize=(10, 2))
            ax.set_title(title)

            # 创建颜色条
            for i, color in enumerate(colors):
                ax.add_patch(
                    plt.Rectangle((i, 0), 1, 1, color=[c / 255 for c in color])
                )

            # 设置图表属性
            ax.set_xlim(0, n_colors)
            ax.set_ylim(0, 1)
            ax.set_xticks([])
            ax.set_yticks([])

        plt.tight_layout()
        plt.show()

    def extract_and_visualize(
        self, image_path: str, n_colors: int = 5, total_colors: int = 20
    ) -> List[Tuple[int, int, int]]:
        """
        从图像中提取颜色并可视化结果

        参数:
            image_path: 图像文件路径
            n_colors: 要提取的主题色数量
            total_colors: 要生成的总颜色数量

        返回:
            生成的颜色方案（RGB颜色列表）
        """
        # 加载图像
        image = self.load_image(image_path)

        # 提取主题色
        base_colors = self.extract_colors(image, n_colors)

        # 生成配色方案
        color_scheme = self.generate_color_scheme(base_colors, total_colors)

        # 可视化结果
        self.visualize_colors(color_scheme, show_image=image)

        return color_scheme


# 示例使用代码
if __name__ == "__main__":
    color_extractor = TheColor()

    # 替换为你自己的图像路径
    image_path = "path/to/your/image.jpg"

    try:
        # 提取颜色并可视化
        colors = color_extractor.extract_and_visualize(
            image_path, n_colors=5, total_colors=20
        )

        print(f"成功提取了 {len(colors)} 种颜色!")
        # 打印颜色的RGB值和十六进制表示
        for i, (r, g, b) in enumerate(colors):
            hex_color = rgb2hex([r / 255, g / 255, b / 255])
            print(f"颜色 {i+1}: RGB=({r}, {g}, {b}), HEX={hex_color}")

    except Exception as e:
        print(f"发生错误: {str(e)}")
