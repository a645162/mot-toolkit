import csv
import os
import time
import math
from typing import List, Dict, Tuple

import tqdm
import matplotlib.pyplot as plt
import numpy as np

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list
from mot_toolkit.datatype.dataset.object_classfication import ObjectClassConfigure
from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotationDirectory


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


def calculate_sequence_adjacent_iou(sequence_dir_path: str) -> Tuple[float, int, int]:
    """
    计算单个序列的相邻帧IoU

    Args:
        sequence_dir_path: 序列目录路径

    Returns:
        tuple: (平均IoU, 有效IoU对数, 总帧数)
    """
    if not os.path.isdir(sequence_dir_path):
        return 0.0, 0, 0

    annotation_directory = XAnyLabelingAnnotationDirectory()
    annotation_directory.dir_path = sequence_dir_path
    annotation_directory.walk_dir(recursive=False)
    annotation_directory.sort_path(group_directory=True)

    frame_count = len(annotation_directory.file_list)
    if frame_count < 2:
        return 0.0, 0, frame_count

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

    # 计算相邻帧IoU
    iou_values = []

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

    # 计算平均IoU
    if iou_values:
        avg_iou = sum(iou_values) / len(iou_values)
        return avg_iou, len(iou_values), frame_count
    else:
        return 0.0, 0, frame_count


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
        "Valid IoU Pairs",
        "Average IoU",
        "IoU Standard Deviation",
    ]

    with open(csv_file_path, "w", newline="", encoding="utf-8") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(headers)

        for row in results:
            csv_writer.writerow(row)


def plot_iou_histogram(iou_data: List[float], output_path: str):
    """
    绘制IoU分布直方图

    Args:
        iou_data: IoU值列表
        output_path: 输出图像路径
    """
    if not iou_data:
        print("Warning: No IoU data available for plotting")
        return

    plt.figure(figsize=(12, 8))

    # 设置直方图区间 (0-1, 分成50个区间)
    bins = np.linspace(0, 1, 51)

    # 绘制直方图
    n, bins, patches = plt.hist(
        iou_data, bins=bins, alpha=0.7, color="blue", edgecolor="black"
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
        color="r",
        linestyle="--",
        linewidth=2,
        label=f"Mean: {mean_iou:.3f}",
    )
    plt.axvline(
        x=median_iou,
        color="g",
        linestyle="--",
        linewidth=2,
        label=f"Median: {median_iou:.3f}",
    )

    # 添加标题和标签
    plt.title(
        f"Adjacent Frame IoU Distribution\n"
        f"Mean: {mean_iou:.3f}, Std: {std_iou:.3f}, Median: {median_iou:.3f}\n"
        f"Range: [{min_iou:.3f}, {max_iou:.3f}], Total Samples: {len(iou_data)}",
        fontsize=14,
    )
    plt.xlabel("IoU Value", fontsize=12)
    plt.ylabel("Frequency", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend()

    # 保存图像
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"IoU distribution histogram saved to: {output_path}")
    print(
        f"IoU statistics - Mean: {mean_iou:.4f}, Std: {std_iou:.4f}, Median: {median_iou:.4f}"
    )


def plot_sequence_iou_bar_chart(
    sequence_results: List, output_path: str, top_n: int = 50
):
    """
    绘制序列IoU均值的柱状图

    Args:
        sequence_results: 序列结果列表 [(video_name, seq_name, frame_count, valid_pairs, avg_iou, std_iou)]
        output_path: 输出路径
        top_n: 显示前N个序列
    """
    if not sequence_results:
        print("Warning: No sequence results available for plotting")
        return

    # 过滤掉IoU为0的序列并按IoU排序
    valid_results = [
        (result[1], result[4]) for result in sequence_results if result[4] > 0
    ]
    valid_results.sort(key=lambda x: x[1], reverse=True)

    # 取前top_n个序列
    if len(valid_results) > top_n:
        valid_results = valid_results[:top_n]

    if not valid_results:
        print("Warning: No valid sequences with IoU > 0")
        return

    # 提取序列名和IoU值
    seq_names = [result[0] for result in valid_results]
    iou_values = [result[1] for result in valid_results]

    plt.figure(figsize=(20, 10))

    # 创建柱状图
    bars = plt.bar(
        range(len(seq_names)), iou_values, alpha=0.7, color="skyblue", edgecolor="black"
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
        color="r",
        linestyle="--",
        linewidth=2,
        label=f"Mean IoU: {mean_iou:.3f}",
    )

    plt.title(
        f"Top {len(valid_results)} Sequences by Average Adjacent Frame IoU", fontsize=16
    )
    plt.xlabel("Sequence Name", fontsize=12)
    plt.ylabel("Average IoU", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.7, axis="y")
    plt.legend()
    plt.tight_layout()

    # 保存图像
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Sequence IoU bar chart saved to: {output_path}")


