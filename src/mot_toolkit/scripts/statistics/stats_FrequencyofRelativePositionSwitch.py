import csv
import os
import time
import math
from typing import List, Dict, Tuple, Set

import tqdm
import matplotlib.pyplot as plt
import numpy as np

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list
from mot_toolkit.datatype.dataset.object_classfication import ObjectClassConfigure
from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotationDirectory
from mot_toolkit.vis.scheme.genshin.sigewinne_colors import SIGEWINNEColorScheme


def calculate_bbox_center(
    x1: float, y1: float, x2: float, y2: float
) -> Tuple[float, float]:
    """计算边界框的中心点坐标"""
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    return center_x, center_y


def calculate_bbox_overlap(
    box1: Tuple[float, float, float, float], box2: Tuple[float, float, float, float]
) -> bool:
    """
    判断两个边界框是否有重叠

    Args:
        box1: (x1, y1, x2, y2) 第一个边界框
        box2: (x1, y1, x2, y2) 第二个边界框

    Returns:
        bool: 是否有重叠
    """
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2

    # 计算交集区域
    x1_inter = max(x1_1, x1_2)
    y1_inter = max(y1_1, y1_2)
    x2_inter = min(x2_1, x2_2)
    y2_inter = min(y2_1, y2_2)

    # 如果有重叠，交集面积大于0
    return x2_inter > x1_inter and y2_inter > y1_inter


def sw_indicator_function(
    b_i_t: Tuple[float, float, float, float],
    b_j_t: Tuple[float, float, float, float],
    b_i_t1: Tuple[float, float, float, float],
    b_j_t1: Tuple[float, float, float, float],
) -> int:
    """
    指示函数sw(·)：检测两个物体在相邻帧中是否发生相对位置切换

    Args:
        b_i_t: 物体i在时刻t的边界框 (x1, y1, x2, y2)
        b_j_t: 物体j在时刻t的边界框 (x1, y1, x2, y2)
        b_i_t1: 物体i在时刻t+1的边界框 (x1, y1, x2, y2)
        b_j_t1: 物体j在时刻t+1的边界框 (x1, y1, x2, y2)

    Returns:
        int: 1表示发生相对位置切换，0表示未发生
    """
    # 只考虑有重叠的物体对
    if not (
        calculate_bbox_overlap(b_i_t, b_j_t) or calculate_bbox_overlap(b_i_t1, b_j_t1)
    ):
        return 0

    # 计算中心点坐标
    center_i_t = calculate_bbox_center(*b_i_t)
    center_j_t = calculate_bbox_center(*b_j_t)
    center_i_t1 = calculate_bbox_center(*b_i_t1)
    center_j_t1 = calculate_bbox_center(*b_j_t1)

    # 检查左右相对位置是否发生切换
    left_right_switch = False
    if center_i_t[0] != center_j_t[0] and center_i_t1[0] != center_j_t1[0]:
        # t时刻的左右关系
        i_left_of_j_t = center_i_t[0] < center_j_t[0]
        # t+1时刻的左右关系
        i_left_of_j_t1 = center_i_t1[0] < center_j_t1[0]
        # 检查是否发生切换
        left_right_switch = i_left_of_j_t != i_left_of_j_t1

    # 检查上下相对位置是否发生切换
    up_down_switch = False
    if center_i_t[1] != center_j_t[1] and center_i_t1[1] != center_j_t1[1]:
        # t时刻的上下关系
        i_above_j_t = center_i_t[1] < center_j_t[1]
        # t+1时刻的上下关系
        i_above_j_t1 = center_i_t1[1] < center_j_t1[1]
        # 检查是否发生切换
        up_down_switch = i_above_j_t != i_above_j_t1

    # 如果左右或上下任一方向发生切换，返回1
    return 1 if (left_right_switch or up_down_switch) else 0


