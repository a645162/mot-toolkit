import os
import argparse
import multiprocessing
from typing import List, Tuple, Dict, Any, Optional
import cv2
import numpy as np
import shutil

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list
from mot_toolkit.datatype.xanylabeling import (
    XAnyLabelingAnnotationDirectory,
    XAnyLabelingAnnotation,
)
from mot_toolkit.config.hardware import io_cpu_count
from mot_toolkit.utils.logs import get_logger

logger = get_logger()


def parse_args() -> argparse.Namespace:
    """
    解析命令行参数。
    
    返回:
        argparse.Namespace: 解析后的参数对象。
    """
    parser = argparse.ArgumentParser(description="将边界框绘制到图片上并保存")
    parser.add_argument(
        "--dataset_dir", 
        type=str, 
        default="./dataset",
        help="数据集根目录路径"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        help="输出目录路径，将保持与源目录相同的结构。默认为 <数据集目录名>_output"
    )
    parser.add_argument(
        "--num_workers",
        type=int,
        default=None,
        help="处理的工作进程数，默认为系统CPU核心数"
    )
    parser.add_argument(
        "--thickness", 
        type=int, 
        default=2, 
        help="边界框线条粗细，默认为2"
    )
    parser.add_argument(
        "--with_text", 
        action="store_true", 
        default=False,
        help="是否显示类别和ID文本，默认不显示"
    )
    parser.add_argument(
        "--text_scale", 
        type=float, 
        default=0.6, 
        help="文本大小比例，默认为0.6"
    )
    parser.add_argument(
        "--different_color", 
        action="store_true",
        default=False,
        help="为不同目标ID使用不同颜色，默认不使用"
    )
    parser.add_argument(
        "--depth", 
        type=int, 
        default=1, 
        help="扫描数据集目录的深度，默认为1"
    )
    
    args = parser.parse_args()
    
    # 如果未指定输出目录，则基于数据集目录名称自动生成
    if args.output_dir is None:
        dataset_dir_path = os.path.normpath(args.dataset_dir)
        # 获取数据集目录名称
        dataset_dir_name = os.path.basename(dataset_dir_path)
        # 获取父目录路径
        parent_dir_path = os.path.dirname(dataset_dir_path)
        if not parent_dir_path:
            parent_dir_path = "."
        # 构建默认输出目录路径：父目录/数据集目录名_output
        args.output_dir = os.path.join(parent_dir_path, f"{dataset_dir_name}_output")
        
        logger.info(f"输出目录未指定，使用默认路径: {args.output_dir}")
    
    return args


def generate_colors(num_colors: int) -> List[Tuple[int, int, int]]:
    """
    生成一组视觉上可区分的颜色，用于可视化不同的目标ID。

    参数:
        num_colors (int): 需要生成的颜色数量。

    返回:
        List[Tuple[int, int, int]]: 包含BGR颜色元组的列表。
    """
    # 确保至少请求一种颜色
    num_colors = max(1, num_colors)

    colors: List[Tuple[int, int, int]] = []
    for i in range(num_colors):
        # 在HSV颜色空间中生成不同的色调 (H)
        hue = i / num_colors
        # 将饱和度 (S) 和亮度 (V) 设置为较高值，以获得鲜艳的颜色
        hsv_color = np.array([[[hue * 180, 0.8 * 255, 0.9 * 255]]], dtype=np.uint8)
        # 将HSV颜色转换为BGR颜色
        bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR).flatten()
        colors.append((int(bgr_color[0]), int(bgr_color[1]), int(bgr_color[2])))

    return colors


