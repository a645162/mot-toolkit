import os
import time
import argparse
from typing import List, Tuple, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

import torch
import cv2
import numpy as np
import tqdm

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list
from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotationDirectory

os.environ["CUDA_VISIBLE_DEVICES"] = "4"  # 设置可见的GPU设备


def walk_dir_get_dir_list(dir_path: str) -> List[str]:
    """获取目录下的所有子目录"""
    dir_path = dir_path.strip()
    if dir_path == "":
        return []

    dir_path = os.path.abspath(dir_path)
    dir_list = []

    for dir_name in os.listdir(dir_path):
        dir_path_tmp = os.path.join(dir_path, dir_name)
        if os.path.isdir(dir_path_tmp):
            dir_list.append(dir_path_tmp)

    return dir_list


def get_sequence_bbox_info(
    sequence_dir_path: str,
) -> Tuple[List[Tuple[float, float]], str]:
    """
    获取序列中所有bbox的归一化尺寸信息

    Args:
        sequence_dir_path: 序列目录路径

    Returns:
        Tuple[List[Tuple[float, float]], str]: (归一化尺寸列表, 序列名称)
    """
    if not os.path.isdir(sequence_dir_path):
        return [], ""

    sequence_name = os.path.basename(sequence_dir_path)

    annotation_directory = XAnyLabelingAnnotationDirectory()
    annotation_directory.dir_path = sequence_dir_path
    annotation_directory.walk_dir(recursive=False)
    annotation_directory.sort_path(group_directory=True)

    if len(annotation_directory.file_list) == 0:
        return [], sequence_name

    annotation_directory.load_json_files()

    normalized_sizes = []

    for annotation_file in annotation_directory.annotation_file_list:
        img_width, img_height = (
            annotation_file.image_width,
            annotation_file.image_height,
        )

        for rect_annotation in annotation_file.rect_annotation_list:
            # 计算归一化尺寸
            norm_width = rect_annotation.width / img_width
            norm_height = rect_annotation.height / img_height

            normalized_sizes.append((norm_width, norm_height))

    return normalized_sizes, sequence_name


def find_max_dimensions(all_sequences: List[str]) -> Tuple[float, float]:
    """
    找到所有序列中bbox的最大归一化尺寸

    Args:
        all_sequences: 所有序列路径列表

    Returns:
        Tuple[float, float]: (最大宽度, 最大高度)
    """
    max_width = 0.0
    max_height = 0.0

    print("正在计算最大bbox尺寸...")
    for sequence_path in tqdm.tqdm(all_sequences):
        normalized_sizes, _ = get_sequence_bbox_info(sequence_path)

        for width, height in normalized_sizes:
            max_width = max(max_width, width)
            max_height = max(max_height, height)

    return max_width, max_height


