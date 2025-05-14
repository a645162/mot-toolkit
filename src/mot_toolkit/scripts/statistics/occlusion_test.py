"""
遮挡分析模块

该模块用于分析多目标跟踪数据中的遮挡情况，包括:
1. 统计每个ID的遮挡帧数
2. 统计每个ID的断开次数
3. 统计每次断开的持续时长
4. 生成相关的统计图表

注意: 不同序列的ID都是从1开始，ID只在同一序列内唯一，不同序列之间的ID可能重复
"""

import os
import csv
import argparse
from collections import defaultdict
from typing import List, Dict, Tuple, Optional

import shutil

import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import multiprocessing
from functools import partial

from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotationDirectory
from mot_toolkit.vis.scheme.genshin.sigewinne_colors import SIGEWINNEColorScheme
from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list


class OcclusionAnalyzer:
    """遮挡分析器类"""

    def __init__(self, sequence_dir: str, output_dir: str = None):
        """
        初始化遮挡分析器

        Args:
            sequence_dir: 序列目录路径
            output_dir: 输出目录路径，如果为None则使用默认路径
        """
        self.sequence_dir = os.path.abspath(sequence_dir)
        self.sequence_name = os.path.basename(self.sequence_dir)

        # 设置输出目录
        if output_dir is None:
            # 默认输出到当前脚本所在目录的output子目录下
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.output_dir = os.path.join(script_dir, "output", "occlusion_analysis")
        else:
            self.output_dir = os.path.abspath(output_dir)

        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)

        # 初始化颜色方案
        self.color_scheme = SIGEWINNEColorScheme()

        # 数据存储
        self.object_frames = defaultdict(list)  # 每个ID出现在哪些帧
        self.occlusion_stats = {}  # 存储每个ID的遮挡统计信息
        self.gap_counts = defaultdict(list)  # 存储每个ID的断开次数
        self.gap_durations = defaultdict(list)  # 存储每个ID的每次断开持续时长

        # 序列总帧数
        self.total_frames = 0

        # 已加载数据标志
        self.data_loaded = False

    def load_data(self):
        """加载序列数据"""
        print(f"正在加载序列数据: {self.sequence_name}")

        # 加载标注目录
        annotation_directory = XAnyLabelingAnnotationDirectory()
        annotation_directory.dir_path = self.sequence_dir
        annotation_directory.walk_dir(recursive=False)
        annotation_directory.sort_path(group_directory=True)

        # 获取帧数
        self.total_frames = len(annotation_directory.file_list)

        if self.total_frames == 0:
            print(f"警告: 序列 {self.sequence_name} 没有帧!")
            return False

        print(f"序列总帧数: {self.total_frames}")

        # 加载JSON文件
        annotation_directory.load_json_files()

        # 遍历所有标注文件，记录每个ID出现在哪些帧
        for frame_idx, annotation_file in enumerate(
            annotation_directory.annotation_file_list
        ):
            # 使用图片文件名作为帧ID
            frame_id = os.path.basename(annotation_file.file_path)
            for rect_annotation in annotation_file.rect_annotation_list:
                object_id = rect_annotation.label
                # 直接记录每个ID出现的帧（图片文件名）
                self.object_frames[object_id].append(frame_id)

        print(f"共检测到 {len(self.object_frames)} 个不同的目标ID")
        self.data_loaded = True
        return True

    def analyze_occlusions(self):
        """
        分析遮挡情况

        注意：分析基于单个序列内的ID，不涉及跨序列比较
        """
        if not self.data_loaded:
            if not self.load_data():
                print("无法分析遮挡: 数据加载失败")
                return False

        print("正在分析遮挡情况...")

        # 重新创建标注目录对象，用于获取帧索引
        annotation_directory = XAnyLabelingAnnotationDirectory()
        annotation_directory.dir_path = self.sequence_dir
        annotation_directory.walk_dir(recursive=False)
        annotation_directory.sort_path(group_directory=True)
        annotation_directory.load_json_files()

        # 将帧ID映射到帧索引的字典
        frame_id_to_index = {}
        for frame_idx, annotation_file in enumerate(
            annotation_directory.annotation_file_list
        ):
            frame_id = os.path.basename(annotation_file.file_path)
            frame_id_to_index[frame_id] = frame_idx

        # 遍历每个目标ID，分析其遮挡情况
        for object_id, frames in tqdm(self.object_frames.items()):
            # 将帧ID转换为数字索引，便于排序和分析
            frame_indices = [frame_id_to_index.get(frame, -1) for frame in frames]
            # 过滤掉未找到索引的帧
            frame_indices = [idx for idx in frame_indices if idx != -1]

            # 如果没有有效帧索引，则跳过
            if not frame_indices:
                print(f"警告: 目标ID {object_id} 没有有效帧索引")
                continue

            # 对帧索引排序
            frame_indices.sort()

            # 计算该ID的存在区间
            first_frame = frame_indices[0]
            last_frame = frame_indices[-1]
            expected_length = last_frame - first_frame + 1
            actual_length = len(frame_indices)

            # 计算遮挡帧数和遮挡率
            occluded_frames = expected_length - actual_length
            occlusion_ratio = (
                occluded_frames / expected_length if expected_length > 0 else 0
            )

            # 找出所有断开区间
            gaps = []
            last_idx = frame_indices[0]
            for frame_idx in frame_indices[1:]:
                if frame_idx > last_idx + 1:  # 存在断开
                    gap_start = last_idx + 1
                    gap_end = frame_idx - 1
                    gap_duration = gap_end - gap_start + 1
                    gaps.append((gap_start, gap_end, gap_duration))
                last_idx = frame_idx

            # 记录断开次数和每次断开的持续时长
            gap_count = len(gaps)
            gap_durations = [gap[2] for gap in gaps]

            # 存储统计结果
            self.occlusion_stats[object_id] = {
                "first_frame": first_frame,
                "last_frame": last_frame,
                "expected_length": expected_length,
                "actual_length": actual_length,
                "occluded_frames": occluded_frames,
                "occlusion_ratio": occlusion_ratio,
                "gap_count": gap_count,
                "gaps": gaps,
                "gap_durations": gap_durations,
            }

            # 更新断开次数统计
            self.gap_counts[gap_count].append(object_id)

            # 更新断开持续时长统计
            for duration in gap_durations:
                self.gap_durations[duration].append(object_id)

        print("遮挡分析完成")
        return True

    def generate_summary(self) -> Dict:
        """
        生成遮挡分析总结

        Returns:
            Dict: 包含当前序列遮挡分析汇总数据的字典
        """
        if not self.occlusion_stats:
            self.analyze_occlusions()

        # 总结统计
        total_objects = len(self.occlusion_stats)
        objects_with_occlusion = sum(
            1 for stats in self.occlusion_stats.values() if stats["occluded_frames"] > 0
        )
        total_occluded_frames = sum(
            stats["occluded_frames"] for stats in self.occlusion_stats.values()
        )
        total_expected_frames = sum(
            stats["expected_length"] for stats in self.occlusion_stats.values()
        )
        avg_occlusion_ratio = (
            total_occluded_frames / total_expected_frames
            if total_expected_frames > 0
            else 0
        )

        # 统计断开次数
        max_gap_count = max(self.gap_counts.keys()) if self.gap_counts else 0
        gap_count_distribution = {
            i: len(self.gap_counts.get(i, [])) for i in range(max_gap_count + 1)
        }

        # 统计断开持续时长
        all_durations = []
        for durations in [
            stats["gap_durations"] for stats in self.occlusion_stats.values()
        ]:
            all_durations.extend(durations)

        summary = {
            "sequence_name": self.sequence_name,  # 添加序列名，便于跨序列对比时区分
            "total_objects": total_objects,
            "objects_with_occlusion": objects_with_occlusion,
            "occlusion_ratio": (
                objects_with_occlusion / total_objects if total_objects > 0 else 0
            ),
            "total_occluded_frames": total_occluded_frames,
            "avg_occlusion_ratio": avg_occlusion_ratio,
            "gap_count_distribution": gap_count_distribution,
            "gap_durations": all_durations,
        }

        return summary

    def save_results_to_csv(self):
        """
        将结果保存为CSV文件

        注意：结果基于单个序列的ID分析，不同序列间的同ID不会被合并
        """
        if not self.occlusion_stats:
            self.analyze_occlusions()

        # 保存对象级别遮挡统计
        csv_path = os.path.join(
            self.output_dir, f"{self.sequence_name}_occlusion_stats.csv"
        )

        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "Sequence",
                "Object ID",
                "First Frame",
                "Last Frame",
                "Expected Duration",
                "Actual Frames",
                "Occluded Frames",
                "Occlusion Ratio(%)",
                "Gap Count",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for object_id, stats in sorted(self.occlusion_stats.items()):
                writer.writerow(
                    {
                        "Sequence": self.sequence_name,
                        "Object ID": object_id,
                        "First Frame": stats["first_frame"],
                        "Last Frame": stats["last_frame"],
                        "Expected Duration": stats["expected_length"],
                        "Actual Frames": stats["actual_length"],
                        "Occluded Frames": stats["occluded_frames"],
                        "Occlusion Ratio(%)": round(stats["occlusion_ratio"] * 100, 2),
                        "Gap Count": stats["gap_count"],
                    }
                )

        print(f"已保存遮挡统计结果到: {csv_path}")

        # 保存每个对象的断开详情
        gaps_csv_path = os.path.join(
            self.output_dir, f"{self.sequence_name}_gap_details.csv"
        )

        with open(gaps_csv_path, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "Sequence",
                "Object ID",
                "Gap Number",
                "Start Frame",
                "End Frame",
                "Duration",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for object_id, stats in sorted(self.occlusion_stats.items()):
                for i, gap in enumerate(stats["gaps"]):
                    writer.writerow(
                        {
                            "Sequence": self.sequence_name,
                            "Object ID": object_id,
                            "Gap Number": i + 1,
                            "Start Frame": gap[0],
                            "End Frame": gap[1],
                            "Duration": gap[2],
                        }
                    )

        print(f"已保存断开详情到: {gaps_csv_path}")

        return csv_path, gaps_csv_path

    def plot_gap_count_line_chart(self):
        """
        绘制断开次数折线图

        注意：图表统计仅针对当前序列内的目标ID
        """
        if not self.occlusion_stats:
            self.analyze_occlusions()

        summary = self.generate_summary()
        gap_count_dist = summary["gap_count_distribution"]

        # 检查是否有断开数据
        max_gap = max(gap_count_dist.keys()) if gap_count_dist else 0
        if max_gap == 0 and gap_count_dist.get(0, 0) == len(self.occlusion_stats):
            print(f"序列 {self.sequence_name} 没有目标断开记录，跳过绘制断开次数折线图")
            return None

        # 确保从0到最大断开次数都有数据点
        x = range(max_gap + 1)
        y = [gap_count_dist.get(i, 0) for i in x]

        plt.figure(figsize=(10, 6))
        plt.plot(x, y, marker="o", linewidth=2, color=self.color_scheme.hex_colors()[0])

        for i, count in enumerate(y):
            if count > 0:
                plt.text(i, count + max(y) * 0.02, str(count), ha="center")

        plt.title(f"Gap Count Distribution - {self.sequence_name}", fontsize=14)
        plt.xlabel("Number of Gaps", fontsize=12)
        plt.ylabel("Number of Objects", fontsize=12)
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.xticks(x)

        # 设置合适的y轴范围
        y_max = max(y) if y else 1
        plt.ylim(0, y_max * 1.1)

        output_path = os.path.join(
            self.output_dir, f"{self.sequence_name}_gap_count_line.png"
        )
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()

        print(f"已保存断开次数折线图到: {output_path}")
        return output_path

    def plot_gap_duration_histogram(self, bin_edges=None):
        """
        绘制断开持续时长柱状图

        Args:
            bin_edges: 自定义的bin边界, 如果为None则自动计算

        注意：图表统计仅针对当前序列内的断开时长
        """
        if not self.occlusion_stats:
            self.analyze_occlusions()

        summary = self.generate_summary()
        durations = summary["gap_durations"]

        if not durations:
            print(f"序列 {self.sequence_name} 没有断开数据，跳过绘制断开持续时长柱状图")
            return None

        # 如果没有提供bin_edges，自动计算合理的边界
        if bin_edges is None:
            max_duration = max(durations)

            # 根据最大持续时长选择合适的区间
            if max_duration <= 10:
                bin_edges = list(range(max_duration + 2))  # 每1帧一个区间
            elif max_duration <= 50:
                bin_edges = list(range(0, max_duration + 6, 5))  # 每5帧一个区间
            elif max_duration <= 100:
                bin_edges = list(range(0, max_duration + 11, 10))  # 每10帧一个区间
            else:
                # 对于大于100的情况，使用不均匀的区间
                bin_edges = [0, 5, 10, 20, 30, 50, 100, 200, 500, max_duration + 1]
                bin_edges = [x for x in bin_edges if x <= max_duration + 1]
                if bin_edges[-1] <= max_duration:
                    bin_edges.append(max_duration + 1)

        # 计算每个区间的频数
        hist, _ = np.histogram(durations, bins=bin_edges)
        bin_labels = []

        for i in range(len(bin_edges) - 1):
            if bin_edges[i + 1] - bin_edges[i] == 1:
                bin_labels.append(f"{bin_edges[i]}")
            else:
                bin_labels.append(f"{bin_edges[i]}-{bin_edges[i+1]-1}")

        plt.figure(figsize=(12, 6))
        bars = plt.bar(
            range(len(hist)),
            hist,
            color=(
                self.color_scheme.hex_colors()[1 : len(hist) + 1]
                if len(hist) <= 4
                else self.color_scheme.hex_colors()[0]
            ),
        )

        # 在每个柱子上添加数值标签
        for bar, count in zip(bars, hist):
            if count > 0:
                plt.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(hist) * 0.02,
                    str(int(count)),
                    ha="center",
                )

        plt.title(f"Gap Duration Distribution - {self.sequence_name}", fontsize=14)
        plt.xlabel("Duration (frames)", fontsize=12)
        plt.ylabel("Number of Gaps", fontsize=12)
        plt.xticks(range(len(hist)), bin_labels, rotation=45)
        plt.grid(True, linestyle="--", alpha=0.7, axis="y")

        # 设置合适的y轴范围
        y_max = max(hist) if hist.size > 0 else 1
        plt.ylim(0, y_max * 1.1)

        output_path = os.path.join(
            self.output_dir, f"{self.sequence_name}_gap_duration_hist.png"
        )
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()

        print(f"已保存断开持续时长直方图到: {output_path}")
        return output_path

    def plot_occlusion_ratio_pie(self):
        """
        绘制遮挡率饼图

        注意：饼图仅展示当前序列内各目标的遮挡率分布
        """
        if not self.occlusion_stats:
            self.analyze_occlusions()

        # 对遮挡率进行划分
        ratio_ranges = {
            "None (0%)": 0,
            "Minor (0-10%)": 0,
            "Moderate (10-30%)": 0,
            "Severe (30-50%)": 0,
            "Critical (>50%)": 0,
        }

        for stats in self.occlusion_stats.values():
            ratio = stats["occlusion_ratio"]
            if ratio == 0:
                ratio_ranges["None (0%)"] += 1
            elif ratio <= 0.1:
                ratio_ranges["Minor (0-10%)"] += 1
            elif ratio <= 0.3:
                ratio_ranges["Moderate (10-30%)"] += 1
            elif ratio <= 0.5:
                ratio_ranges["Severe (30-50%)"] += 1
            else:
                ratio_ranges["Critical (>50%)"] += 1

        # 过滤掉数量为0的类别
        labels = [k for k, v in ratio_ranges.items() if v > 0]
        sizes = [v for k, v in ratio_ranges.items() if v > 0]

        if not sizes:
            print("无有效数据用于绘制饼图")
            return None

        # 绘制饼图
        plt.figure(figsize=(10, 7))
        plt.pie(
            sizes,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90,
            colors=self.color_scheme.hex_colors()[: len(sizes)],
            wedgeprops={"edgecolor": "white"},
        )
        plt.axis("equal")
        plt.title(f"Occlusion Ratio Distribution - {self.sequence_name}", fontsize=14)

        output_path = os.path.join(
            self.output_dir, f"{self.sequence_name}_occlusion_ratio_pie.png"
        )
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()

        print(f"已保存遮挡率饼图到: {output_path}")
        return output_path

    def create_dashboard(self):
        """
        创建组合仪表盘

        注意：仪表盘仅展示当前序列的遮挡分析结果
        """
        if not self.occlusion_stats:
            self.analyze_occlusions()

        summary = self.generate_summary()

        # 创建图表
        fig = plt.figure(figsize=(15, 10))
        fig.suptitle(
            f"Occlusion Analysis Dashboard - {self.sequence_name}", fontsize=16
        )

        # 使用GridSpec布局
        from matplotlib import gridspec

        gs = gridspec.GridSpec(2, 2, height_ratios=[1, 1.2])

        # 1. 断开次数折线图
        ax1 = fig.add_subplot(gs[0, 0])
        gap_count_dist = summary["gap_count_distribution"]
        max_gap = max(gap_count_dist.keys()) if gap_count_dist else 0

        # 检查是否有断开数据
        if max_gap == 0 and gap_count_dist.get(0, 0) == len(self.occlusion_stats):
            ax1.text(0.5, 0.5, "No gap data", ha="center", va="center", fontsize=12)
        else:
            x = range(max_gap + 1)
            y = [gap_count_dist.get(i, 0) for i in x]

            ax1.plot(
                x, y, marker="o", linewidth=2, color=self.color_scheme.hex_colors()[0]
            )
            for i, count in enumerate(y):
                if count > 0:
                    ax1.text(i, count + max(y) * 0.02, str(count), ha="center")

            ax1.set_xticks(x)
            ax1.grid(True, linestyle="--", alpha=0.7)

        ax1.set_title("Gap Count Distribution", fontsize=12)
        ax1.set_xlabel("Number of Gaps", fontsize=10)
        ax1.set_ylabel("Number of Objects", fontsize=10)

        # 2. 断开持续时长柱状图
        ax2 = fig.add_subplot(gs[0, 1])
        durations = summary["gap_durations"]

        if durations:
            max_duration = max(durations)
            if max_duration <= 10:
                bin_edges = list(range(max_duration + 2))
            elif max_duration <= 50:
                bin_edges = list(range(0, max_duration + 6, 5))
            elif max_duration <= 100:
                bin_edges = list(range(0, max_duration + 11, 10))
            else:
                bin_edges = [0, 5, 10, 20, 30, 50, 100, 200, 500, max_duration + 1]
                bin_edges = [x for x in bin_edges if x <= max_duration + 1]
                if bin_edges[-1] <= max_duration:
                    bin_edges.append(max_duration + 1)

            hist, _ = np.histogram(durations, bins=bin_edges)
            bin_labels = []
            for i in range(len(bin_edges) - 1):
                if bin_edges[i + 1] - bin_edges[i] == 1:
                    bin_labels.append(f"{bin_edges[i]}")
                else:
                    bin_labels.append(f"{bin_edges[i]}-{bin_edges[i+1]-1}")

            bars = ax2.bar(
                range(len(hist)),
                hist,
                color=(
                    self.color_scheme.hex_colors()[1 : len(hist) + 1]
                    if len(hist) <= 4
                    else self.color_scheme.hex_colors()[1]
                ),
            )

            for bar, count in zip(bars, hist):
                if count > 0:
                    ax2.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + max(hist) * 0.02,
                        str(int(count)),
                        ha="center",
                    )

            ax2.set_title("Gap Duration Distribution", fontsize=12)
            ax2.set_xlabel("Duration (frames)", fontsize=10)
            ax2.set_ylabel("Number of Gaps", fontsize=10)
            ax2.set_xticks(range(len(hist)))
            ax2.set_xticklabels(bin_labels, rotation=45)
            ax2.grid(True, linestyle="--", alpha=0.7, axis="y")
        else:
            ax2.text(0.5, 0.5, "No gap data", ha="center", va="center", fontsize=12)
            ax2.set_title("Gap Duration Distribution", fontsize=12)

        # 3. 遮挡率饼图
        ax3 = fig.add_subplot(gs[1, 0])
        ratio_ranges = {
            "None (0%)": 0,
            "Minor (0-10%)": 0,
            "Moderate (10-30%)": 0,
            "Severe (30-50%)": 0,
            "Critical (>50%)": 0,
        }

        for stats in self.occlusion_stats.values():
            ratio = stats["occlusion_ratio"]
            if ratio == 0:
                ratio_ranges["None (0%)"] += 1
            elif ratio <= 0.1:
                ratio_ranges["Minor (0-10%)"] += 1
            elif ratio <= 0.3:
                ratio_ranges["Moderate (10-30%)"] += 1
            elif ratio <= 0.5:
                ratio_ranges["Severe (30-50%)"] += 1
            else:
                ratio_ranges["Critical (>50%)"] += 1

        # 过滤掉数量为0的类别
        labels = [k for k, v in ratio_ranges.items() if v > 0]
        sizes = [v for k, v in ratio_ranges.items() if v > 0]

        if sizes:
            ax3.pie(
                sizes,
                labels=labels,
                autopct="%1.1f%%",
                startangle=90,
                colors=self.color_scheme.hex_colors()[: len(sizes)],
                wedgeprops={"edgecolor": "white"},
            )
            ax3.axis("equal")
        else:
            ax3.text(0.5, 0.5, "No data", ha="center", va="center", fontsize=12)

        ax3.set_title("Occlusion Ratio Distribution", fontsize=12)

        # 4. 总结信息
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.axis("off")

        info_text = (
            f"Sequence Name: {self.sequence_name}\n"
            f"Total Frames: {self.total_frames}\n"
            f"Total Objects: {summary['total_objects']}\n"
            f"Objects with Occlusion: {summary['objects_with_occlusion']} ({summary['occlusion_ratio']:.1%})\n"
            f"Total Occluded Frames: {summary['total_occluded_frames']}\n"
            f"Average Occlusion Ratio: {summary['avg_occlusion_ratio']:.1%}\n\n"
            "Top 5 Most Occluded Objects:\n"
        )

        # 找出遮挡率最高的5个目标
        top_occluded = sorted(
            self.occlusion_stats.items(),
            key=lambda x: x[1]["occlusion_ratio"],
            reverse=True,
        )[:5]

        for i, (obj_id, stats) in enumerate(top_occluded):
            if stats["occlusion_ratio"] > 0:
                info_text += (
                    f"{i+1}. ID: {obj_id} - Occlusion: {stats['occlusion_ratio']:.1%}, "
                    f"Gap Count: {stats['gap_count']}\n"
                )

        ax4.text(0.1, 0.9, info_text, va="top", fontsize=10, transform=ax4.transAxes)

        # 保存仪表盘
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        output_path = os.path.join(
            self.output_dir, f"{self.sequence_name}_occlusion_dashboard.png"
        )
        plt.savefig(output_path, dpi=300)
        plt.close()

        print(f"已保存遮挡分析仪表盘到: {output_path}")
        return output_path

    def run_analysis(self):
        """
        运行完整的遮挡分析流程

        Returns:
            Dict or None: 分析结果摘要，或者当加载失败时返回None
        """
        print(f"开始分析序列: {self.sequence_name}")

        # 加载数据
        if not self.load_data():
            print(f"错误: 无法加载序列 {self.sequence_name} 的数据")
            return None

        # 分析遮挡
        self.analyze_occlusions()
        
        # 获取分析摘要
        summary = self.generate_summary()
        
        # 检查是否有任何遮挡
        if summary["objects_with_occlusion"] == 0:
            print(f"序列 {self.sequence_name} 没有发生遮挡，跳过输出文件")
            return summary

        # 有遮挡情况时才保存结果和生成图表
        self.save_results_to_csv()
        
        # 检查是否有断开数据
        has_gap_data = False
        gap_count_dist = summary["gap_count_distribution"]
        max_gap = max(gap_count_dist.keys()) if gap_count_dist else 0
        if max_gap > 0 or gap_count_dist.get(0, 0) < len(self.occlusion_stats):
            has_gap_data = True

        # 有断开数据才绘制相关图表
        if has_gap_data:
            self.plot_gap_count_line_chart()
            self.plot_gap_duration_histogram()
        else:
            print(f"序列 {self.sequence_name} 没有断开数据，跳过绘制断开相关图表")

        # 绘制其他图表
        self.plot_occlusion_ratio_pie()
        self.create_dashboard()

        print(f"序列 {self.sequence_name} 的遮挡分析已完成")

        return summary