def draw_bbox(
    img: np.ndarray,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    label: Optional[str] = None,
    track_id: Optional[int] = None,
    color: Tuple[int, int, int] = (0, 255, 0),
    text_color: Tuple[int, int, int] = (255, 255, 255),
    thickness: int = 2,
    with_text: bool = True,
    text_scale: float = 0.6,
) -> None:
    """
    在图像上绘制边界框和可选的标签文本。

    参数:
        img: 输入图像
        x1, y1: 边界框左上角坐标
        x2, y2: 边界框右下角坐标
        label: 可选的标签文本
        track_id: 可选的跟踪ID
        color: BGR格式的颜色元组，默认为绿色
        text_color: 文本颜色
        thickness: 线条粗细
        with_text: 是否显示文本
        text_scale: 文本大小比例
    """
    pt1 = (int(round(x1)), int(round(y1)))
    pt2 = (int(round(x2)), int(round(y2)))
    cv2.rectangle(img, pt1, pt2, color, thickness)

    # 如果需要显示文本
    if with_text and (label is not None or track_id is not None):
        text_items = []
        if label:
            text_items.append(label)
        if track_id is not None:
            text_items.append(f"ID:{track_id}")

        if text_items:
            text = " | ".join(text_items)
            font = cv2.FONT_HERSHEY_SIMPLEX
            text_thickness = max(1, int(thickness / 2))

            # 计算文本尺寸以绘制背景矩形
            (text_width, text_height), baseline = cv2.getTextSize(
                text, font, text_scale, text_thickness
            )

            # 绘制文本背景矩形
            bg_pt1 = (pt1[0], pt1[1] - text_height - baseline - 5)
            bg_pt2 = (pt1[0] + text_width + 5, pt1[1])
            cv2.rectangle(img, bg_pt1, bg_pt2, color, -1)  # 填充矩形

            # 绘制文本
            cv2.putText(
                img,
                text,
                (pt1[0] + 2, pt1[1] - baseline - 2),
                font,
                text_scale,
                text_color,
                text_thickness,
                cv2.LINE_AA,
            )


def process_sequence(task_args: Tuple[str, str, Dict[str, Any]]) -> None:
    """
    处理单个序列：加载注释文件，为每个图像绘制边界框，并保存结果。

    参数:
        task_args: 包含以下元素的元组:
            - sequence_dir (str): 序列目录路径。
            - output_base_dir (str): 输出基础目录。
            - draw_options (Dict[str, Any]): 绘制选项。
    """
    sequence_dir, output_base_dir, draw_options = task_args

    # 获取相对路径，用于在输出目录中创建相同的目录结构
    try:
        # 从完整路径中获取序列名
        sequence_name = os.path.basename(sequence_dir)

        # 构建目标目录路径
        output_dir = os.path.join(output_base_dir, sequence_name)

        logger.info(f"处理序列: {sequence_name}")
        logger.info(f"输出目录: {output_dir}")

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 加载注释目录
        annotation_directory = XAnyLabelingAnnotationDirectory()
        annotation_directory.dir_path = sequence_dir
        annotation_directory.walk_dir(recursive=False)
        annotation_directory.sort_path(group_directory=True)
        annotation_directory.load_json_files()

        # 检查是否有注释文件
        if len(annotation_directory.annotation_file_list) == 0:
            logger.error(f"在序列 {sequence_dir} 中未找到注释文件")
            return

        # 获取该序列的所有唯一ID，以生成不同颜色
        all_track_ids = set()
        if draw_options.get("different_color", False):
            for annotation_file in annotation_directory.annotation_file_list:
                for rect in annotation_file.rect_annotation_list:
                    if rect.track_id is not None:
                        all_track_ids.add(rect.track_id)

            id_colors = generate_colors(len(all_track_ids))
            id_to_color_map = {
                track_id: id_colors[i % len(id_colors)]
                for i, track_id in enumerate(sorted(all_track_ids))
            }
        else:
            id_to_color_map = {}  # 空字典表示使用默认颜色

        # 处理每个注释文件
        for annotation_file in annotation_directory.annotation_file_list:
            # 获取图像路径和输出路径
            image_path = annotation_file.pic_path
            image_filename = annotation_file.pic_file_name
            output_image_path = os.path.join(output_dir, image_filename)

            # 读取原始图像
            try:
                img = cv2.imread(image_path)
                if img is None:
                    logger.error(f"无法读取图像: {image_path}")
                    continue
            except Exception as e:
                logger.error(f"读取图像 {image_path} 时出错: {e}")
                continue

            # 克隆图像以进行绘制
            draw_img = img.copy()

            # 绘制所有矩形注释
            for rect in annotation_file.rect_annotation_list:
                label = rect.label if hasattr(rect, "label") else None
                track_id = rect.track_id if hasattr(rect, "track_id") else None

                # 选择颜色
                if track_id is not None and track_id in id_to_color_map:
                    color = id_to_color_map[track_id]
                else:
                    color = (0, 255, 0)  # 默认绿色

                # 绘制边界框
                draw_bbox(
                    draw_img,
                    rect.x1,
                    rect.y1,
                    rect.x2,
                    rect.y2,
                    label=label,
                    track_id=track_id,
                    color=color,
                    thickness=draw_options.get("thickness", 2),
                    with_text=draw_options.get("with_text", True),
                    text_scale=draw_options.get("text_scale", 0.6),
                )

            # 保存结果图像
            try:
                cv2.imwrite(output_image_path, draw_img)
            except Exception as e:
                logger.error(f"保存图像 {output_image_path} 时出错: {e}")

        logger.info(f"序列 {sequence_name} 处理完成")

    except Exception as e:
        logger.error(f"处理序列 {sequence_dir} 时发生错误: {e}")


