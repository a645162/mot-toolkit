import csv
import os
import time
import math
from typing import List, Dict, Tuple

import tqdm
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list
from mot_toolkit.datatype.dataset.object_classfication import ObjectClassConfigure
from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotationDirectory
from mot_toolkit.vis.scheme.genshin.sigewinne_colors import SIGEWINNEColorScheme


def setup_plot_style():
    """设置绘图样式 - 模仿气泡图的Times字体设置"""
    plt.style.use("default")
    custom_font_path = os.path.expanduser("./Resources/Fonts/Times New Roman.ttf")
    if os.path.exists(custom_font_path):
        font_manager.fontManager.addfont(custom_font_path)
        plt.rc("font", family="Times New Roman")
        print(f"✓ 已注册自定义字体: {custom_font_path}")
    else:
        plt.rc("font", family="Times New Roman")
        print(f"✗ 未找到自定义字体文件: {custom_font_path}，尝试系统字体")
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.figsize"] = (10, 8)
    plt.rcParams["figure.dpi"] = 100
    # 字体大小设置
    plt.rcParams["font.size"] = 16
    plt.rcParams["axes.labelsize"] = 18
    plt.rcParams["axes.titlesize"] = 20
    plt.rcParams["xtick.labelsize"] = 15
    plt.rcParams["ytick.labelsize"] = 15
    plt.rcParams["legend.fontsize"] = 15


def calculate_iou(
    box1: Tuple[float, float, float, float], box2: Tuple[float, float, float, float]
) -> float:
    """
    计算两个边界框的IoU (Intersection over Union)

    Args:
        box1: (x1, y1, x2, y2) 第一个边界框
        box2: (x1, y1, x2, y2) 第二个边界框

    Returns:
        float: IoU值 (0-1之间)
    """
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2

    # 计算交集区域
    x1_inter = max(x1_1, x1_2)
    y1_inter = max(y1_1, y1_2)
    x2_inter = min(x2_1, x2_2)
    y2_inter = min(y2_1, y2_2)

    # 如果没有交集，返回0
    if x2_inter <= x1_inter or y2_inter <= y1_inter:
        return 0.0

    # 计算交集面积
    intersection_area = (x2_inter - x1_inter) * (y2_inter - y1_inter)

    # 计算各自的面积
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)

    # 计算并集面积
    union_area = area1 + area2 - intersection_area

    # 避免除零错误
    if union_area <= 0:
        return 0.0

    return intersection_area / union_area


def calculate_sequence_adjacent_iou(
    sequence_dir_path: str,
) -> Tuple[float, int, int, float, int]:
    """
    计算单个序列的相邻帧IoU (按照DanceTrack论文公式)

    Args:
        sequence_dir_path: 序列目录路径

    Returns:
        tuple: (DanceTrack式IoU, 有效IoU对数, 总帧数, 原始平均IoU, 对象数量)
    """
    if not os.path.isdir(sequence_dir_path):
        return 0.0, 0, 0, 0.0, 0

    annotation_directory = XAnyLabelingAnnotationDirectory()
    annotation_directory.dir_path = sequence_dir_path
    annotation_directory.walk_dir(recursive=False)
    annotation_directory.sort_path(group_directory=True)

    frame_count = len(annotation_directory.file_list)
    if frame_count < 2:
        return 0.0, 0, frame_count, 0.0, 0

    annotation_directory.load_json_files()

    # 存储每帧中每个目标的边界框 {frame_idx: {object_id: (x1, y1, x2, y2)}}
    frame_objects: Dict[int, Dict[str, Tuple[float, float, float, float]]] = {}

    # 遍历所有标注文件
    for frame_idx, annotation_file in enumerate(
        annotation_directory.annotation_file_list
    ):
        frame_objects[frame_idx] = {}

        for rect_annotation in annotation_file.rect_annotation_list:
            object_id = rect_annotation.label
            bbox = (
                rect_annotation.x1,
                rect_annotation.y1,
                rect_annotation.x2,
                rect_annotation.y2,
            )
            frame_objects[frame_idx][object_id] = bbox

    # 统计所有出现过的对象ID
    all_object_ids = set()
    for frame_objects_dict in frame_objects.values():
        all_object_ids.update(frame_objects_dict.keys())

    total_objects = len(all_object_ids)  # N: 对象数量
    total_frame_intervals = frame_count - 1  # T-1: 帧间隔数量

    # 计算相邻帧IoU
    iou_values = []
    total_iou_sum = 0.0  # 用于DanceTrack公式计算

    for frame_idx in range(frame_count - 1):
        current_frame = frame_objects.get(frame_idx, {})
        next_frame = frame_objects.get(frame_idx + 1, {})

        # 找到在连续两帧中都存在的目标
        common_objects = set(current_frame.keys()) & set(next_frame.keys())

        for obj_id in common_objects:
            bbox1 = current_frame[obj_id]
            bbox2 = next_frame[obj_id]
            iou = calculate_iou(bbox1, bbox2)
            iou_values.append(iou)
            total_iou_sum += iou

    # 计算原始平均IoU (用于兼容性)
    original_avg_iou = sum(iou_values) / len(iou_values) if iou_values else 0.0

    # 计算DanceTrack式IoU: U = 1/(N(T-1)) * ∑∑IoU
    # 注意：DanceTrack的公式假设所有对象在所有帧间隔都存在
    # 实际计算时，我们只对存在的IoU对进行求和，然后除以理论上的总对数 N*(T-1)
    dancetrack_iou = 0.0
    if total_objects > 0 and total_frame_intervals > 0:
        # DanceTrack公式：分母是所有对象在所有帧间隔的理论总数
        theoretical_total_pairs = total_objects * total_frame_intervals
        dancetrack_iou = total_iou_sum / theoretical_total_pairs

    return dancetrack_iou, len(iou_values), frame_count, original_avg_iou, total_objects