def draw_sequence_bboxes_tensor(
    sequence_path: str, canvas_size: int, alpha: float = 0.1, device: str = "cpu"
) -> Tuple[torch.Tensor, str, int]:
    """
    使用PyTorch张量为单个序列绘制所有bbox

    Args:
        sequence_path: 序列路径
        canvas_size: 画布尺寸（正方形）
        alpha: 透明度
        device: PyTorch设备

    Returns:
        Tuple[torch.Tensor, str, int]: (画布张量, 序列名称, bbox数量)
    """
    normalized_sizes, sequence_name = get_sequence_bbox_info(sequence_path)

    if not normalized_sizes:
        # 返回空张量
        empty_canvas = torch.zeros(
            (canvas_size, canvas_size), dtype=torch.float32, device=device
        )
        return empty_canvas, sequence_name, 0

    # 创建画布张量
    canvas = torch.zeros((canvas_size, canvas_size), dtype=torch.float32, device=device)

    center = canvas_size // 2

    for norm_width, norm_height in normalized_sizes:
        # 计算实际像素尺寸
        pixel_width = int(norm_width * canvas_size)
        pixel_height = int(norm_height * canvas_size)

        # 计算矩形的边界
        left = max(0, center - pixel_width // 2)
        right = min(canvas_size, center + pixel_width // 2)
        top = max(0, center - pixel_height // 2)
        bottom = min(canvas_size, center + pixel_height // 2)

        # 在张量上绘制矩形（加法操作，支持叠加）
        if right > left and bottom > top:
            canvas[top:bottom, left:right] += alpha

    return canvas, sequence_name, len(normalized_sizes)


def process_sequences_parallel(
    all_sequences: List[str],
    canvas_size: int,
    alpha: float = 0.1,
    max_workers: int = 4,
    device: str = "cpu",
) -> List[Tuple[torch.Tensor, str, int]]:
    """
    并行处理所有序列

    Args:
        all_sequences: 所有序列路径列表
        canvas_size: 画布尺寸
        alpha: 透明度
        max_workers: 最大工作线程数
        device: PyTorch设备

    Returns:
        List[Tuple[torch.Tensor, str, int]]: 处理结果列表
    """
    results = []

    print(f"正在使用{max_workers}个线程并行处理{len(all_sequences)}个序列...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_sequence = {
            executor.submit(
                draw_sequence_bboxes_tensor, seq_path, canvas_size, alpha, device
            ): seq_path
            for seq_path in all_sequences
        }

        # 收集结果
        for future in tqdm.tqdm(
            as_completed(future_to_sequence), total=len(all_sequences)
        ):
            try:
                canvas, sequence_name, bbox_count = future.result()
                results.append((canvas, sequence_name, bbox_count))
            except Exception as exc:
                sequence_path = future_to_sequence[future]
                print(f"序列 {sequence_path} 处理失败: {exc}")

    return results


def combine_canvases(
    canvas_results: List[Tuple[torch.Tensor, str, int]],
) -> torch.Tensor:
    """
    叠加所有画布张量

    Args:
        canvas_results: 画布结果列表

    Returns:
        torch.Tensor: 叠加后的最终画布
    """
    if not canvas_results:
        return torch.zeros((512, 512), dtype=torch.float32)

    print("正在叠加所有画布...")

    # 获取画布尺寸
    canvas_size = canvas_results[0][0].shape[0]
    device = canvas_results[0][0].device

    # 创建最终画布
    final_canvas = torch.zeros(
        (canvas_size, canvas_size), dtype=torch.float32, device=device
    )

    total_bbox_count = 0
    valid_sequences = 0

    for canvas, sequence_name, bbox_count in canvas_results:
        if bbox_count > 0:
            final_canvas += canvas
            total_bbox_count += bbox_count
            valid_sequences += 1
            print(f"  {sequence_name}: {bbox_count} bboxes")

    print(f"总计: {valid_sequences} 个有效序列, {total_bbox_count} 个bbox")

    return final_canvas


def tensor_to_opencv_image(
    tensor: torch.Tensor, colormap: int = cv2.COLORMAP_JET
) -> np.ndarray:
    """
    将PyTorch张量转换为OpenCV图像

    Args:
        tensor: 输入张量
        colormap: OpenCV颜色映射

    Returns:
        np.ndarray: OpenCV图像
    """
    # 将张量移到CPU并转换为numpy
    numpy_array = tensor.cpu().numpy()

    # 归一化到0-255范围
    if numpy_array.max() > numpy_array.min():
        normalized = (numpy_array - numpy_array.min()) / (
            numpy_array.max() - numpy_array.min()
        )
    else:
        normalized = numpy_array

    # 转换为uint8
    image_uint8 = (normalized * 255).astype(np.uint8)

    # 应用颜色映射
    colored_image = cv2.applyColorMap(image_uint8, colormap)

    return colored_image


def save_visualization(
    final_canvas: torch.Tensor, output_path: str, title_info: Dict = None
) -> None:
    """
    保存可视化结果

    Args:
        final_canvas: 最终画布张量
        output_path: 输出路径
        title_info: 标题信息字典
    """
    # 转换为OpenCV图像
    colored_image = tensor_to_opencv_image(final_canvas, cv2.COLORMAP_JET)

    # 添加标题信息
    if title_info:
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        color = (255, 255, 255)
        thickness = 2

        # 在图像上方添加文字信息
        canvas_size = colored_image.shape[0]
        text_height = 30
        text_area_height = len(title_info) * text_height + 20

        # 创建带文字区域的新图像
        final_image = np.zeros(
            (canvas_size + text_area_height, canvas_size, 3), dtype=np.uint8
        )
        final_image[text_area_height:, :, :] = colored_image

        # 添加文字
        y_offset = 25
        for key, value in title_info.items():
            text = f"{key}: {value}"
            cv2.putText(
                final_image, text, (10, y_offset), font, font_scale, color, thickness
            )
            y_offset += text_height
    else:
        final_image = colored_image

    # 保存图像
    cv2.imwrite(output_path, final_image)
    print(f"可视化结果已保存到: {output_path}")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="绘制bbox尺寸分布统计图")

    parser.add_argument(
        "--base-path",
        type=str,
        default=r"/home/konghaomin/Datasets/MaritimeTrackAllData/MT20250319/LabelMe",
        help="数据集基础路径",
    )
    parser.add_argument(
        "--canvas-size", type=int, default=1024, help="画布尺寸（正方形边长）"
    )
    parser.add_argument("--alpha", type=float, default=0.05, help="每个bbox的透明度")
    parser.add_argument("--max-workers", type=int, default=8, help="最大工作线程数")
    parser.add_argument(
        "--output", type=str, default="bbox_distribution.png", help="输出图像文件名"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda",
        choices=["cpu", "cuda"],
        help="PyTorch计算设备",
    )
    parser.add_argument(
        "--black-list",
        nargs="+",
        default=["BV14S4y147jX-t5PTpDLBGiSESMzw"],
        help="要排除的视频关键词列表",
    )

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    start_time = time.time()

    # 检查设备可用性
    if args.device == "cuda" and not torch.cuda.is_available():
        print("CUDA不可用，将使用CPU")
        device = "cpu"
    else:
        device = args.device

    print(f"使用设备: {device}")

    base_path = os.path.abspath(args.base_path)

    output_path = os.path.join(args.output)

    # 获取所有视频目录
    video_dir_list = get_dataset_dir_list(base_path)

    # 过滤黑名单
    filtered_video_dirs = []
    for video_dir_path in video_dir_list:
        is_blacklisted = any(keyword in video_dir_path for keyword in args.black_list)
        if not is_blacklisted:
            filtered_video_dirs.append(video_dir_path)

    print(f"找到 {len(filtered_video_dirs)} 个视频目录（已过滤黑名单）")

    # 获取所有序列
    all_sequences = []
    for video_dir_path in filtered_video_dirs:
        sequence_dirs = walk_dir_get_dir_list(video_dir_path)
        all_sequences.extend(sequence_dirs)

    print(f"总共找到 {len(all_sequences)} 个序列")

    if not all_sequences:
        print("没有找到任何序列，程序退出")
        return

    # 计算最大尺寸
    max_width, max_height = find_max_dimensions(all_sequences)
    max_dimension = max(max_width, max_height)

    print(f"最大归一化尺寸: 宽度={max_width:.4f}, 高度={max_height:.4f}")
    print(f"使用最大尺寸: {max_dimension:.4f}")
    print(f"画布尺寸: {args.canvas_size}x{args.canvas_size}")

    # 并行处理所有序列
    canvas_results = process_sequences_parallel(
        all_sequences, args.canvas_size, args.alpha, args.max_workers, device
    )

    # 叠加所有画布
    final_canvas = combine_canvases(canvas_results)

    # 计算统计信息
    total_bbox_count = sum(count for _, _, count in canvas_results)
    valid_sequences = sum(1 for _, _, count in canvas_results if count > 0)

    # 准备标题信息
    title_info = {
        "Total Sequences": len(all_sequences),
        "Valid Sequences": valid_sequences,
        "Total BBoxes": total_bbox_count,
        "Max Normalized Size": f"{max_dimension:.4f}",
        "Canvas Size": f"{args.canvas_size}x{args.canvas_size}",
        "Alpha": args.alpha,
    }

    # 保存可视化结果
    save_visualization(final_canvas, output_path, title_info)

    end_time = time.time()
    print(f"处理完成，耗时: {end_time - start_time:.2f} 秒")

    # 显示最终统计
    print("\n" + "=" * 50)
    print("最终统计:")
    for key, value in title_info.items():
        print(f"  {key}: {value}")
    print("=" * 50)


if __name__ == "__main__":
    main()
