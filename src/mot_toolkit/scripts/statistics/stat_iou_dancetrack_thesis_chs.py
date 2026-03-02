import csv
import os
import time
import math
import pickle
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
    """设置绘图样式 - 使用中文宋体字体"""
    plt.style.use("default")
    custom_font_path = os.path.expanduser("./Resources/Fonts/simsun.ttc")
    if os.path.exists(custom_font_path):
        font_manager.fontManager.addfont(custom_font_path)
        plt.rc("font", family="SimSun")
        print(f"✓ 已注册自定义字体: {custom_font_path}")
    else:
        plt.rc("font", family="SimSun")
        print(f"✗ 未找到自定义字体文件: {custom_font_path}，尝试系统宋体")
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.figsize"] = (10, 8)
    plt.rcParams["figure.dpi"] = 100
    # 字体大小设置 - 论文标准（调大字号）
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
        "视频名称",
        "序列名称",
        "帧数",
        "目标数",
        "有效IoU对数",
        "DanceTrack IoU值",
        "原始平均IoU",
        "IoU标准差",
    ]

    with open(csv_file_path, "w", newline="", encoding="utf-8") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(headers)

        for row in results:
            csv_writer.writerow(row)


def save_statistics_cache(cache_file_path: str, cache_data: Dict):
    """保存统计缓存到pickle文件"""
    with open(cache_file_path, "wb") as cache_file:
        pickle.dump(cache_data, cache_file)


def load_statistics_cache(cache_file_path: str) -> Dict:
    """从pickle文件加载统计缓存"""
    with open(cache_file_path, "rb") as cache_file:
        return pickle.load(cache_file)


def plot_iou_histogram(iou_data: List[float], output_path: str):
    """
    绘制IoU分布直方图 - 论文插图风格

    Args:
        iou_data: IoU值列表
        output_path: 输出图像路径
    """
    if not iou_data:
        print("警告: 没有可用于绘图的IoU数据")
        return

    setup_plot_style()

    # 使用单栏图片尺寸 (论文标准)
    fig, ax = plt.subplots(figsize=(8, 5))

    # 获取希格雯配色
    color_scheme = SIGEWINNEColorScheme()
    colors = color_scheme.hex_colors()

    # 设置直方图区间 (0-1, 分成40个区间，减少过于细密的分割)
    bins = np.linspace(0, 1, 41)

    # 绘制直方图 - 简化样式
    n, bins, patches = ax.hist(
        iou_data,
        bins=bins,
        alpha=0.75,
        color=colors[1],
        edgecolor="black",
        linewidth=0.5,
    )

    # 计算统计信息
    mean_iou = np.mean(iou_data)
    std_iou = np.std(iou_data)
    median_iou = np.median(iou_data)

    # 添加统计线 - 简化，只保留最重要的
    ax.axvline(
        x=mean_iou,
        color=colors[0],
        linestyle="--",
        linewidth=1.5,
        label=f"均值: {mean_iou:.3f}",
        alpha=0.8,
    )

    # 简化标签 - 去除冗余信息
    ax.set_xlabel("IoU值")
    ax.set_ylabel("频数/次")

    # 简化网格
    ax.grid(True, linestyle=":", alpha=0.5, color="gray", linewidth=0.5)
    ax.set_axisbelow(True)

    # 简化图例 - 修复alpha参数错误
    legend = ax.legend(
        loc="upper right",
        frameon=True,
        fancybox=False,
        shadow=False,
        edgecolor="black",
        facecolor="white",
        fontsize=10,
    )
    # 设置图例透明度的正确方法
    legend.get_frame().set_alpha(0.9)

    # 美化坐标轴 - 学术风格
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.0)
    ax.spines["bottom"].set_linewidth(1.0)

    # 设置坐标轴范围
    ax.set_xlim(0, 1)
    ax.set_ylim(bottom=0)

    # 紧凑布局
    plt.tight_layout(pad=1.0)

    # 保存多种格式
    formats_info = [
        ("png", {"dpi": 300, "bbox_inches": "tight", "pad_inches": 0.1}),
        ("eps", {"format": "eps", "bbox_inches": "tight", "pad_inches": 0.1}),
        ("svg", {"format": "svg", "bbox_inches": "tight", "pad_inches": 0.1}),
        ("pdf", {"format": "pdf", "bbox_inches": "tight", "pad_inches": 0.1}),
    ]

    for fmt, kwargs in formats_info:
        fmt_output_path = output_path.replace(".png", f".{fmt}")
        try:
            plt.savefig(fmt_output_path, **kwargs)
            print(f"✓ 保存{fmt.upper()}格式: {fmt_output_path}")
        except Exception as e:
            print(f"✗ 保存{fmt.upper()}格式失败: {e}")

    plt.close()

    print(f"IoU分布直方图已保存到: {output_path}")
    print(
        f"统计信息 - 均值: {mean_iou:.4f}, 标准差: {std_iou:.4f}, 中位数: {median_iou:.4f}"
    )