def walk_dir_get_dir_list(dir_path: str) -> List[str]:
    """获取目录下的所有子目录列表"""
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


def save_iou_results_to_csv(results: List, csv_file_path: str):
    """保存IoU统计结果到CSV文件"""
    headers = [
        "Video Name",
        "Sequence Name",
        "Frame Count",
        "Object Count",
        "Valid IoU Pairs",
        "DanceTrack IoU",
        "Original Average IoU",
        "IoU Standard Deviation",
    ]

    with open(csv_file_path, "w", newline="", encoding="utf-8") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(headers)

        for row in results:
            csv_writer.writerow(row)


def plot_iou_histogram_compare(
    iou_data1: List[float],
    iou_data2: List[float],
    dataset1_name: str,
    dataset2_name: str,
    output_path: str,
):
    """
    绘制两个数据集的IoU分布对比直方图

    Args:
        iou_data1: 第一个数据集的IoU值列表
        iou_data2: 第二个数据集的IoU值列表
        dataset1_name: 第一个数据集名称
        dataset2_name: 第二个数据集名称
        output_path: 输出图像路径
    """
    if not iou_data1 and not iou_data2:
        print("Warning: No IoU data available for plotting")
        return

    setup_plot_style()

    plt.figure(figsize=(14, 10))  # 增加高度从8到10

    # 获取希格雯配色
    color_scheme = SIGEWINNEColorScheme()
    colors = color_scheme.hex_colors()

    # 设置直方图区间 (0-1, 分成50个区间)
    bins = np.linspace(0, 1, 51)

    # 绘制双数据集直方图
    alpha = 0.7
    if iou_data1:
        plt.hist(
            iou_data1,
            bins=bins,
            alpha=alpha,
            color=colors[0],
            label=dataset1_name,  # 去掉样本数量显示
            edgecolor="black",
            linewidth=0.5,
        )

    if iou_data2:
        plt.hist(
            iou_data2,
            bins=bins,
            alpha=alpha,
            color=colors[2],
            label=dataset2_name,  # 去掉样本数量显示
            edgecolor="black",
            linewidth=0.5,
        )

    # 计算并显示统计信息
    stats_text = []

    if iou_data1:
        mean1 = np.mean(iou_data1)
        std1 = np.std(iou_data1)
        median1 = np.median(iou_data1)
        plt.axvline(x=mean1, color=colors[0], linestyle="--", linewidth=2, alpha=0.8)
        stats_text.append(
            f"{dataset1_name}: μ={mean1:.3f}, σ={std1:.3f}, Med={median1:.3f}"
        )

    if iou_data2:
        mean2 = np.mean(iou_data2)
        std2 = np.std(iou_data2)
        median2 = np.median(iou_data2)
        plt.axvline(x=mean2, color=colors[2], linestyle="--", linewidth=2, alpha=0.8)
        stats_text.append(
            f"{dataset2_name}: μ={mean2:.3f}, σ={std2:.3f}, Med={median2:.3f}"
        )

    # 添加标题和标签
    title = f"Adjacent Frame IoU Distribution Comparison"
    if stats_text:
        title += f"\n{' | '.join(stats_text)}"

    # plt.title(title, fontsize=14)
    plt.xlabel("IoU Value", fontsize=12)
    plt.ylabel("Frequency", fontsize=12)
    plt.grid(True, linestyle=":", alpha=0.5)
    plt.legend(loc="upper right")

    # 美化坐标轴
    plt.gca().spines["top"].set_visible(False)
    plt.gca().spines["right"].set_visible(False)

    # 保存图像
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")

    # Save additional formats
    for fmt in ["svg", "eps", "pdf"]:
        fmt_output_path = output_path.replace(".png", f".{fmt}")
        plt.savefig(fmt_output_path, format=fmt, bbox_inches="tight")

    plt.close()

    print(f"Comparison IoU distribution histogram saved to: {output_path}")