def parse_args():
    """解析命令行参数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Calculate adjacent frame IoU statistics"
    )

    parser.add_argument(
        "--base-path",
        type=str,
        default=r"/home/konghaomin/Datasets/MaritimeTrackAllData/MT20250319/LabelMe",
        help="Dataset base path",
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

    # opt.base_path = r"/home/konghaomin/Datasets/SMD_LabelMe_Fix_20250509"

    return opt


def main():
    """主函数"""
    args = parse_args()

    base_path = os.path.abspath(args.base_path)
    output_csv = args.output_csv
    black_list = args.black_list

    # 输出目录设置
    output_dir_path = os.path.dirname(os.path.abspath(__file__))
    output_dir_path = os.path.join(output_dir_path, "output")
    output_dir_path = os.path.join(output_dir_path, "iou")

    # 获取数据集层级信息用于输出目录命名
    level1 = os.path.basename(base_path)
    level2 = os.path.basename(os.path.dirname(base_path))
    output_dir_path = os.path.join(output_dir_path, level1, level2)

    if not os.path.exists(output_dir_path):
        os.makedirs(output_dir_path, exist_ok=True)

    # 输出文件路径
    output_csv_path = os.path.join(output_dir_path, output_csv)
    iou_hist_path = os.path.join(output_dir_path, "adjacent_frame_iou_histogram.png")
    seq_bar_path = os.path.join(output_dir_path, "sequence_iou_bar_chart.png")
    summary_txt_path = os.path.join(output_dir_path, "iou_summary.txt")

    start_time = time.time()

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
    all_sequence_iou_values = []  # 收集所有序列的IoU值用于绘制分布图
    sequence_avg_ious = []  # 收集每个序列的平均IoU用于柱状图

    total_frames = 0
    total_valid_pairs = 0

    # 新增：用于加权平均计算的数据
    weighted_iou_sum = 0.0  # 加权IoU总和
    total_weighted_frames = 0  # 有效序列的总帧数

    for video_dir_path in filtered_video_dirs:
        video_name = os.path.basename(video_dir_path)
        sequence_dir_list = walk_dir_get_dir_list(video_dir_path)

        print(f"Processing video: {video_name} ({len(sequence_dir_list)} sequences)")

        for sequence_dir_path in tqdm.tqdm(
            sequence_dir_list, desc=f"Processing {video_name}"
        ):
            sequence_name = os.path.basename(sequence_dir_path)

            # 计算该序列的相邻帧IoU
            avg_iou, valid_pairs, frame_count = calculate_sequence_adjacent_iou(
                sequence_dir_path
            )

            # 计算标准差 (需要重新计算获取所有IoU值)
            std_iou = 0.0
            if valid_pairs > 1:
                # 重新计算获取所有IoU值用于计算标准差
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
                        all_sequence_iou_values.append(iou)  # 添加到总的IoU列表

                if iou_values:
                    std_iou = np.std(iou_values)

            # 添加结果
            results.append(
                [video_name, sequence_name, frame_count, valid_pairs, avg_iou, std_iou]
            )

            if avg_iou > 0:  # 只有有效的序列才添加到柱状图数据
                sequence_avg_ious.append(
                    (
                        video_name,
                        sequence_name,
                        frame_count,
                        valid_pairs,
                        avg_iou,
                        std_iou,
                    )
                )

                # 新增：累加加权IoU计算所需数据
                weighted_iou_sum += avg_iou * frame_count
                total_weighted_frames += frame_count

            total_frames += frame_count
            total_valid_pairs += valid_pairs

    # 计算按帧数加权的数据集IoU
    dataset_weighted_iou = (
        weighted_iou_sum / total_weighted_frames if total_weighted_frames > 0 else 0.0
    )

    # 保存CSV结果
    save_iou_results_to_csv(results, output_csv_path)

    # 绘制IoU分布直方图
    if all_sequence_iou_values:
        plot_iou_histogram(all_sequence_iou_values, iou_hist_path)

    # 绘制序列IoU柱状图
    if sequence_avg_ious:
        plot_sequence_iou_bar_chart(sequence_avg_ious, seq_bar_path)

    # 生成总结报告
    valid_sequences = [r for r in results if r[4] > 0]
    overall_avg_iou = np.mean([r[4] for r in valid_sequences]) if valid_sequences else 0
    overall_std_iou = np.std([r[4] for r in valid_sequences]) if valid_sequences else 0

    summary_lines = [
        "=" * 60,
        "Adjacent Frame IoU Statistics Summary",
        "=" * 60,
        f"Total Videos: {len(filtered_video_dirs)}",
        f"Total Sequences: {len(results)}",
        f"Valid Sequences (IoU > 0): {len(valid_sequences)}",
        f"Total Frames: {total_frames}",
        f"Total Valid IoU Pairs: {total_valid_pairs}",
        f"Overall Average IoU (Unweighted): {overall_avg_iou:.4f}",
        f"Dataset IoU (Frame-Weighted): {dataset_weighted_iou:.4f}",
        f"Overall Standard Deviation: {overall_std_iou:.4f}",
        "=" * 60,
    ]

    if all_sequence_iou_values:
        summary_lines.extend(
            [
                f"All IoU Values Statistics:",
                f"  Total IoU Samples: {len(all_sequence_iou_values)}",
                f"  Mean: {np.mean(all_sequence_iou_values):.4f}",
                f"  Std: {np.std(all_sequence_iou_values):.4f}",
                f"  Median: {np.median(all_sequence_iou_values):.4f}",
                f"  Min: {np.min(all_sequence_iou_values):.4f}",
                f"  Max: {np.max(all_sequence_iou_values):.4f}",
                "=" * 60,
                f"Weighted vs Unweighted IoU Comparison:",
                f"  Unweighted Average IoU: {overall_avg_iou:.4f}",
                f"  Frame-Weighted Dataset IoU: {dataset_weighted_iou:.4f}",
                f"  Difference: {abs(dataset_weighted_iou - overall_avg_iou):.4f}",
                "=" * 60,
            ]
        )

    summary_text = "\n".join(summary_lines)
    print("\n" + summary_text)

    # 保存总结到文件
    with open(summary_txt_path, "w", encoding="utf-8") as f:
        f.write(summary_text)

    end_time = time.time()

    print(f"CSV results saved to: {output_csv_path}")
    print(f"IoU histogram saved to: {iou_hist_path}")
    print(f"Sequence bar chart saved to: {seq_bar_path}")
    print(f"Summary saved to: {summary_txt_path}")
    print(f"Dataset Frame-Weighted IoU: {dataset_weighted_iou:.4f}")
    print(f"Processing completed in {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    main()