def draw_dataset_with_bbox(
    dataset_dir: str,
    output_dir: str,
    draw_options: Dict[str, Any] = None,
    num_workers: int = None,
    depth: int = 1,
) -> None:
    """
    读取数据集中的所有序列，将边界框绘制到图像上，并保存到输出目录。

    参数:
        dataset_dir: 数据集目录路径
        output_dir: 输出目录路径
        draw_options: 绘制选项
        num_workers: 并行处理的工作进程数
        depth: 扫描数据集目录的深度
    """
    if draw_options is None:
        draw_options = {
            "thickness": 2,
            "with_text": True,
            "text_scale": 0.6,
            "different_color": True,
        }

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 获取所有序列目录
    try:
        sequence_dirs = get_dataset_dir_list(dataset_dir_path=dataset_dir, depth=depth)

        if not sequence_dirs:
            logger.error(f"在 {dataset_dir} 中未找到任何序列目录")
            return

        logger.info(f"找到 {len(sequence_dirs)} 个序列目录进行处理")

    except Exception as e:
        logger.error(f"获取数据集目录列表时出错: {e}")
        return

    # 准备多进程任务
    task_args = [(seq_dir, output_dir, draw_options) for seq_dir in sequence_dirs]

    # 确定实际使用的工作进程数
    # 如果 num_workers 未指定 (None)，multiprocessing.Pool 将默认使用 os.cpu_count()
    effective_workers = num_workers if num_workers is not None else io_cpu_count
    
    logger.info(f"准备使用 {effective_workers} 个工作进程处理 {len(task_args)} 个序列...")
    try:
        # 使用多进程处理所有序列
        # Pool(processes=None) 默认使用所有可用的CPU核心
        with multiprocessing.Pool(processes=num_workers) as pool:
            pool.map(process_sequence, task_args)
    except Exception as e:
        logger.error(f"多进程处理时出错: {e}")
        # 可以在此处添加更详细的错误处理或重试逻辑（如果适用）
    else:
        logger.info(f"所有 {len(task_args)} 个序列处理完成。结果已保存到 {output_dir}")


def main() -> None:
    """主函数，解析命令行参数并执行处理。"""
    args = parse_args()

    # 准备绘制选项
    draw_options = {
        "thickness": args.thickness,
        "with_text": args.with_text,
        "text_scale": args.text_scale,
        "different_color": args.different_color,
    }

    logger.info(f"数据集路径: {args.dataset_dir}")
    logger.info(f"输出目录: {args.output_dir}")
    logger.info(f"扫描深度: {args.depth}")
    logger.info(f"工作进程数: {'自动 (全部核心)' if args.num_workers is None else args.num_workers}")
    logger.info(f"绘制选项: {draw_options}")

    # 确认继续
    user_input = input("按 Enter 键继续，或输入 'q' 退出: ")
    if user_input.lower() == "q":
        logger.info("用户取消操作")
        return

    # 执行处理
    draw_dataset_with_bbox(
        dataset_dir=args.dataset_dir,
        output_dir=args.output_dir,
        draw_options=draw_options,
        num_workers=args.num_workers,
        depth=args.depth,
    )


if __name__ == "__main__":
    main()