def calculate_sequence_relative_position_switch_frequency(
    sequence_dir_path: str,
) -> Tuple[float, int, int, int, int]:
    """
    计算单个序列的相对位置切换频率

    Args:
        sequence_dir_path: 序列目录路径

    Returns:
        tuple: (相对位置切换频率S, 总切换次数, 物体数量N, 帧数T, 有效物体对数)
    """
    if not os.path.isdir(sequence_dir_path):
        return 0.0, 0, 0, 0, 0

    annotation_directory = XAnyLabelingAnnotationDirectory()
    annotation_directory.dir_path = sequence_dir_path
    annotation_directory.walk_dir(recursive=False)
    annotation_directory.sort_path(group_directory=True)

    frame_count = len(annotation_directory.file_list)
    if frame_count < 2:
        return 0.0, 0, 0, frame_count, 0

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

    N = len(all_object_ids)  # 物体数量
    T = frame_count  # 帧数

    if N < 2 or T < 2:
        return 0.0, 0, N, T, 0

    # 计算相对位置切换
    total_switches = 0
    valid_pairs_count = 0

    # 遍历所有相邻帧对
    for t in range(T - 1):
        current_frame = frame_objects.get(t, {})
        next_frame = frame_objects.get(t + 1, {})

        # 找到在连续两帧中都存在的目标
        common_objects = set(current_frame.keys()) & set(next_frame.keys())
        common_objects_list = list(common_objects)

        # 遍历所有物体对 (i, j)，其中 i != j
        for i in range(len(common_objects_list)):
            for j in range(i + 1, len(common_objects_list)):  # 避免重复计算对称情况
                obj_i = common_objects_list[i]
                obj_j = common_objects_list[j]

                b_i_t = current_frame[obj_i]
                b_j_t = current_frame[obj_j]
                b_i_t1 = next_frame[obj_i]
                b_j_t1 = next_frame[obj_j]

                # 计算指示函数
                switch_count = sw_indicator_function(b_i_t, b_j_t, b_i_t1, b_j_t1)
                total_switches += switch_count

                if (
                    switch_count > 0
                    or calculate_bbox_overlap(b_i_t, b_j_t)
                    or calculate_bbox_overlap(b_i_t1, b_j_t1)
                ):
                    valid_pairs_count += 1

    # 计算归一化因子：2*N*(T-1)*(N-1)
    # 注意：论文公式中的因子可能需要根据实际实现调整
    # 这里使用修正版本，考虑实际的物体对数量
    if N > 1 and T > 1:
        # 使用DanceTrack论文中的归一化因子
        normalization_factor = 2 * N * (T - 1) * (N - 1)
        frequency_s = (
            total_switches / normalization_factor if normalization_factor > 0 else 0.0
        )
    else:
        frequency_s = 0.0

    return frequency_s, total_switches, N, T, valid_pairs_count


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


def save_frps_results_to_csv(results: List, csv_file_path: str):
    """保存相对位置切换频率统计结果到CSV文件"""
    headers = [
        "Video Name",
        "Sequence Name",
        "Frame Count (T)",
        "Object Count (N)",
        "Total Switches",
        "Valid Pairs Count",
        "FRPS Frequency (S)",
        "Normalization Factor",
        "Raw Switch Rate",
    ]

    with open(csv_file_path, "w", newline="", encoding="utf-8") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(headers)

        for row in results:
            csv_writer.writerow(row)


def plot_frps_histogram(frps_data: List[float], output_path: str):
    """
    绘制相对位置切换频率分布直方图

    Args:
        frps_data: FRPS值列表
        output_path: 输出图像路径
    """
    if not frps_data:
        print("Warning: No FRPS data available for plotting")
        return

    plt.figure(figsize=(12, 8))

    # 获取希格雯配色
    color_scheme = SIGEWINNEColorScheme()
    colors = color_scheme.hex_colors()

    # 设置直方图区间 (根据数据范围自适应)
    max_value = max(frps_data)
    if max_value < 0.1:
        bins = np.linspace(0, 0.1, 51)
    elif max_value < 1.0:
        bins = np.linspace(0, 1.0, 51)
    else:
        bins = np.linspace(0, max_value * 1.1, 51)

    # 绘制直方图
    n, bins, patches = plt.hist(
        frps_data, bins=bins, alpha=0.7, color=colors[1], edgecolor="black"
    )

    # 计算统计信息
    mean_frps = np.mean(frps_data)
    std_frps = np.std(frps_data)
    median_frps = np.median(frps_data)
    min_frps = np.min(frps_data)
    max_frps = np.max(frps_data)

    # 添加统计线
    plt.axvline(
        x=mean_frps,
        color=colors[0],
        linestyle="--",
        linewidth=2,
        label=f"Mean: {mean_frps:.6f}",
    )
    plt.axvline(
        x=median_frps,
        color=colors[3],
        linestyle="--",
        linewidth=2,
        label=f"Median: {median_frps:.6f}",
    )

    # 添加标题和标签
    plt.title(
        f"Frequency of Relative Position Switch (FRPS) Distribution\n"
        f"Mean: {mean_frps:.6f}, Std: {std_frps:.6f}, Median: {median_frps:.6f}\n"
        f"Range: [{min_frps:.6f}, {max_frps:.6f}], Total Samples: {len(frps_data)}",
        fontsize=14,
    )
    plt.xlabel("FRPS Value", fontsize=12)
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

    print(f"FRPS distribution histogram saved to: {output_path}")
    print(
        f"FRPS statistics - Mean: {mean_frps:.6f}, Std: {std_frps:.6f}, Median: {median_frps:.6f}"
    )


