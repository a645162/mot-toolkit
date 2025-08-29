import os
import cv2
import numpy as np
from PIL import Image, ImageDraw
from typing import List, Tuple, Optional
from dataclasses import dataclass
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FilmStripConfig:
    """胶片效果配置参数"""

    strip_ratio: int = 15  # 胶片边框宽度比例
    hole_ratio: int = 30  # 胶片孔洞大小比例
    spacing_ratio: int = 25  # 孔洞间距比例
    gradient_steps: int = 5  # 边缘渐变步数
    hole_color: Tuple[int, int, int] = (255, 255, 255)  # 孔洞颜色
    min_strip_width: int = 40  # 最小胶片边框宽度
    min_hole_size: int = 15  # 最小孔洞大小
    min_hole_spacing: int = 20  # 最小孔洞间距

    def validate(self) -> None:
        """验证配置参数"""
        if self.strip_ratio <= 0 or self.hole_ratio <= 0 or self.spacing_ratio <= 0:
            raise ValueError("比例参数必须为正数")
        if self.gradient_steps < 0:
            raise ValueError("渐变步数不能为负数")


class FilmStripGenerator:
    """电影胶片效果生成器"""

    def __init__(self, config: Optional[FilmStripConfig] = None):
        self.config = config or FilmStripConfig()
        self.config.validate()

    def _draw_holes(
        self, draw: ImageDraw.Draw, positions: List[Tuple[int, int]], hole_size: int
    ) -> None:
        """绘制胶片孔洞"""
        for center_x, center_y in positions:
            draw.rectangle(
                [
                    center_x - hole_size // 2,
                    center_y - hole_size // 2,
                    center_x + hole_size // 2,
                    center_y + hole_size // 2,
                ],
                fill=self.config.hole_color,
            )

    def _draw_edge_gradient(
        self, draw: ImageDraw.Draw, lines: List[List[List[Tuple[int, int]]]]
    ) -> None:
        """绘制边缘渐变效果"""
        for i in range(self.config.gradient_steps):
            color = (i * 10, i * 10, i * 10)
            for start_pos, end_pos in lines[i]:
                draw.line([start_pos, end_pos], fill=color)

    def _get_hole_positions(
        self, start: int, end: int, spacing: int, hole_size: int
    ) -> List[int]:
        """计算孔洞位置"""
        positions = []
        current = start + spacing

        while current + hole_size < end:
            positions.append(current)
            current += spacing + hole_size

        return positions

    def _calculate_dimensions(
        self, width: int, height: int, is_landscape: bool
    ) -> Tuple[int, int, int]:
        """计算胶片效果的尺寸参数"""
        base_dimension = height if is_landscape else width

        strip_width = max(
            self.config.min_strip_width, base_dimension // self.config.strip_ratio
        )
        hole_size = max(
            self.config.min_hole_size, base_dimension // self.config.hole_ratio
        )
        hole_spacing = max(
            self.config.min_hole_spacing, base_dimension // self.config.spacing_ratio
        )

        return strip_width, hole_size, hole_spacing

    def _process_landscape_image(self, img: np.ndarray) -> np.ndarray:
        """处理横屏图像"""
        height, width = img.shape[:2]
        strip_width, hole_size, hole_spacing = self._calculate_dimensions(
            width, height, True
        )

        # 创建新画布
        new_width = width
        new_height = height + 2 * strip_width
        film_strip = np.zeros((new_height, new_width, 3), dtype=np.uint8)
        film_strip[strip_width : strip_width + height, :] = img

        # 转换为PIL并绘制
        pil_img = Image.fromarray(cv2.cvtColor(film_strip, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img)

        # 绘制孔洞
        hole_x_positions = self._get_hole_positions(
            0, new_width, hole_spacing, hole_size
        )

        # 上方孔洞
        top_holes = [(x, strip_width // 2) for x in hole_x_positions]
        self._draw_holes(draw, top_holes, hole_size)

        # 下方孔洞
        bottom_holes = [(x, new_height - strip_width // 2) for x in hole_x_positions]
        self._draw_holes(draw, bottom_holes, hole_size)

        # 边缘渐变
        edge_lines = self._create_horizontal_gradient_lines(
            new_width, new_height, strip_width
        )
        self._draw_edge_gradient(draw, edge_lines)

        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    def _process_portrait_image(self, img: np.ndarray) -> np.ndarray:
        """处理竖屏图像"""
        height, width = img.shape[:2]
        strip_width, hole_size, hole_spacing = self._calculate_dimensions(
            width, height, False
        )

        # 创建新画布
        new_width = width + 2 * strip_width
        new_height = height
        film_strip = np.zeros((new_height, new_width, 3), dtype=np.uint8)
        film_strip[:, strip_width : strip_width + width] = img

        # 转换为PIL并绘制
        pil_img = Image.fromarray(cv2.cvtColor(film_strip, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img)

        # 绘制孔洞
        hole_y_positions = self._get_hole_positions(
            0, new_height, hole_spacing, hole_size
        )

        # 左侧孔洞
        left_holes = [(strip_width // 2, y) for y in hole_y_positions]
        self._draw_holes(draw, left_holes, hole_size)

        # 右侧孔洞
        right_holes = [(new_width - strip_width // 2, y) for y in hole_y_positions]
        self._draw_holes(draw, right_holes, hole_size)

        # 边缘渐变
        edge_lines = self._create_vertical_gradient_lines(
            new_width, new_height, strip_width
        )
        self._draw_edge_gradient(draw, edge_lines)

        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    def _create_horizontal_gradient_lines(
        self, width: int, height: int, strip_width: int
    ) -> List[List[List[Tuple[int, int]]]]:
        """创建水平方向的渐变线条"""
        edge_lines = []
        for i in range(self.config.gradient_steps):
            lines_for_step = [
                [(0, i), (width, i)],
                [(0, strip_width - 1 - i), (width, strip_width - 1 - i)],
                [(0, height - 1 - i), (width, height - 1 - i)],
                [(0, height - strip_width + i), (width, height - strip_width + i)],
            ]
            edge_lines.append(lines_for_step)
        return edge_lines

    def _create_vertical_gradient_lines(
        self, width: int, height: int, strip_width: int
    ) -> List[List[List[Tuple[int, int]]]]:
        """创建垂直方向的渐变线条"""
        edge_lines = []
        for i in range(self.config.gradient_steps):
            lines_for_step = [
                [(i, 0), (i, height)],
                [(strip_width - 1 - i, 0), (strip_width - 1 - i, height)],
                [(width - 1 - i, 0), (width - 1 - i, height)],
                [(width - strip_width + i, 0), (width - strip_width + i, height)],
            ]
            edge_lines.append(lines_for_step)
        return edge_lines

    def apply_film_strip_effect(self, img: np.ndarray) -> np.ndarray:
        """
        为图片数组添加电影胶片效果

        Args:
            img: 输入图片数组

        Returns:
            处理后的图片数组
        """
        try:
            height, width = img.shape[:2]
            logger.info(f"处理图片，尺寸: {width}x{height}")

            # 判断图像方向并处理
            is_landscape = width > height
            if is_landscape:
                result = self._process_landscape_image(img)
            else:
                result = self._process_portrait_image(img)

            return result

        except Exception as e:
            logger.error(f"应用胶片效果时发生错误: {str(e)}")
            raise

    def create_film_strip_effect(
        self, image_path: str, output_dir: str
    ) -> Optional[str]:
        """
        为图片添加电影胶片效果并保存

        Args:
            image_path: 输入图片路径
            output_dir: 输出目录

        Returns:
            输出文件路径，失败时返回None
        """
        try:
            # 验证输入
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"输入文件不存在: {image_path}")

            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)

            # 读取图片
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"无法读取图片: {image_path}")

            # 应用胶片效果
            result = self.apply_film_strip_effect(img)

            # 生成输出文件名
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            output_path = os.path.join(output_dir, f"{base_name}_film_strip.jpg")

            # 保存结果
            success = cv2.imwrite(output_path, result)
            if not success:
                raise RuntimeError(f"保存图片失败: {output_path}")

            logger.info(f"电影胶片效果已保存至: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"创建胶片效果时发生错误: {str(e)}")
            return None


def main() -> None:
    """主程序"""
    # 输入图片路径
    image_path = r"D:\Prj\LiGroup\SCI\mot-toolkit\src\mot_toolkit\scripts\preview\dataset\output\first_frame\BV1BG411973R-TvfoYYtoODz4LeHz_00000000-00000488.jpg"

    # 输出目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(current_dir, "output", "movies")

    # 创建配置
    config = FilmStripConfig(
        strip_ratio=15, hole_ratio=30, spacing_ratio=25, gradient_steps=5
    )

    logger.info(f"处理图片: {image_path}")
    logger.info(f"输出目录: {output_dir}")
    logger.info(f"胶片效果配置: {config}")

    # 创建生成器并处理
    generator = FilmStripGenerator(config)
    result_path = generator.create_film_strip_effect(image_path, output_dir)

    if result_path:
        logger.info("电影胶片效果制作完成！")
        logger.info(f"生成的文件: {result_path}")
    else:
        logger.error("电影胶片效果制作失败！")


if __name__ == "__main__":
    main()