def plot_sequence_iou_bar_chart(
    sequence_results: List, output_path: str, top_n: int = 30
):
    """
    绘制序列IoU均值的柱状图 - 论文插图风格

    Args:
        sequence_results: 序列结果列表
        output_path: 输出路径
        top_n: 显示前N个序列 (减少到30个以提高可读性)
    """
    if not sequence_results:
        print("警告: 没有可用于绘图的序列结果")
        return

    setup_plot_style()

    # 过滤和排序
    valid_results = [
        (result[1], result[5]) for result in sequence_results if result[5] > 0
    ]
    valid_results.sort(key=lambda x: x[1], reverse=True)

    # 取前top_n个序列
    if len(valid_results) > top_n:
        valid_results = valid_results[:top_n]

    if not valid_results:
        print("警告: 没有DanceTrack IoU大于0的有效序列")
        return

    # 提取数据
    seq_names = [result[0] for result in valid_results]
    iou_values = [result[1] for result in valid_results]

    # 调整图片尺寸 - 适合论文
    fig, ax = plt.subplots(figsize=(12, 6))

    # 获取希格雯配色
    color_scheme = SIGEWINNEColorScheme()
    colors = color_scheme.hex_colors()

    # 创建柱状图 - 简化样式
    bar_colors = [colors[i % len(colors)] for i in range(len(seq_names))]
    bars = ax.bar(
        range(len(seq_names)),
        iou_values,
        alpha=0.8,
        color=bar_colors,
        edgecolor="black",
        linewidth=0.5,
    )

    # 简化x轴标签显示 - 只显示每隔几个标签
    step = max(1, len(seq_names) // 15)  # 最多显示15个标签
    xtick_positions = range(0, len(seq_names), step)
    xtick_labels = [seq_names[i] for i in xtick_positions]
    ax.set_xticks(xtick_positions)
    ax.set_xticklabels(xtick_labels, rotation=45, ha="right", fontsize=9)

    # 添加平均线 - 简化
    mean_iou = np.mean(iou_values)
    ax.axhline(
        y=mean_iou,
        color="red",
        linestyle="--",
        linewidth=1.5,
        alpha=0.8,
        label=f"均值: {mean_iou:.3f}",
    )

    # 简化标签
    ax.set_xlabel("序列")
    ax.set_ylabel("DanceTrack IoU值")

    # 简化网格
    ax.grid(True, linestyle=":", alpha=0.5, axis="y", linewidth=0.5)
    ax.set_axisbelow(True)

    # 简化图例
    ax.legend(loc="upper right", fontsize=10)

    # 美化坐标轴
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.0)
    ax.spines["bottom"].set_linewidth(1.0)

    # 设置坐标轴范围从0开始
    ax.set_ylim(bottom=0)

    # 紧凑布局
    plt.tight_layout(pad=1.0)

    # 保存多种格式
    formats_info = [
        ("png", {"dpi": 300, "bbox_inches": "tight", "pad_inches": 0.1}),
        ("eps", {"format": "eps", "bbox_inches": "tight", "pad_inches": 0.1}),
        ("svg", {"format": "svg", "bbox_inches": "tight", "pad_inches": 0.1}),
        ("pdf", {"format": "pdf", "bbox_inches": "tight", "pad_inches": 0.1}),
    ]

    for fmt, kwargs in formats_info:
        fmt_output_path = output_path.replace(".png", f".{fmt}")
        try:
            plt.savefig(fmt_output_path, **kwargs)
            print(f"✓ 保存{fmt.upper()}格式: {fmt_output_path}")
        except Exception as e:
            print(f"✗ 保存{fmt.upper()}格式失败: {e}")

    plt.close()

    print(f"序列DanceTrack IoU柱状图已保存到: {output_path}")