def plot_sequence_frps_bar_chart(
    sequence_results: List, output_path: str, top_n: int = 50
):
    """
    绘制序列FRPS值的柱状图

    Args:
        sequence_results: 序列结果列表
        output_path: 输出路径
        top_n: 显示前N个序列
    """
    if not sequence_results:
        print("Warning: No sequence results available for plotting")
        return

    # 过滤掉FRPS为0的序列并按FRPS排序 (索引6是FRPS值)
    valid_results = [
        (result[1], result[6]) for result in sequence_results if result[6] > 0
    ]
    valid_results.sort(key=lambda x: x[1], reverse=True)

    # 取前top_n个序列
    if len(valid_results) > top_n:
        valid_results = valid_results[:top_n]

    if not valid_results:
        print("Warning: No valid sequences with FRPS > 0")
        return

    # 提取序列名和FRPS值
    seq_names = [result[0] for result in valid_results]
    frps_values = [result[1] for result in valid_results]

    plt.figure(figsize=(20, 10))

    # 获取希格雯配色
    color_scheme = SIGEWINNEColorScheme()
    colors = color_scheme.hex_colors()

    # 创建柱状图，每个柱子交替使用希格雯配色
    bar_colors = [colors[i % len(colors)] for i in range(len(seq_names))]
    bars = plt.bar(
        range(len(seq_names)),
        frps_values,
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
            height + height * 0.01,
            f"{height:.6f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    # 计算总体统计
    mean_frps = np.mean(frps_values)
    plt.axhline(
        y=mean_frps,
        color=colors[0],
        linestyle="--",
        linewidth=2,
        label=f"Mean FRPS: {mean_frps:.6f}",
    )

    plt.title(
        f"Top {len(valid_results)} Sequences by Frequency of Relative Position Switch",
        fontsize=16,
    )
    plt.xlabel("Sequence Name", fontsize=12)
    plt.ylabel("FRPS Value", fontsize=12)
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

    print(f"Sequence FRPS bar chart saved to: {output_path}")


def parse_args():
    """解析命令行参数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Calculate Frequency of Relative Position Switch statistics"
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
        default="frps_stats.csv",
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
    output_dir_path = os.path.join(output_dir_path, "frps")

    # 获取数据集层级信息用于输出目录命名
    level1 = os.path.basename(base_path)
    level2 = os.path.basename(os.path.dirname(base_path))
    output_dir_path = os.path.join(output_dir_path, level1, level2)

    if not os.path.exists(output_dir_path):
        os.makedirs(output_dir_path, exist_ok=True)

    # 输出文件路径
    output_csv_path = os.path.join(output_dir_path, output_csv)
    frps_hist_path = os.path.join(output_dir_path, "frps_histogram.png")
    seq_bar_path = os.path.join(output_dir_path, "sequence_frps_bar_chart.png")
    summary_txt_path = os.path.join(output_dir_path, "frps_summary.txt")

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
    all_frps_values = []  # 收集所有序列的FRPS值用于绘制分布图
    sequence_frps_data = []  # 收集每个序列的FRPS数据用于柱状图

    total_frames = 0
    total_objects = 0
    total_switches = 0
    total_valid_pairs = 0

    # 用于加权平均计算的数据
    weighted_frps_sum = 0.0
    total_weighted_frames = 0

    for video_dir_path in filtered_video_dirs:
        video_name = os.path.basename(video_dir_path)
        sequence_dir_list = walk_dir_get_dir_list(video_dir_path)

        print(f"Processing video: {video_name} ({len(sequence_dir_list)} sequences)")

        for sequence_dir_path in tqdm.tqdm(
            sequence_dir_list, desc=f"Processing {video_name}"
        ):
            sequence_name = os.path.basename(sequence_dir_path)

            # 计算该序列的相对位置切换频率
            frps, switches, N, T, valid_pairs = (
                calculate_sequence_relative_position_switch_frequency(sequence_dir_path)
            )

            # 计算归一化因子和原始切换率
            normalization_factor = 2 * N * (T - 1) * (N - 1) if N > 1 and T > 1 else 0
            raw_switch_rate = switches / (T - 1) if T > 1 else 0

            # 添加结果
            results.append(
                [
                    video_name,
                    sequence_name,
                    T,  # Frame Count
                    N,  # Object Count
                    switches,  # Total Switches
                    valid_pairs,  # Valid Pairs Count
                    frps,  # FRPS Frequency
                    normalization_factor,  # Normalization Factor
                    raw_switch_rate,  # Raw Switch Rate
                ]
            )

            if frps > 0:  # 只有有效的序列才添加到统计数据
                all_frps_values.append(frps)
                sequence_frps_data.append(
                    [
                        video_name,
                        sequence_name,
                        T,
                        N,
                        switches,
                        valid_pairs,
                        frps,
                        normalization_factor,
                        raw_switch_rate,
                    ]
                )

                # 累加加权FRPS计算所需数据
                weighted_frps_sum += frps * T
                total_weighted_frames += T

            total_frames += T
            total_objects += N
            total_switches += switches
            total_valid_pairs += valid_pairs

    # 计算按帧数加权的数据集FRPS
    dataset_weighted_frps = (
        weighted_frps_sum / total_weighted_frames if total_weighted_frames > 0 else 0.0
    )

    # 保存CSV结果
    save_frps_results_to_csv(results, output_csv_path)

    # 绘制FRPS分布直方图
    if all_frps_values:
        plot_frps_histogram(all_frps_values, frps_hist_path)

    # 绘制序列FRPS柱状图
    if sequence_frps_data:
        plot_sequence_frps_bar_chart(sequence_frps_data, seq_bar_path)

    # 生成总结报告
    valid_sequences = [r for r in results if r[6] > 0]  # FRPS > 0
    overall_avg_frps = (
        np.mean([r[6] for r in valid_sequences]) if valid_sequences else 0
    )
    overall_std_frps = np.std([r[6] for r in valid_sequences]) if valid_sequences else 0

    # 计算全局FRPS (根据论文公式)
    total_N = len(set([r[1] for r in results]))  # 所有序列中的唯一对象数估计
    global_normalization_factor = (
        2
        * total_objects
        * (total_frames - len(results))
        * (total_objects - 1)
        / len(results)
        if total_objects > 1 and total_frames > len(results)
        else 1
    )
    global_frps = (
        total_switches / global_normalization_factor
        if global_normalization_factor > 0
        else 0
    )

    summary_lines = [
        "=" * 60,
        "Frequency of Relative Position Switch (FRPS) Statistics Summary",
        "=" * 60,
        f"Formula: S = Σ Σ Σ sw(Bi^t, Bj^t, Bi^t+1, Bj^t+1) / [2*N*(T-1)*(N-1)]",
        "=" * 60,
        f"Total Videos: {len(filtered_video_dirs)}",
        f"Total Sequences: {len(results)}",
        f"Valid Sequences (FRPS > 0): {len(valid_sequences)}",
        f"Total Frames: {total_frames}",
        (
            f"Average Objects per Sequence: {total_objects / len(results):.2f}"
            if results
            else "0"
        ),
        f"Total Position Switches: {total_switches}",
        f"Total Valid Object Pairs: {total_valid_pairs}",
        "=" * 60,
        f"Overall Average FRPS (Unweighted): {overall_avg_frps:.6f}",
        f"Dataset FRPS (Frame-Weighted): {dataset_weighted_frps:.6f}",
        f"Global FRPS Estimate: {global_frps:.6f}",
        f"FRPS Standard Deviation: {overall_std_frps:.6f}",
        "=" * 60,
    ]

    if all_frps_values:
        summary_lines.extend(
            [
                f"All FRPS Values Statistics:",
                f"  Total FRPS Samples: {len(all_frps_values)}",
                f"  Mean: {np.mean(all_frps_values):.6f}",
                f"  Std: {np.std(all_frps_values):.6f}",
                f"  Median: {np.median(all_frps_values):.6f}",
                f"  Min: {np.min(all_frps_values):.6f}",
                f"  Max: {np.max(all_frps_values):.6f}",
                f"  75th Percentile: {np.percentile(all_frps_values, 75):.6f}",
                f"  95th Percentile: {np.percentile(all_frps_values, 95):.6f}",
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
    print(f"FRPS histogram saved to: {frps_hist_path}")
    print(f"Sequence bar chart saved to: {seq_bar_path}")
    print(f"Summary saved to: {summary_txt_path}")
    print(f"Dataset Frame-Weighted FRPS: {dataset_weighted_frps:.6f}")
    print(f"Processing completed in {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    main()
