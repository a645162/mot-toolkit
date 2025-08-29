import os
import cv2
import numpy as np
from typing import List, Optional
import logging
import glob
from mot_toolkit.vis.movies.draw_film_strip_effect import (
    FilmStripGenerator,
    FilmStripConfig,
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiImageFilmStripProcessor:
    """多图片胶片效果处理器"""

    def __init__(self, config: Optional[FilmStripConfig] = None):
        self.film_generator = FilmStripGenerator(config)

    def _extract_sort_key(self, filename: str) -> int:
        """
        从文件名中提取排序关键字

        Args:
            filename: 文件名

        Returns:
            排序用的整数
        """
        # 去掉扩展名
        base_name = os.path.splitext(filename)[0]

        # 检查是否存在下划线
        if "_" in base_name:
            # 取最后一个下划线后面的内容
            sort_part = base_name.split("_")[-1]
        else:
            sort_part = base_name

        # 尝试转换为整数
        try:
            return int(sort_part)
        except ValueError:
            logger.warning(f"无法将 '{sort_part}' 转换为整数，使用0作为默认值")
            return 0

    def _sort_image_files(self, image_paths: List[str]) -> List[str]:
        """
        根据文件名中的数字对图片文件进行排序

        Args:
            image_paths: 图片文件路径列表

        Returns:
            排序后的文件路径列表
        """

        def sort_key(path):
            filename = os.path.basename(path)
            return self._extract_sort_key(filename)

        sorted_paths = sorted(image_paths, key=sort_key)

        logger.info("文件排序结果:")
        for i, path in enumerate(sorted_paths):
            filename = os.path.basename(path)
            sort_num = self._extract_sort_key(filename)
            logger.info(f"  {i+1}: {filename} (排序键: {sort_num})")

        return sorted_paths

    def _load_and_resize_images(self, image_paths: List[str]) -> List[np.ndarray]:
        """
        加载图片并统一尺寸

        Args:
            image_paths: 图片文件路径列表

        Returns:
            图片数组列表
        """
        images = []
        target_height = None

        # 第一次遍历，确定目标高度
        for path in image_paths:
            img = cv2.imread(path)
            if img is None:
                logger.warning(f"无法读取图片: {path}")
                continue

            if target_height is None:
                target_height = img.shape[0]
            else:
                target_height = min(target_height, img.shape[0])

        if target_height is None:
            raise ValueError("没有有效的图片文件")

        logger.info(f"目标高度: {target_height}")

        # 第二次遍历，调整尺寸并加载
        for path in image_paths:
            img = cv2.imread(path)
            if img is None:
                continue

            # 按比例调整宽度
            height, width = img.shape[:2]
            target_width = int(width * target_height / height)

            # 调整尺寸
            resized_img = cv2.resize(img, (target_width, target_height))
            images.append(resized_img)

            logger.info(
                f"加载图片: {os.path.basename(path)} - {width}x{height} -> {target_width}x{target_height}"
            )

        return images

    def _concatenate_images_horizontally(self, images: List[np.ndarray]) -> np.ndarray:
        """
        水平拼接图片

        Args:
            images: 图片数组列表

        Returns:
            拼接后的图片数组
        """
        if not images:
            raise ValueError("图片列表为空")

        # 确保所有图片高度相同
        target_height = images[0].shape[0]
        for i, img in enumerate(images):
            if img.shape[0] != target_height:
                logger.warning(f"图片 {i} 高度不匹配，重新调整")
                width = int(img.shape[1] * target_height / img.shape[0])
                images[i] = cv2.resize(img, (width, target_height))

        # 水平拼接
        concatenated = np.hstack(images)
        total_width = sum(img.shape[1] for img in images)

        logger.info(f"拼接完成: {len(images)} 张图片 -> {total_width}x{target_height}")

        return concatenated

    def process_directory(
        self, input_dir: str, output_path: str, pattern: str = "*.jpg"
    ) -> Optional[str]:
        """
        处理目录中的所有图片，拼接并应用胶片效果

        Args:
            input_dir: 输入目录路径
            output_path: 输出文件路径
            pattern: 文件匹配模式

        Returns:
            输出文件路径，失败时返回None
        """
        try:
            # 查找所有图片文件
            search_pattern = os.path.join(input_dir, pattern)
            image_paths = glob.glob(search_pattern)

            if not image_paths:
                raise ValueError(
                    f"在目录 {input_dir} 中未找到匹配 {pattern} 的图片文件"
                )

            logger.info(f"找到 {len(image_paths)} 个图片文件")

            # 排序文件
            sorted_paths = self._sort_image_files(image_paths)

            # 加载并调整图片尺寸
            images = self._load_and_resize_images(sorted_paths)

            if not images:
                raise ValueError("没有成功加载任何图片")

            # 水平拼接图片
            concatenated_img = self._concatenate_images_horizontally(images)

            # 应用胶片效果
            logger.info("应用胶片效果...")
            film_strip_img = self.film_generator.apply_film_strip_effect(
                concatenated_img
            )

            # 创建输出目录
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 保存结果
            success = cv2.imwrite(output_path, film_strip_img)
            if not success:
                raise RuntimeError(f"保存图片失败: {output_path}")

            logger.info(f"多图片胶片效果已保存至: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"处理多图片胶片效果时发生错误: {str(e)}")
            return None

    def process_file_list(
        self, image_paths: List[str], output_path: str
    ) -> Optional[str]:
        """
        处理指定的图片文件列表

        Args:
            image_paths: 图片文件路径列表
            output_path: 输出文件路径

        Returns:
            输出文件路径，失败时返回None
        """
        try:
            if not image_paths:
                raise ValueError("图片文件列表为空")

            logger.info(f"处理 {len(image_paths)} 个图片文件")

            # 排序文件
            sorted_paths = self._sort_image_files(image_paths)

            # 加载并调整图片尺寸
            images = self._load_and_resize_images(sorted_paths)

            if not images:
                raise ValueError("没有成功加载任何图片")

            # 水平拼接图片
            concatenated_img = self._concatenate_images_horizontally(images)

            # 应用胶片效果
            logger.info("应用胶片效果...")
            film_strip_img = self.film_generator.apply_film_strip_effect(
                concatenated_img
            )

            # 创建输出目录
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 保存结果
            success = cv2.imwrite(output_path, film_strip_img)
            if not success:
                raise RuntimeError(f"保存图片失败: {output_path}")

            logger.info(f"多图片胶片效果已保存至: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"处理多图片胶片效果时发生错误: {str(e)}")
            return None


def create_multi_image_film_strip(
    image_paths: List[str],
    output_path: str,
    base_dir: Optional[str] = None,
    config: Optional[FilmStripConfig] = None,
) -> Optional[str]:
    """
    创建多图片胶片效果

    Args:
        image_paths: 图片路径列表
        output_path: 输出文件路径
        base_dir: 基础目录路径（可选），如果提供，会与image_paths中的路径进行拼接
        config: 胶片效果配置（可选）

    Returns:
        输出文件路径，失败时返回None
    """
    try:
        # 处理图片路径
        final_image_paths = []

        if base_dir:
            # 如果指定了基础目录，与图片路径进行拼接
            for path in image_paths:
                if os.path.isabs(path):
                    # 如果是绝对路径，直接使用
                    full_path = path
                else:
                    # 如果是相对路径，与基础目录拼接
                    full_path = os.path.join(base_dir, path)

                if os.path.exists(full_path):
                    final_image_paths.append(full_path)
                else:
                    logger.warning(f"图片文件不存在: {full_path}")
        else:
            # 没有基础目录，直接使用原路径
            for path in image_paths:
                if os.path.exists(path):
                    final_image_paths.append(path)
                else:
                    logger.warning(f"图片文件不存在: {path}")

        if not final_image_paths:
            raise ValueError("没有找到有效的图片文件")

        # 创建默认配置
        if config is None:
            config = FilmStripConfig(
                strip_ratio=15, hole_ratio=30, spacing_ratio=25, gradient_steps=5
            )

        logger.info(f"有效图片数量: {len(final_image_paths)}")
        for i, path in enumerate(final_image_paths, 1):
            logger.info(f"  {i}: {os.path.basename(path)}")
        logger.info(f"输出文件: {output_path}")
        logger.info(f"胶片效果配置: {config}")

        # 创建处理器并处理
        processor = MultiImageFilmStripProcessor(config)
        result_path = processor.process_file_list(
            image_paths=final_image_paths, output_path=output_path
        )

        if result_path:
            logger.info("多图片胶片效果制作完成！")
            logger.info(f"生成的文件: {result_path}")
        else:
            logger.error("多图片胶片效果制作失败！")

        return result_path

    except Exception as e:
        logger.error(f"创建多图片胶片效果时发生错误: {str(e)}")
        return None


def main() -> None:
    """主程序"""
    # 示例用法
    base_dir = r"D:\Prj\LiGroup\SCI\mot-toolkit\src\mot_toolkit\scripts\preview\dataset\output\first_frame"

    # 图片路径列表（可以是相对路径或绝对路径）
    image_paths = [
        "BV1B84y1D7Hg-kdDKogHERE0VwOKy_00000000-00000816.jpg",
        "BV1B3411Q7wV-F5KqBqN5h8jjoV3e_00000000-00000318.jpg",
        # 在这里添加更多图片路径...
    ]

    # 输出文件路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(current_dir, "output", "movies")
    output_path = os.path.join(output_dir, "multi_image_film_strip.jpg")

    # 调用新函数
    result = create_multi_image_film_strip(
        image_paths=image_paths, output_path=output_path, base_dir=base_dir
    )

    if result:
        print(f"成功生成胶片效果图片: {result}")
    else:
        print("生成胶片效果图片失败")


if __name__ == "__main__":
    main()