def plot_iou_histogram(iou_data: List[float], output_path: str):
    """
    绘制IoU分布直方图 (单数据集版本，保持向后兼容)
    """
    if not iou_data:
        print("Warning: No IoU data available for plotting")
        return

    setup_plot_style()

    plt.figure(figsize=(12, 8))

    # 获取希格雯配色
    color_scheme = SIGEWINNEColorScheme()
    colors = color_scheme.hex_colors()

    # 设置直方图区间 (0-1, 分成50个区间)
    bins = np.linspace(0, 1, 51)

    # 绘制直方图
    n, bins, patches = plt.hist(
        iou_data, bins=bins, alpha=0.7, color=colors[1], edgecolor="black"
    )

    # 计算统计信息
    mean_iou = np.mean(iou_data)
    std_iou = np.std(iou_data)
    median_iou = np.median(iou_data)
    min_iou = np.min(iou_data)
    max_iou = np.max(iou_data)

    # 添加统计线
    plt.axvline(
        x=mean_iou,
        color=colors[0],
        linestyle="--",
        linewidth=2,
        label=f"Mean: {mean_iou:.3f}",
    )
    plt.axvline(
        x=median_iou,
        color=colors[3],
        linestyle="--",
        linewidth=2,
        label=f"Median: {median_iou:.3f}",
    )

    # 添加标题和标签
    # plt.title(
    #     f"Adjacent Frame IoU Distribution\n"
    #     f"Mean: {mean_iou:.3f}, Std: {std_iou:.3f}, Median: {median_iou:.3f}\n"
    #     f"Range: [{min_iou:.3f}, {max_iou:.3f}], Total Samples: {len(iou_data)}",
    #     fontsize=14,
    # )
    plt.xlabel("IoU Value", fontsize=12)
    plt.ylabel("Frequency", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend()

    # 保存图像
    plt.savefig(output_path, dpi=300, bbox_inches="tight")

    # Save svg
    svg_output_path = output_path.replace(".png", ".svg")
    plt.savefig(svg_output_path, format="svg", bbox_inches="tight")

    # Save eps
    eps_output_path = output_path.replace(".png", ".eps")
    plt.savefig(eps_output_path, format="eps", bbox_inches="tight")

    plt.close()

    print(f"IoU distribution histogram saved to: {output_path}")
    print(
        f"IoU statistics - Mean: {mean_iou:.4f}, Std: {std_iou:.4f}, Median: {median_iou:.4f}"
    )


def plot_sequence_iou_bar_chart(
    sequence_results: List, output_path: str, top_n: int = 50
):
    """
    绘制序列IoU均值的柱状图 (使用DanceTrack IoU)

    Args:
        sequence_results: 序列结果列表
        output_path: 输出路径
        top_n: 显示前N个序列
    """
    if not sequence_results:
        print("Warning: No sequence results available for plotting")
        return

    setup_plot_style()

    # 过滤掉IoU为0的序列并按DanceTrack IoU排序 (索引5是DanceTrack IoU)
    valid_results = [
        (result[1], result[5]) for result in sequence_results if result[5] > 0
    ]
    valid_results.sort(key=lambda x: x[1], reverse=True)

    # 取前top_n个序列
    if len(valid_results) > top_n:
        valid_results = valid_results[:top_n]

    if not valid_results:
        print("Warning: No valid sequences with DanceTrack IoU > 0")
        return

    # 提取序列名和IoU值
    seq_names = [result[0] for result in valid_results]
    iou_values = [result[1] for result in valid_results]

    plt.figure(figsize=(20, 10))

    # 获取希格雯配色
    color_scheme = SIGEWINNEColorScheme()
    colors = color_scheme.hex_colors()

    # 创建柱状图，每个柱子交替使用希格雯配色
    bar_colors = [colors[i % len(colors)] for i in range(len(seq_names))]
    bars = plt.bar(
        range(len(seq_names)),
        iou_values,
        alpha=0.7,
        color=bar_colors,
        edgecolor="black",
    )

    # 设置x轴标签 (旋转45度以避免重叠)
    plt.xticks(range(len(seq_names)), seq_names, rotation=45, ha="right")

    # 添加数值标签到柱子顶部
    for i, bar in enumerate(bars):
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.001,
            f"{height:.3f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    # 计算总体统计
    mean_iou = np.mean(iou_values)
    plt.axhline(
        y=mean_iou,
        color=colors[0],
        linestyle="--",
        linewidth=2,
        label=f"Mean DanceTrack IoU: {mean_iou:.3f}",
    )

    # plt.title(
    #     f"Top {len(valid_results)} Sequences by DanceTrack Adjacent Frame IoU",
    #     fontsize=16,
    # )
    plt.xlabel("Sequence Name", fontsize=12)
    plt.ylabel("DanceTrack IoU", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.7, axis="y")
    plt.legend()
    plt.tight_layout()

    # 保存图像
    plt.savefig(output_path, dpi=300, bbox_inches="tight")

    # Save svg
    svg_output_path = output_path.replace(".png", ".svg")
    plt.savefig(svg_output_path, format="svg", bbox_inches="tight")

    # Save eps
    eps_output_path = output_path.replace(".png", ".eps")
    plt.savefig(eps_output_path, format="eps", bbox_inches="tight")

    plt.close()

    print(f"Sequence DanceTrack IoU bar chart saved to: {output_path}")


def parse_args():
    """解析命令行参数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Calculate adjacent frame IoU statistics and compare datasets"
    )

    parser.add_argument(
        "--base-path",
        type=str,
        default=r"/home/konghaomin/Datasets/MaritimeTrackAllData/MT20250319/LabelMe",
        help="First dataset base path",
    )
    parser.add_argument(
        "--base-path2",
        type=str,
        default=r"/home/konghaomin/Datasets/SMD_LabelMe_Ori",
        help="Second dataset base path for comparison (optional)",
    )
    parser.add_argument(
        "--dataset1-name",
        type=str,
        default="MartimeTrack",
        help="Name for the first dataset",
    )
    parser.add_argument(
        "--dataset2-name",
        type=str,
        default="Singapore Maritime Dataset",
        help="Name for the second dataset",
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default="adjacent_frame_iou_stats.csv",
        help="Output CSV file path",
    )
    parser.add_argument(
        "--black-list",
        nargs="+",
        default=["BV14S4y147jX-t5PTpDLBGiSESMzw"],
        help="List of video keywords to exclude",
    )

    opt = parser.parse_args()

    # Default second dataset path if not provided
    if opt.base_path2 is None:
        opt.base_path2 = r"/home/konghaomin/Datasets/SMD_LabelMe_Ori"

    # Auto-generate dataset names if using defaults
    if opt.dataset1_name == "Dataset1":
        opt.dataset1_name = os.path.basename(opt.base_path)
    if opt.dataset2_name == "Dataset2":
        opt.dataset2_name = os.path.basename(opt.base_path2)

    return opt


def process_dataset(base_path: str, black_list: List[str]) -> Tuple[List, List[float]]:
    """
    处理单个数据集

    Returns:
        tuple: (results, all_iou_values)
    """
    # 获取视频目录列表
    video_dir_list = get_dataset_dir_list(base_path)

    # 过滤黑名单
    filtered_video_dirs = []
    for video_dir_path in video_dir_list:
        found_blacklisted = False
        for keyword in black_list:
            if keyword in video_dir_path:
                found_blacklisted = True
                break
        if not found_blacklisted:
            filtered_video_dirs.append(video_dir_path)

    print(f"Found {len(filtered_video_dirs)} videos after filtering blacklist")

    results = []
    all_sequence_iou_values = []

    for video_dir_path in filtered_video_dirs:
        video_name = os.path.basename(video_dir_path)
        sequence_dir_list = walk_dir_get_dir_list(video_dir_path)

        print(f"Processing video: {video_name} ({len(sequence_dir_list)} sequences)")

        for sequence_dir_path in tqdm.tqdm(
            sequence_dir_list, desc=f"Processing {video_name}"
        ):
            sequence_name = os.path.basename(sequence_dir_path)

            # 计算该序列的相邻帧IoU
            dancetrack_iou, valid_pairs, frame_count, original_avg_iou, object_count = (
                calculate_sequence_adjacent_iou(sequence_dir_path)
            )

            # 计算标准差和收集IoU值
            std_iou = 0.0
            if valid_pairs > 1:
                # 重新计算获取所有IoU值
                annotation_directory = XAnyLabelingAnnotationDirectory()
                annotation_directory.dir_path = sequence_dir_path
                annotation_directory.walk_dir(recursive=False)
                annotation_directory.sort_path(group_directory=True)
                annotation_directory.load_json_files()

                frame_objects = {}
                for frame_idx, annotation_file in enumerate(
                    annotation_directory.annotation_file_list
                ):
                    frame_objects[frame_idx] = {}
                    for rect_annotation in annotation_file.rect_annotation_list:
                        object_id = rect_annotation.label
                        bbox = (
                            rect_annotation.x1,
                            rect_annotation.y1,
                            rect_annotation.x2,
                            rect_annotation.y2,
                        )
                        frame_objects[frame_idx][object_id] = bbox

                iou_values = []
                for frame_idx in range(
                    len(annotation_directory.annotation_file_list) - 1
                ):
                    current_frame = frame_objects.get(frame_idx, {})
                    next_frame = frame_objects.get(frame_idx + 1, {})
                    common_objects = set(current_frame.keys()) & set(next_frame.keys())

                    for obj_id in common_objects:
                        bbox1 = current_frame[obj_id]
                        bbox2 = next_frame[obj_id]
                        iou = calculate_iou(bbox1, bbox2)
                        iou_values.append(iou)
                        all_sequence_iou_values.append(iou)

                if iou_values:
                    std_iou = np.std(iou_values)

            # 添加结果
            results.append(
                [
                    video_name,
                    sequence_name,
                    frame_count,
                    object_count,
                    valid_pairs,
                    dancetrack_iou,
                    original_avg_iou,
                    std_iou,
                ]
            )

    return results, all_sequence_iou_values


def main():
    """主函数"""
    args = parse_args()

    base_path1 = os.path.abspath(args.base_path)
    base_path2 = os.path.abspath(args.base_path2) if args.base_path2 else None
    dataset1_name = args.dataset1_name
    dataset2_name = args.dataset2_name
    output_csv = args.output_csv
    black_list = args.black_list

    # 输出目录设置
    output_dir_path = os.path.dirname(os.path.abspath(__file__))
    output_dir_path = os.path.join(output_dir_path, "output")
    output_dir_path = os.path.join(output_dir_path, "iou_dancetrack_compare")

    if not os.path.exists(output_dir_path):
        os.makedirs(output_dir_path, exist_ok=True)

    start_time = time.time()

    print("=" * 60)
    print("Processing Dataset 1:", dataset1_name)
    print("Path:", base_path1)
    print("=" * 60)

    results1, all_iou_values1 = process_dataset(base_path1, black_list)

    results2, all_iou_values2 = [], []
    if base_path2:
        print("\n" + "=" * 60)
        print("Processing Dataset 2:", dataset2_name)
        print("Path:", base_path2)
        print("=" * 60)

        results2, all_iou_values2 = process_dataset(base_path2, black_list)

    # 保存CSV结果
    csv1_path = os.path.join(output_dir_path, f"{dataset1_name}_{output_csv}")
    save_iou_results_to_csv(results1, csv1_path)

    if results2:
        csv2_path = os.path.join(output_dir_path, f"{dataset2_name}_{output_csv}")
        save_iou_results_to_csv(results2, csv2_path)

    # 绘制对比直方图
    if base_path2 and (all_iou_values1 or all_iou_values2):
        compare_hist_path = os.path.join(
            output_dir_path, "iou_distribution_comparison.png"
        )
        plot_iou_histogram_compare(
            all_iou_values1,
            all_iou_values2,
            dataset1_name,
            dataset2_name,
            compare_hist_path,
        )

    # 绘制单独的直方图
    if all_iou_values1:
        hist1_path = os.path.join(output_dir_path, f"{dataset1_name}_iou_histogram.png")
        plot_iou_histogram(all_iou_values1, hist1_path)

    if all_iou_values2:
        hist2_path = os.path.join(output_dir_path, f"{dataset2_name}_iou_histogram.png")
        plot_iou_histogram(all_iou_values2, hist2_path)

    # 生成对比总结报告
    summary_lines = [
        "=" * 80,
        "Dataset Comparison Report - Adjacent Frame IoU Statistics",
        "=" * 80,
    ]

    # Dataset 1 statistics
    if results1:
        valid_sequences1 = [r for r in results1 if r[5] > 0]
        dancetrack_avg1 = (
            np.mean([r[5] for r in valid_sequences1]) if valid_sequences1 else 0
        )

        summary_lines.extend(
            [
                f"Dataset 1: {dataset1_name}",
                f"  Path: {base_path1}",
                f"  Total Sequences: {len(results1)}",
                f"  Valid Sequences: {len(valid_sequences1)}",
                f"  IoU Samples: {len(all_iou_values1)}",
                f"  DanceTrack IoU: {dancetrack_avg1:.4f}",
            ]
        )

        if all_iou_values1:
            summary_lines.extend(
                [
                    f"  Mean IoU: {np.mean(all_iou_values1):.4f}",
                    f"  Std IoU: {np.std(all_iou_values1):.4f}",
                    f"  Median IoU: {np.median(all_iou_values1):.4f}",
                ]
            )

    # Dataset 2 statistics
    if results2:
        valid_sequences2 = [r for r in results2 if r[5] > 0]
        dancetrack_avg2 = (
            np.mean([r[5] for r in valid_sequences2]) if valid_sequences2 else 0
        )

        summary_lines.extend(
            [
                "",
                f"Dataset 2: {dataset2_name}",
                f"  Path: {base_path2}",
                f"  Total Sequences: {len(results2)}",
                f"  Valid Sequences: {len(valid_sequences2)}",
                f"  IoU Samples: {len(all_iou_values2)}",
                f"  DanceTrack IoU: {dancetrack_avg2:.4f}",
            ]
        )

        if all_iou_values2:
            summary_lines.extend(
                [
                    f"  Mean IoU: {np.mean(all_iou_values2):.4f}",
                    f"  Std IoU: {np.std(all_iou_values2):.4f}",
                    f"  Median IoU: {np.median(all_iou_values2):.4f}",
                ]
            )

        # Comparison
        if results1 and all_iou_values1 and all_iou_values2:
            diff_dancetrack = dancetrack_avg1 - dancetrack_avg2
            diff_mean = np.mean(all_iou_values1) - np.mean(all_iou_values2)

            summary_lines.extend(
                [
                    "",
                    "Comparison (Dataset1 - Dataset2):",
                    f"  DanceTrack IoU Difference: {diff_dancetrack:+.4f}",
                    f"  Mean IoU Difference: {diff_mean:+.4f}",
                ]
            )

    summary_lines.append("=" * 80)
    summary_text = "\n".join(summary_lines)
    print("\n" + summary_text)

    # 保存总结到文件
    summary_txt_path = os.path.join(output_dir_path, "comparison_summary.txt")
    with open(summary_txt_path, "w", encoding="utf-8") as f:
        f.write(summary_text)

    end_time = time.time()
    print(f"\nProcessing completed in {end_time - start_time:.2f} seconds")
    print(f"Results saved to: {output_dir_path}")


if __name__ == "__main__":
    main()
