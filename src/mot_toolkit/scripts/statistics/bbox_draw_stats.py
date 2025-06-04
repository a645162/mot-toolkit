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

from mot_toolkit.vis.scheme.genshin.sigewinne_colors import SIGEWINNEColorScheme

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
        # 返回空张量 - 白色背景
        empty_canvas = torch.ones(
            (canvas_size, canvas_size, 3), dtype=torch.float32, device=device
        )
        return empty_canvas, sequence_name, 0

    # 创建RGB画布张量 (3通道) - 白色背景
    canvas = torch.ones(
        (canvas_size, canvas_size, 3), dtype=torch.float32, device=device
    )

    center = canvas_size // 2
    
    # 获取希格雯配色方案中的颜色
    color_scheme = SIGEWINNEColorScheme()
    hex_colors = color_scheme.hex_colors().copy()
    # Remove 3rd color
    hex_colors = hex_colors[:2] + hex_colors[3:]
    
    # 将十六进制颜色转换为RGB浮点数格式 (0-1范围)
    colors = []
    for hex_color in hex_colors:
        r = int(hex_color[1:3], 16) / 255.0
        g = int(hex_color[3:5], 16) / 255.0
        b = int(hex_color[5:7], 16) / 255.0
        colors.append(torch.tensor([r, g, b], device=device))
    
    # 根据序列名称选择颜色索引 (确保相同序列使用相同颜色)
    color_idx = hash(sequence_name) % len(colors)
    color = colors[color_idx]

    for norm_width, norm_height in normalized_sizes:
        # 计算实际像素尺寸
        pixel_width = int(norm_width * canvas_size)
        pixel_height = int(norm_height * canvas_size)

        # 计算矩形的边界
        left = max(0, center - pixel_width // 2)
        right = min(canvas_size, center + pixel_width // 2)
        top = max(0, center - pixel_height // 2)
        bottom = min(canvas_size, center + pixel_height // 2)

        # 绘制YOLO风格的矩形边框 (而不是填充整个区域)
        if right > left and bottom > top:
            # 确定线宽 (比例线宽)
            line_width = max(1, int(min(pixel_width, pixel_height) * 0.01))

            # 绘制上边框
            if top + line_width <= bottom:
                canvas[top : top + line_width, left:right, :] = (1.0 - alpha) * canvas[top : top + line_width, left:right, :] + alpha * color

            # 绘制下边框
            if bottom - line_width >= top:
                canvas[bottom - line_width : bottom, left:right, :] = (1.0 - alpha) * canvas[bottom - line_width : bottom, left:right, :] + alpha * color

            # 绘制左边框
            if left + line_width <= right:
                canvas[top:bottom, left : left + line_width, :] = (1.0 - alpha) * canvas[top:bottom, left : left + line_width, :] + alpha * color

            # 绘制右边框
            if right - line_width >= left:
                canvas[top:bottom, right - line_width : right, :] = (1.0 - alpha) * canvas[top:bottom, right - line_width : right, :] + alpha * color

    # 裁剪值，确保在0到1的范围内
    canvas = torch.clamp(canvas, 0.0, 1.0)

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
        return torch.ones((512, 512, 3), dtype=torch.float32)  # 返回白色背景

    print("正在叠加所有画布...")

    # 获取画布尺寸
    canvas_size = canvas_results[0][0].shape[0]
    device = canvas_results[0][0].device

    # 创建最终画布 (3通道) - 白色背景
    final_canvas = torch.ones(
        (canvas_size, canvas_size, 3), dtype=torch.float32, device=device
    )

    # 获取希格雯配色方案
    color_scheme = SIGEWINNEColorScheme()
    hex_colors = color_scheme.hex_colors()
    
    # 将十六进制颜色转换为RGB浮点数格式 (0-1范围)
    colors = []
    for hex_color in hex_colors:
        r = int(hex_color[1:3], 16) / 255.0
        g = int(hex_color[3:5], 16) / 255.0
        b = int(hex_color[5:7], 16) / 255.0
        colors.append(torch.tensor([r, g, b], device=device))

    total_bbox_count = 0
    valid_sequences = 0

    # 循环所有序列结果，每个序列使用不同颜色
    for idx, (canvas, sequence_name, bbox_count) in enumerate(canvas_results):
        if bbox_count > 0:
            # 从原始画布中减去白色背景，得到只有bbox线条的部分
            bbox_only = canvas - 1.0
            
            # 为这个序列选择颜色
            color_idx = idx % len(colors)
            color = colors[color_idx]
            
            # 将bbox线条部分应用当前颜色
            color_canvas = torch.zeros_like(canvas)
            for c in range(3):
                color_canvas[..., c] = bbox_only.sum(dim=2) * color[c]
                
            # 将有颜色的bbox添加到最终画布
            final_canvas = final_canvas + color_canvas
            
            total_bbox_count += bbox_count
            valid_sequences += 1
            print(f"  {sequence_name}: {bbox_count} bboxes (颜色: {hex_colors[color_idx]})")

    # 裁剪值到0-1范围
    final_canvas = torch.clamp(final_canvas, 0.0, 1.0)

    # 在画布中心绘制参考点
    center = canvas_size // 2
    marker_size = max(5, canvas_size // 100)
    final_canvas[
        center - marker_size : center + marker_size,
        center - marker_size : center + marker_size,
        :,
    ] = torch.tensor(
        [1.0, 0.0, 0.0], device=device
    )  # 红色中心点

    return final_canvas


def tensor_to_opencv_image(tensor: torch.Tensor) -> np.ndarray:
    """
    将PyTorch RGB张量转换为OpenCV BGR图像

    Args:
        tensor: 输入RGB张量 (H, W, 3)

    Returns:
        np.ndarray: OpenCV BGR图像
    """
    # 将张量移到CPU并转换为numpy
    numpy_array = tensor.cpu().numpy()

    # 转换为uint8 (0-255)
    image_uint8 = (numpy_array * 255).astype(np.uint8)

    # RGB到BGR转换 (OpenCV使用BGR格式)
    image_bgr = cv2.cvtColor(image_uint8, cv2.COLOR_RGB2BGR)

    return image_bgr


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
    image = tensor_to_opencv_image(final_canvas)

    # 添加网格线以增强可视化效果
    canvas_size = image.shape[0]
    grid_step = canvas_size // 10
    grid_color = (120, 120, 120)  # 浅灰色
    grid_thickness = 1

    # 绘制网格线
    for i in range(0, canvas_size + 1, grid_step):
        cv2.line(image, (0, i), (canvas_size, i), grid_color, grid_thickness)
        cv2.line(image, (i, 0), (i, canvas_size), grid_color, grid_thickness)

    # 绘制中心参考线
    center = canvas_size // 2
    center_color = (0, 0, 255)  # 红色
    center_thickness = 2
    cv2.line(image, (center, 0), (center, canvas_size), center_color, center_thickness)
    cv2.line(image, (0, center), (canvas_size, center), center_color, center_thickness)

    # 添加标题信息
    if title_info:
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        color = (255, 255, 255)
        thickness = 2

        # 在图像上方添加文字信息
        text_height = 30
        text_area_height = len(title_info) * text_height + 20

        # 创建带文字区域的新图像
        final_image = np.zeros(
            (canvas_size + text_area_height, canvas_size, 3), dtype=np.uint8
        )
        final_image[text_area_height:, :, :] = image

        # 添加文字
        y_offset = 25
        for key, value in title_info.items():
            text = f"{key}: {value}"
            cv2.putText(
                final_image, text, (10, y_offset), font, font_scale, color, thickness
            )
            y_offset += text_height
    else:
        final_image = image

    # 保存图像
    cv2.imwrite(output_path, final_image)
    print(f"可视化结果已保存到: {output_path}")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="绘制BBox尺寸分布统计图")

    parser.add_argument(
        "--base-path",
        type=str,
        default=r"/home/konghaomin/Datasets/MaritimeTrackAllData/MT20250319/LabelMe",
        help="数据集基础路径",
    )
    parser.add_argument(
        "--canvas-size", type=int, default=2048, help="画布尺寸（正方形边长）"
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
    parser.add_argument(
        "--title-info",
        action="store_true",
        help="是否在输出图像中添加标题信息",
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

    # 保存YOLO风格的可视化和热力图两种可视化结果
    output_prefix = os.path.splitext(args.output)[0]
    yolo_style_output = os.path.join(f"{output_prefix}_yolo_style.jpg")

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

    # 保存YOLO风格可视化结果
    save_visualization(
        final_canvas, yolo_style_output, title_info if args.title_info else None
    )

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