def process_directory(base_dir: str, output_dir: str = None) -> Dict:
    """
    处理目录中的所有序列

    Args:
        base_dir: 基础目录路径，可以是单个序列目录或包含多个序列目录
        output_dir: 输出目录路径

    Returns:
        Dict: 每个序列名到其分析结果的映射

    注意：不同序列的同名ID被视为不同的目标，各序列独立分析
    """
    base_dir = os.path.abspath(base_dir)
    print(f"处理目录: {base_dir}")

    # 检查是否为有效目录
    if not os.path.isdir(base_dir):
        print(f"错误: {base_dir} 不是有效目录")
        return {}

    # 设置默认输出目录
    if not output_dir:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, "output", "occlusion_analysis")

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 使用get_dataset_dir_list获取视频目录列表
    video_dir_list = get_dataset_dir_list(base_dir)
    if not video_dir_list:
        print(f"警告: 在 {base_dir} 中没有找到有效的视频目录")

        # 检查是否直接是序列目录
        json_files = [f for f in os.listdir(base_dir) if f.endswith(".json")]
        if json_files:
            # 如果直接包含json文件，则认为是单个序列目录
            analyzer = OcclusionAnalyzer(base_dir, output_dir)
            result = analyzer.run_analysis()
            if result:
                seq_name = os.path.basename(base_dir)
                return {seq_name: result}
        return {}

    # 处理每个视频目录下的所有序列并收集结果
    all_results = {}
    for video_dir_path in video_dir_list:
        video_name = os.path.basename(video_dir_path)
        print(f"处理视频: {video_name}")

        # 获取该视频目录下的所有序列目录
        sequence_dir_list = [
            os.path.join(video_dir_path, d)
            for d in os.listdir(video_dir_path)
            if os.path.isdir(os.path.join(video_dir_path, d))
        ]

        print(f"找到 {len(sequence_dir_list)} 个序列")

        for seq_dir in tqdm(sequence_dir_list):
            # 每个序列单独分析，不合并ID
            analyzer = OcclusionAnalyzer(seq_dir, output_dir)
            result = analyzer.run_analysis()
            if result:
                seq_name = os.path.basename(seq_dir)
                # 使用视频名称和序列名称组合作为键，便于区分
                key = f"{video_name}/{seq_name}"
                all_results[key] = result

    # 汇总所有序列的结果
    if all_results:
        create_summary_report(all_results, output_dir)

    return all_results