def parse_args():
    """解析命令行参数"""
    import argparse

    parser = argparse.ArgumentParser(description="计算相邻帧IoU统计信息")

    parser.add_argument(
        "--base-path",
        type=str,
        default=r"/home/konghaomin/Datasets/MaritimeTrackAllData/MT20250319/LabelMe",
        help="数据集根路径",
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default="adjacent_frame_iou_stats.csv",
        help="输出CSV文件路径",
    )
    parser.add_argument(
        "--black-list",
        nargs="+",
        default=["BV14S4y147jX-t5PTpDLBGiSESMzw"],
        help="需要排除的视频关键词列表",
    )

    opt = parser.parse_args()

    # opt.base_path = r"/home/konghaomin/Datasets/SMD_LabelMe_Fix_20250509"
    # opt.base_path = r"/home/konghaomin/Datasets/SMD_LabelMe_Ori"
    opt.base_path = r"D:\Datasets\MaritimeTrackAllData\LabelMe"
    # opt.base_path = r"D:\Datasets\SMD\SMD_LabelMe_Ori"

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
    output_dir_path = os.path.join(output_dir_path, "iou_dancetrack")

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
    cache_file_path = os.path.join(output_dir_path, "iou_statistics_cache.pkl")

    start_time = time.time()

    # 初始化统计变量
    filtered_video_dirs = []
    results = []
    all_sequence_iou_values = []  # 收集所有序列的IoU值用于绘制分布图
    sequence_avg_ious = []  # 收集每个序列的平均IoU用于柱状图

    total_frames = 0
    total_valid_pairs = 0
    total_objects = 0

    # DanceTrack式统计
    total_dancetrack_iou_sum = 0.0
    total_theoretical_pairs = 0

    # 用于加权平均计算
    weighted_iou_sum = 0.0
    total_weighted_frames = 0

    # 优先从缓存加载
    if os.path.exists(cache_file_path):
        print(f"检测到缓存文件，直接加载统计结果: {cache_file_path}")
        cache_data = load_statistics_cache(cache_file_path)
        filtered_video_dirs = cache_data.get("filtered_video_dirs", [])
        results = cache_data.get("results", [])
        all_sequence_iou_values = cache_data.get("all_sequence_iou_values", [])
        sequence_avg_ious = cache_data.get("sequence_avg_ious", [])
        total_frames = cache_data.get("total_frames", 0)
        total_valid_pairs = cache_data.get("total_valid_pairs", 0)
        total_objects = cache_data.get("total_objects", 0)
        total_dancetrack_iou_sum = cache_data.get("total_dancetrack_iou_sum", 0.0)
        total_theoretical_pairs = cache_data.get("total_theoretical_pairs", 0)
        weighted_iou_sum = cache_data.get("weighted_iou_sum", 0.0)
        total_weighted_frames = cache_data.get("total_weighted_frames", 0)
    else:
        print("未检测到缓存文件，开始统计并缓存结果...")

        # 获取视频目录列表
        video_dir_list = get_dataset_dir_list(base_path)

        # 过滤黑名单
        for video_dir_path in video_dir_list:
            found_blacklisted = False
            for keyword in black_list:
                if keyword in video_dir_path:
                    found_blacklisted = True
                    break
            if not found_blacklisted:
                filtered_video_dirs.append(video_dir_path)

        print(f"黑名单过滤后共找到 {len(filtered_video_dirs)} 个视频")

        for video_dir_path in filtered_video_dirs:
            video_name = os.path.basename(video_dir_path)
            sequence_dir_list = walk_dir_get_dir_list(video_dir_path)

            print(f"正在处理视频: {video_name}（{len(sequence_dir_list)} 个序列）")

            for sequence_dir_path in tqdm.tqdm(
                sequence_dir_list, desc=f"处理 {video_name}"
            ):
                sequence_name = os.path.basename(sequence_dir_path)

                # 计算该序列的相邻帧IoU
                (
                    dancetrack_iou,
                    valid_pairs,
                    frame_count,
                    original_avg_iou,
                    object_count,
                ) = calculate_sequence_adjacent_iou(sequence_dir_path)

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
                        common_objects = set(current_frame.keys()) & set(
                            next_frame.keys()
                        )

                        for obj_id in common_objects:
                            bbox1 = current_frame[obj_id]
                            bbox2 = next_frame[obj_id]
                            iou = calculate_iou(bbox1, bbox2)
                            iou_values.append(iou)
                            all_sequence_iou_values.append(iou)  # 添加到总的IoU列表

                    if iou_values:
                        std_iou = np.std(iou_values)

                # 添加结果 [video_name, sequence_name, frame_count, object_count, valid_pairs, dancetrack_iou, original_avg_iou, std_iou]
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

                if dancetrack_iou > 0:  # 只有有效的序列才添加到柱状图数据
                    sequence_avg_ious.append(
                        (
                            video_name,
                            sequence_name,
                            frame_count,
                            object_count,
                            valid_pairs,
                            dancetrack_iou,
                            original_avg_iou,
                            std_iou,
                        )
                    )

                    # 累加加权IoU计算所需数据 (使用DanceTrack IoU)
                    weighted_iou_sum += dancetrack_iou * frame_count
                    total_weighted_frames += frame_count

                # DanceTrack式全局统计
                if object_count > 0 and frame_count > 1:
                    frame_intervals = frame_count - 1
                    theoretical_pairs = object_count * frame_intervals
                    total_dancetrack_iou_sum += dancetrack_iou * theoretical_pairs
                    total_theoretical_pairs += theoretical_pairs

                total_frames += frame_count
                total_valid_pairs += valid_pairs
                total_objects += object_count

        cache_data = {
            "filtered_video_dirs": filtered_video_dirs,
            "results": results,
            "all_sequence_iou_values": all_sequence_iou_values,
            "sequence_avg_ious": sequence_avg_ious,
            "total_frames": total_frames,
            "total_valid_pairs": total_valid_pairs,
            "total_objects": total_objects,
            "total_dancetrack_iou_sum": total_dancetrack_iou_sum,
            "total_theoretical_pairs": total_theoretical_pairs,
            "weighted_iou_sum": weighted_iou_sum,
            "total_weighted_frames": total_weighted_frames,
        }
        save_statistics_cache(cache_file_path, cache_data)
        print(f"统计缓存已保存: {cache_file_path}")

    # 计算全局DanceTrack IoU
    global_dancetrack_iou = (
        total_dancetrack_iou_sum / total_theoretical_pairs
        if total_theoretical_pairs > 0
        else 0.0
    )

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
    valid_sequences = [r for r in results if r[5] > 0]  # 使用DanceTrack IoU判断
    dancetrack_avg_iou = (
        np.mean([r[5] for r in valid_sequences]) if valid_sequences else 0
    )  # DanceTrack IoU
    original_avg_iou = (
        np.mean([r[6] for r in valid_sequences]) if valid_sequences else 0
    )  # 原始平均IoU
    dancetrack_std_iou = (
        np.std([r[5] for r in valid_sequences]) if valid_sequences else 0
    )

    summary_lines = [
        "=" * 60,
        "相邻帧IoU统计汇总（DanceTrack风格）",
        "=" * 60,
        f"视频总数: {len(filtered_video_dirs)}",
        f"序列总数: {len(results)}",
        f"有效序列数（DanceTrack IoU > 0）: {len(valid_sequences)}",
        f"总帧数: {total_frames}",
        f"目标总数: {total_objects}",
        f"有效IoU对总数: {total_valid_pairs}",
        f"理论配对总数: {total_theoretical_pairs}",
        "=" * 60,
        "DanceTrack IoU公式: U = 1/(N*(T-1)) * ∑∑IoU",
        f"全局DanceTrack IoU: {global_dancetrack_iou:.4f}",
        f"序列平均DanceTrack IoU: {dancetrack_avg_iou:.4f}",
        f"DanceTrack IoU标准差: {dancetrack_std_iou:.4f}",
        "=" * 60,
        "与原始方法对比:",
        f"原始平均IoU（简单均值）: {original_avg_iou:.4f}",
        f"按帧加权DanceTrack IoU: {dataset_weighted_iou:.4f}",
        f"差值（DanceTrack - 原始）: {dancetrack_avg_iou - original_avg_iou:.4f}",
        "=" * 60,
    ]

    if all_sequence_iou_values:
        summary_lines.extend(
            [
                "全部IoU值统计:",
                f"  IoU样本总数: {len(all_sequence_iou_values)}",
                f"  均值: {np.mean(all_sequence_iou_values):.4f}",
                f"  标准差: {np.std(all_sequence_iou_values):.4f}",
                f"  中位数: {np.median(all_sequence_iou_values):.4f}",
                f"  最小值: {np.min(all_sequence_iou_values):.4f}",
                f"  最大值: {np.max(all_sequence_iou_values):.4f}",
                "=" * 60,
            ]
        )

    summary_text = "\n".join(summary_lines)
    print("\n" + summary_text)

    # 保存总结到文件
    with open(summary_txt_path, "w", encoding="utf-8") as f:
        f.write(summary_text)

    end_time = time.time()

    print(f"CSV结果已保存到: {output_csv_path}")
    print(f"IoU直方图已保存到: {iou_hist_path}")
    print(f"序列柱状图已保存到: {seq_bar_path}")
    print(f"汇总报告已保存到: {summary_txt_path}")
    print(f"缓存文件路径: {cache_file_path}")
    print(f"全局DanceTrack IoU: {global_dancetrack_iou:.4f}")
    print(f"处理完成，耗时 {end_time - start_time:.2f} 秒")


if __name__ == "__main__":
    main()