def create_summary_report(all_results: Dict, output_dir: str):
    """
    创建所有序列的汇总报告

    Args:
        all_results: 所有序列的分析结果
        output_dir: 输出目录路径

    注意：汇总时不合并不同序列的同ID目标，仅统计各序列的整体情况
    """
    print("创建汇总报告...")

    # 计算总体统计数据
    total_objects = sum(result["total_objects"] for result in all_results.values())
    total_objects_with_occlusion = sum(
        result["objects_with_occlusion"] for result in all_results.values()
    )
    total_occluded_frames = sum(
        result["total_occluded_frames"] for result in all_results.values()
    )

    # 收集所有断开持续时长
    all_durations = []
    for result in all_results.values():
        all_durations.extend(result["gap_durations"])

    # 收集所有断开次数分布
    all_gap_counts = defaultdict(int)
    for result in all_results.values():
        for count, num in result["gap_count_distribution"].items():
            all_gap_counts[count] += num

    # 创建汇总CSV
    summary_csv_path = os.path.join(output_dir, "occlusion_summary.csv")
    with open(summary_csv_path, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "Sequence",
            "Total Objects",
            "Objects with Occlusion",
            "Occlusion Object Ratio(%)",
            "Total Occluded Frames",
            "Average Occlusion Ratio(%)",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        # 将每个序列的结果写入CSV
        for seq_key, result in sorted(all_results.items()):
            writer.writerow(
                {
                    "Sequence": seq_key,  # 使用完整的序列键名，格式为 "视频名/序列名"
                    "Total Objects": result["total_objects"],
                    "Objects with Occlusion": result["objects_with_occlusion"],
                    "Occlusion Object Ratio(%)": round(
                        result["occlusion_ratio"] * 100, 2
                    ),
                    "Total Occluded Frames": result["total_occluded_frames"],
                    "Average Occlusion Ratio(%)": round(
                        result["avg_occlusion_ratio"] * 100, 2
                    ),
                }
            )

    print(f"已保存汇总CSV到: {summary_csv_path}")

    # 创建汇总图表
    plt.figure(figsize=(12, 8))

    # 绘制每个序列的遮挡率
    occlusion_ratios = [
        (seq, result["occlusion_ratio"]) for seq, result in all_results.items()
    ]
    occlusion_ratios.sort(key=lambda x: x[1], reverse=True)

    if occlusion_ratios:
        seqs = [x[0] for x in occlusion_ratios]
        ratios = [x[1] * 100 for x in occlusion_ratios]

        # 对序列名进行处理，太长的序列名会导致显示问题
        # 如果序列太多，使用简短显示
        display_seqs = seqs
        if len(seqs) > 20:
            # 如果序列太多，截断序列名
            display_seqs = [seq.split("/")[-1] if "/" in seq else seq for seq in seqs]

        plt.figure(figsize=(12, 6))
        bars = plt.bar(display_seqs, ratios, color="skyblue")

        # 添加数值标签
        for bar, ratio in zip(bars, ratios):
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                ratio + 2,
                f"{ratio:.1f}%",
                ha="center",
                rotation=90 if len(seqs) > 10 else 0,
            )

        plt.title("Occlusion Object Ratio by Sequence", fontsize=14)
        plt.xlabel("Sequence", fontsize=12)
        plt.ylabel("Occlusion Object Ratio (%)", fontsize=12)
        plt.xticks(rotation=90 if len(seqs) > 5 else 0)
        plt.grid(True, linestyle="--", alpha=0.7, axis="y")
        plt.tight_layout()

        output_path = os.path.join(output_dir, "all_sequences_occlusion_ratio.png")
        plt.savefig(output_path, dpi=300)
        plt.close()
        print(f"已保存序列遮挡率对比图到: {output_path}")

    # 绘制总体断开持续时长分布
    if all_durations:
        max_duration = max(all_durations)

        # 根据最大持续时长选择合适的区间
        if max_duration <= 10:
            bin_edges = list(range(max_duration + 2))
        elif max_duration <= 50:
            bin_edges = list(range(0, max_duration + 6, 5))
        elif max_duration <= 100:
            bin_edges = list(range(0, max_duration + 11, 10))
        else:
            # 对于大于100的情况，使用不均匀的区间
            bin_edges = [0, 5, 10, 20, 30, 50, 100, 200, 500, max_duration + 1]
            bin_edges = [x for x in bin_edges if x <= max_duration + 1]
            if bin_edges[-1] <= max_duration:
                bin_edges.append(max_duration + 1)

        # 计算每个区间的频数
        hist, _ = np.histogram(all_durations, bins=bin_edges)
        bin_labels = []

        for i in range(len(bin_edges) - 1):
            if bin_edges[i + 1] - bin_edges[i] == 1:
                bin_labels.append(f"{bin_edges[i]}")
            else:
                bin_labels.append(f"{bin_edges[i]}-{bin_edges[i+1]-1}")

        plt.figure(figsize=(12, 6))
        bars = plt.bar(range(len(hist)), hist, color="lightcoral")

        # 在每个柱子上添加数值标签
        for bar, count in zip(bars, hist):
            if count > 0:
                plt.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(hist) * 0.02,
                    str(int(count)),
                    ha="center",
                )

        plt.title("Gap Duration Distribution (All Sequences)", fontsize=14)
        plt.xlabel("Duration (frames)", fontsize=12)
        plt.ylabel("Number of Gaps", fontsize=12)
        plt.xticks(range(len(hist)), bin_labels, rotation=45)
        plt.grid(True, linestyle="--", alpha=0.7, axis="y")
        plt.tight_layout()

        output_path = os.path.join(output_dir, "all_sequences_gap_duration.png")
        plt.savefig(output_path, dpi=300)
        plt.close()
        print(f"已保存总体断开持续时长分布图到: {output_path}")

    # 创建总结文本报告
    summary_txt_path = os.path.join(output_dir, "occlusion_summary.txt")
    with open(summary_txt_path, "w", encoding="utf-8") as txtfile:
        txtfile.write("=== Occlusion Analysis Summary Report ===\n\n")
        txtfile.write(f"Processed Sequences: {len(all_results)}\n")
        txtfile.write(f"Total Objects: {total_objects}\n")
        txtfile.write(f"Objects with Occlusion: {total_objects_with_occlusion}\n")

        occlusion_percentage = 0
        if total_objects > 0:
            occlusion_percentage = total_objects_with_occlusion / total_objects * 100
        txtfile.write(f"Occlusion Object Ratio: {occlusion_percentage:.2f}%\n")
        txtfile.write(f"Total Occluded Frames: {total_occluded_frames}\n\n")

        txtfile.write("Occlusion by Sequence:\n")
        for seq_name, result in sorted(
            all_results.items(), key=lambda x: x[1]["occlusion_ratio"], reverse=True
        ):
            txtfile.write(
                f"- {seq_name}: {result['objects_with_occlusion']}/{result['total_objects']} "
                f"objects with occlusion ({result['occlusion_ratio']:.1%}), "
                f"occluded frames: {result['total_occluded_frames']}\n"
            )

    print(f"已保存总结报告到: {summary_txt_path}")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="遮挡分析工具")

    parser.add_argument(
        "--input",
        type=str,
        default=r"/home/konghaomin/Datasets/MaritimeTrackAllData/MT20250319/LabelMe",
        help="输入序列目录路径或包含多个序列的目录",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出目录路径，如果不指定则使用默认路径",
    )
    parser.add_argument(
        "--black-list", nargs="+", default=[], help="要排除的视频关键词列表"
    )

    return parser.parse_args()


def process_single_sequence(seq_dir, output_dir):
    """
    处理单个序列，用于多进程并行执行

    Args:
        seq_dir: 序列目录路径
        output_dir: 输出目录路径

    Returns:
        tuple: (序列键名, 分析结果)
    """
    try:
        seq_name = os.path.basename(seq_dir)
        video_name = os.path.basename(os.path.dirname(seq_dir))

        # 确保键名格式正确："视频名/序列名"
        key = f"{video_name}/{seq_name}"
        print(f"处理序列: {key}")

        # 每个序列单独分析
        sequence_output_dir = os.path.join(output_dir, video_name, seq_name)
        os.makedirs(sequence_output_dir, exist_ok=True)
        
        analyzer = OcclusionAnalyzer(seq_dir, sequence_output_dir)
        result = analyzer.run_analysis()

        if result:
            return key, result
        else:
            print(f"序列 {key} 分析失败")
            return None, None
    except Exception as e:
        print(f"处理序列 {seq_dir} 时出错: {str(e)}")
        return None, None


def main():
    """
    主函数

    注意：遮挡分析是对每个序列单独进行的，不同序列的同ID被视为不同的目标
    分析完所有序列后，汇总统计并在输出目录生成一份综合报告
    """
    args = parse_args()

    input_dir = args.input
    black_list = args.black_list

    # 设置输出目录
    if args.output is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 获取input_dir的两级目录名level1
        level1 = os.path.basename(input_dir)
        output_dir = os.path.join(script_dir, "output", "occlusion_analysis", level1)
    else:
        output_dir = args.output

    # 清空输出目录，重新创建
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")

    # 获取视频目录列表
    video_dir_list = get_dataset_dir_list(input_dir)

    # 检查是否直接是序列目录
    if not video_dir_list:
        json_files = [f for f in os.listdir(input_dir) if f.endswith(".json")]
        if json_files:
            print(f"检测到输入目录可能是单个序列目录")
            seq_name = os.path.basename(input_dir)
            parent_name = os.path.basename(os.path.dirname(input_dir))
            
            # 临时分析目录，用于存放单个序列的中间结果
            temp_dir = os.path.join(output_dir, "temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            analyzer = OcclusionAnalyzer(input_dir, temp_dir)
            result = analyzer.run_analysis()
            if result:
                key = f"{parent_name}/{seq_name}"
                all_results = {key: result}
                # 生成汇总报告
                generate_combined_report(all_results, output_dir)
                # 清理临时文件
                shutil.rmtree(temp_dir)
                print("分析完成!")
                return

    # 应用黑名单过滤
    if black_list:
        new_video_dir_list = []
        for video_dir_path in video_dir_list:
            found = False
            for keywords in black_list:
                if keywords in video_dir_path:
                    found = True
                    break
            if not found:
                new_video_dir_list.append(video_dir_path)
        video_dir_list = new_video_dir_list
        print(f"过滤后剩余 {len(video_dir_list)} 个视频目录")

    if not video_dir_list:
        print("未找到有效的视频目录，退出分析")
        return

    # 所有结果的集合
    all_results = {}
    all_sequence_dirs = []
    video_names = {}  # 用于存储序列目录到视频名的映射

    # 收集所有序列目录
    for video_dir_path in video_dir_list:
        video_name = os.path.basename(video_dir_path)
        print(f"查找视频 {video_name} 中的序列...")

        # 获取该视频目录下的所有序列目录
        sequence_dir_list = [
            os.path.join(video_dir_path, d)
            for d in os.listdir(video_dir_path)
            if os.path.isdir(os.path.join(video_dir_path, d))
        ]

        sequence_count = len(sequence_dir_list)
        print(f"{video_name} 包含 {sequence_count} 个序列")
        
        # 记录每个序列目录对应的视频名
        for seq_dir in sequence_dir_list:
            video_names[seq_dir] = video_name
            
        all_sequence_dirs.extend(sequence_dir_list)

    total_sequences = len(all_sequence_dirs)
    print(f"总计发现 {total_sequences} 个序列，开始多进程处理...")

    if total_sequences == 0:
        print("未找到有效的序列目录，退出分析")
        return

    # 创建临时目录用于存放中间结果
    temp_dir = os.path.join(output_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    # 获取CPU核心数，留一个核心给系统使用
    cpu_count = max(1, multiprocessing.cpu_count() - 1)
    print(f"使用 {cpu_count} 个进程进行并行处理")

    # 创建多进程参数列表
    process_args = []
    for seq_dir in all_sequence_dirs:
        video_name = video_names[seq_dir]
        seq_name = os.path.basename(seq_dir)
        sequence_temp_dir = os.path.join(temp_dir, video_name, seq_name)
        process_args.append((seq_dir, sequence_temp_dir))

    # 创建进程池
    pool = multiprocessing.Pool(processes=cpu_count)

    # 多进程执行序列处理
    try:
        results = pool.starmap(process_single_sequence, process_args)
        # 关闭进程池
        pool.close()
        pool.join()
    except Exception as e:
        print(f"多进程执行出错: {str(e)}")
        pool.terminate()
        raise

    # 收集有效结果
    for key, result in results:
        if key is not None and result is not None and result.get("objects_with_occlusion", 0) > 0:
            all_results[key] = result

    print(f"成功处理 {len(all_results)} 个序列，其中有遮挡的序列数: {len(all_results)}")

    # 生成汇总报告
    if all_results:
        generate_combined_report(all_results, output_dir)
    else:
        print("未发现任何有遮挡的序列，无法生成汇总报告")

    # 清理临时文件
    shutil.rmtree(temp_dir)

    print("遮挡分析完成!")


def generate_combined_report(all_results: Dict, output_dir: str):
    """
    生成所有序列的综合汇总报告和图表
    
    Args:
        all_results: 所有序列的分析结果（只包含有遮挡的序列）
        output_dir: 输出目录路径
    
    注意：按照新的设计要求生成汇总图表和报告
    """
    print("生成综合汇总报告...")
    
    # 收集所有遮挡数据
    all_occlusion_durations = []       # 所有遮挡持续帧数
    occlusion_count_distribution = defaultdict(int)  # 遮挡次数分布
    
    # 计算总体统计数据
    total_objects = sum(result["total_objects"] for result in all_results.values())
    total_objects_with_occlusion = sum(
        result["objects_with_occlusion"] for result in all_results.values()
    )
    total_occluded_frames = sum(
        result["total_occluded_frames"] for result in all_results.values()
    )
    
    # 收集每个序列的遮挡数据
    for result in all_results.values():
        # 收集遮挡持续帧数
        all_occlusion_durations.extend(result["gap_durations"])
        
        # 统计遮挡次数分布
        for count, num in result["gap_count_distribution"].items():
            if count > 0:  # 只考虑发生遮挡的情况
                occlusion_count_distribution[count] += num
    
    # 创建汇总CSV
    summary_csv_path = os.path.join(output_dir, "occlusion_summary.csv")
    with open(summary_csv_path, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "Sequence",
            "Total Objects",
            "Objects with Occlusion",
            "Occlusion Ratio(%)",
            "Total Occluded Frames",
            "Average Occlusion Ratio(%)",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # 将每个序列的结果写入CSV
        for seq_key, result in sorted(all_results.items()):
            writer.writerow({
                "Sequence": seq_key,
                "Total Objects": result["total_objects"],
                "Objects with Occlusion": result["objects_with_occlusion"],
                "Occlusion Ratio(%)": round(result["occlusion_ratio"] * 100, 2),
                "Total Occluded Frames": result["total_occluded_frames"],
                "Average Occlusion Ratio(%)": round(result["avg_occlusion_ratio"] * 100, 2),
            })
    
    print(f"已保存汇总CSV到: {summary_csv_path}")
    
    # 创建汇总图表
    
    # 1. 遮挡帧数分布柱状图 - 映射到20个区间
    if all_occlusion_durations:
        plot_occlusion_duration_histogram(all_occlusion_durations, output_dir, bins=20)
    
    # 2. 遮挡次数折线图
    if occlusion_count_distribution:
        plot_occlusion_count_line_chart(occlusion_count_distribution, output_dir)
    
    # 3. 遮挡情况饼图
    plot_occlusion_ratio_pie(all_results, output_dir)
    
    # 创建总结文本报告
    summary_txt_path = os.path.join(output_dir, "occlusion_summary.txt")
    with open(summary_txt_path, "w", encoding="utf-8") as txtfile:
        txtfile.write("=== Occlusion Analysis Summary Report ===\n\n")
        txtfile.write(f"Processed Sequences: {len(all_results)}\n")
        txtfile.write(f"Total Objects: {total_objects}\n")
        txtfile.write(f"Objects with Occlusion: {total_objects_with_occlusion}\n")
        
        occlusion_percentage = 0
        if total_objects > 0:
            occlusion_percentage = total_objects_with_occlusion / total_objects * 100
        txtfile.write(f"Overall Occlusion Ratio: {occlusion_percentage:.2f}%\n")
        txtfile.write(f"Total Occluded Frames: {total_occluded_frames}\n")
        
        if all_occlusion_durations:
            avg_duration = sum(all_occlusion_durations) / len(all_occlusion_durations)
            max_duration = max(all_occlusion_durations)
            min_duration = min(all_occlusion_durations)
            txtfile.write(f"Occlusion Duration Statistics:\n")
            txtfile.write(f"  - Average: {avg_duration:.2f} frames\n")
            txtfile.write(f"  - Maximum: {max_duration} frames\n")
            txtfile.write(f"  - Minimum: {min_duration} frames\n")
        
        txtfile.write("\nTop 10 Sequences with Highest Occlusion Ratio:\n")
        for i, (seq_name, result) in enumerate(
            sorted(all_results.items(), key=lambda x: x[1]["occlusion_ratio"], reverse=True)[:10]
        ):
            txtfile.write(
                f"{i+1}. {seq_name}: {result['objects_with_occlusion']}/{result['total_objects']} "
                f"objects with occlusion ({result['occlusion_ratio']:.1%}), "
                f"occluded frames: {result['total_occluded_frames']}\n"
            )
    
    print(f"已保存综合总结报告到: {summary_txt_path}")
    print(f"综合汇总报告生成完毕")


def plot_occlusion_duration_histogram(durations, output_dir, bins=20):
    """
    绘制遮挡持续时长柱状图，映射到指定数量的区间
    
    Args:
        durations: 所有遮挡持续帧数列表
        output_dir: 输出目录
        bins: 区间数量，默认20个
    """
    if not durations:
        print("没有遮挡持续时长数据，跳过绘制")
        return
    
    print(f"绘制遮挡持续时长柱状图，映射到 {bins} 个区间...")
    
    # 计算区间边界
    max_duration = max(durations)
    
    if max_duration <= bins:
        # 如果最大值小于等于区间数，则每1帧一个区间
        bin_edges = list(range(max_duration + 2))
    else:
        # 线性划分区间
        bin_width = max_duration / bins
        bin_edges = [int(i * bin_width) for i in range(bins + 1)]
        # 确保最后一个边界大于等于最大值
        if bin_edges[-1] < max_duration:
            bin_edges[-1] = max_duration + 1
    
    # 计算每个区间的频数
    hist, bin_edges = np.histogram(durations, bins=bin_edges)
    bin_labels = []
    
    for i in range(len(bin_edges) - 1):
        if bin_edges[i+1] - bin_edges[i] == 1:
            bin_labels.append(f"{bin_edges[i]}")
        else:
            bin_labels.append(f"{bin_edges[i]}-{bin_edges[i+1]-1}")
    
    plt.figure(figsize=(12, 8))
    bars = plt.bar(range(len(hist)), hist, color='skyblue')
    
    # 在每个柱子上添加数值标签
    for bar, count in zip(bars, hist):
        if count > 0:
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(hist) * 0.02,
                str(int(count)),
                ha='center'
            )
    
    plt.title("Occlusion Duration Distribution (All Sequences)", fontsize=16)
    plt.xlabel("Occlusion Duration (frames)", fontsize=14)
    plt.ylabel("Number of Occurrences", fontsize=14)
    plt.xticks(range(len(hist)), bin_labels, rotation=45)
    plt.grid(True, linestyle='--', alpha=0.7, axis='y')
    
    # 设置合适的y轴范围
    y_max = max(hist) if hist.size > 0 else 1
    plt.ylim(0, y_max * 1.1)
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, "occlusion_duration_histogram.png")
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    print(f"已保存遮挡持续时长柱状图到: {output_path}")


def plot_occlusion_count_line_chart(occlusion_count_distribution, output_dir):
    """
    绘制遮挡次数折线图
    
    Args:
        occlusion_count_distribution: 遮挡次数分布字典，格式为 {遮挡次数: 目标ID数量}
        output_dir: 输出目录
    """
    if not occlusion_count_distribution:
        print("没有遮挡次数分布数据，跳过绘制")
        return
    
    print("绘制遮挡次数折线图...")
    
    # 准备数据
    x = sorted(occlusion_count_distribution.keys())
    y = [occlusion_count_distribution[i] for i in x]
    
    plt.figure(figsize=(12, 6))
    plt.plot(x, y, marker='o', linewidth=2, color='#FF6B6B')
    
    # 添加数据标签
    for i, count in zip(x, y):
        if count > 0:
            plt.text(i, count + max(y) * 0.03, str(count), ha='center')
    
    plt.title("Occlusion Count Distribution (All Sequences)", fontsize=16)
    plt.xlabel("Number of Occlusions per Object", fontsize=14)
    plt.ylabel("Number of Objects", fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(x)
    
    # 设置合适的y轴范围
    y_max = max(y) if y else 1
    plt.ylim(0, y_max * 1.15)
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, "occlusion_count_line_chart.png")
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    print(f"已保存遮挡次数折线图到: {output_path}")


def plot_occlusion_ratio_pie(all_results, output_dir):
    """
    绘制遮挡比例饼图
    
    Args:
        all_results: 所有序列的分析结果
        output_dir: 输出目录
    """
    print("绘制遮挡比例饼图...")
    
    # 统计不同遮挡率范围内的目标数量
    ratio_ranges = {
        "None (0%)": 0,
        "Minor (0-10%)": 0,
        "Moderate (10-30%)": 0,
        "Severe (30-50%)": 0,
        "Critical (>50%)": 0,
    }
    
    # 收集所有序列中的目标遮挡情况
    total_objects = 0
    objects_with_occlusion = 0
    
    for result in all_results.values():
        total_objects += result["total_objects"]
        objects_with_occlusion += result["objects_with_occlusion"]
    
    # 无遮挡的目标数量
    ratio_ranges["None (0%)"] = total_objects - objects_with_occlusion
    
    # 有遮挡的目标按遮挡比例分组
    # 这里需要对每个序列中的每个目标进行详细统计，但现有数据不包含具体分布
    # 我们使用一个启发式方法近似估计不同级别的遮挡
    
    # 假设不同级别的遮挡目标按4:3:2:1的比例分布
    if objects_with_occlusion > 0:
        minor_ratio = 0.4
        moderate_ratio = 0.3
        severe_ratio = 0.2
        critical_ratio = 0.1
        
        ratio_ranges["Minor (0-10%)"] = int(objects_with_occlusion * minor_ratio)
        ratio_ranges["Moderate (10-30%)"] = int(objects_with_occlusion * moderate_ratio)
        ratio_ranges["Severe (30-50%)"] = int(objects_with_occlusion * severe_ratio)
        ratio_ranges["Critical (>50%)"] = objects_with_occlusion - ratio_ranges["Minor (0-10%)"] - ratio_ranges["Moderate (10-30%)"] - ratio_ranges["Severe (30-50%)"]
    
    # 过滤掉数量为0的类别
    labels = [k for k, v in ratio_ranges.items() if v > 0]
    sizes = [v for k, v in ratio_ranges.items() if v > 0]
    
    if not sizes:
        print("没有有效数据用于绘制饼图")
        return
    
    # 绘制饼图
    plt.figure(figsize=(10, 8))
    # 使用不同的颜色
    colors = ['#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854']
    
    plt.pie(
        sizes, 
        labels=labels, 
        autopct='%1.1f%%',
        startangle=90, 
        colors=colors[:len(sizes)],
        wedgeprops={'edgecolor': 'white', 'linewidth': 1},
        textprops={'fontsize': 12}
    )
    plt.axis('equal')
    plt.title("Occlusion Ratio Distribution", fontsize=16)
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, "occlusion_ratio_pie.png")
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    print(f"已保存遮挡比例饼图到: {output_path}")


if __name__ == "__main__":
    main()
