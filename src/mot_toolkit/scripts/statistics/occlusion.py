"""
遮挡分析模块

该模块用于分析多目标跟踪数据中的遮挡情况，包括:
1. 统计每个ID的遮挡帧数
2. 统计每个ID的断开次数
3. 统计每次断开的持续时长
4. 生成相关的统计图表

注意: 不同序列的ID都是从1开始，ID只在同一序列内唯一，不同序列之间的ID可能重复
多进程处理：不再为每个序列单独生成汇总报告，而是收集所有序列的数据统一生成一份综合报告
每个序列的分析结果只保存在临时目录中，最后会被清理
只关注有遮挡的序列，无遮挡的序列会被忽略
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
# from functools import partial # Not used

from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotationDirectory
from mot_toolkit.vis.scheme.genshin.sigewinne_colors import SIGEWINNEColorScheme
from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list


class OcclusionAnalyzer:
    """遮挡分析器类"""

    def __init__(self, sequence_dir: str, output_dir: str):
        """
        初始化遮挡分析器

        Args:
            sequence_dir: 序列目录路径
            output_dir: 输出目录路径 (通常是序列特定的临时目录)
        """
        self.sequence_dir = os.path.abspath(sequence_dir)
        self.sequence_name = os.path.basename(self.sequence_dir)
        self.output_dir = os.path.abspath(output_dir)

        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)

        # 初始化颜色方案
        self.color_scheme = SIGEWINNEColorScheme()

        # 数据存储
        self.object_frames = defaultdict(list)  # 每个ID出现在哪些帧
        self.occlusion_stats: Dict[str, Dict] = {}  # 存储每个ID的遮挡统计信息
        self.gap_counts = defaultdict(list)  # 存储每个ID的断开次数
        self.gap_durations = defaultdict(list)  # 存储每个ID的每次断开持续时长

        # 序列总帧数
        self.total_frames = 0

        # 已加载数据标志
        self.data_loaded = False

    def load_data(self):
        """加载序列数据"""
        # print(f"正在加载序列数据: {self.sequence_name}") # Verbose, disable for parallel
        annotation_directory = XAnyLabelingAnnotationDirectory()
        annotation_directory.dir_path = self.sequence_dir
        annotation_directory.walk_dir(recursive=False)
        annotation_directory.sort_path(group_directory=True)
        self.total_frames = len(annotation_directory.file_list)

        if self.total_frames == 0:
            # print(f"警告: 序列 {self.sequence_name} 没有帧!") # Verbose
            return False

        annotation_directory.load_json_files()
        for frame_idx, annotation_file in enumerate(
            annotation_directory.annotation_file_list
        ):
            frame_id = os.path.basename(annotation_file.file_path)
            for rect_annotation in annotation_file.rect_annotation_list:
                object_id = rect_annotation.label
                self.object_frames[object_id].append(frame_id)
        self.data_loaded = True
        return True

    def analyze_occlusions(self):
        """分析遮挡情况"""
        if not self.data_loaded:
            if not self.load_data():
                # print("无法分析遮挡: 数据加载失败") # Verbose
                return False
        # print(f"正在分析遮挡情况: {self.sequence_name}") # Verbose

        annotation_directory = XAnyLabelingAnnotationDirectory()
        annotation_directory.dir_path = self.sequence_dir
        annotation_directory.walk_dir(recursive=False)
        annotation_directory.sort_path(group_directory=True)
        annotation_directory.load_json_files()
        frame_id_to_index = {
            os.path.basename(f.file_path): idx
            for idx, f in enumerate(annotation_directory.annotation_file_list)
        }

        for object_id, frames in self.object_frames.items(): # tqdm removed for less verbose parallel
            frame_indices = sorted(
                [idx for idx in [frame_id_to_index.get(f, -1) for f in frames] if idx != -1]
            )
            if not frame_indices:
                continue

            first_frame, last_frame = frame_indices[0], frame_indices[-1]
            expected_length = last_frame - first_frame + 1
            actual_length = len(frame_indices)
            occluded_frames = expected_length - actual_length
            occlusion_ratio = (
                occluded_frames / expected_length if expected_length > 0 else 0
            )

            gaps = []
            last_idx = frame_indices[0]
            for frame_idx in frame_indices[1:]:
                if frame_idx > last_idx + 1:
                    gap_duration = frame_idx - last_idx - 1
                    gaps.append((last_idx + 1, frame_idx - 1, gap_duration))
                last_idx = frame_idx
            
            gap_count = len(gaps)
            current_gap_durations = [gap[2] for gap in gaps]

            self.occlusion_stats[object_id] = {
                "first_frame": first_frame, "last_frame": last_frame,
                "expected_length": expected_length, "actual_length": actual_length,
                "occluded_frames": occluded_frames, "occlusion_ratio": occlusion_ratio,
                "gap_count": gap_count, "gaps": gaps, "gap_durations": current_gap_durations,
            }
            self.gap_counts[gap_count].append(object_id)
            for duration in current_gap_durations:
                self.gap_durations[duration].append(object_id)
        return True

    def generate_summary(self) -> Dict:
        """生成遮挡分析总结"""
        if not self.occlusion_stats:
            if not self.analyze_occlusions(): # Ensure analysis is done
                 return { # Return empty summary if analysis fails
                    "sequence_name": self.sequence_name, "total_objects": 0,
                    "objects_with_occlusion": 0, "occlusion_ratio": 0,
                    "total_occluded_frames": 0, "avg_occlusion_ratio": 0,
                    "gap_count_distribution": {}, "gap_durations": [],
                }


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
        max_gap_count = max(self.gap_counts.keys()) if self.gap_counts else 0
        gap_count_distribution = {
            i: len(self.gap_counts.get(i, [])) for i in range(max_gap_count + 1)
        }
        all_durations = [
            dur for stats in self.occlusion_stats.values() for dur in stats["gap_durations"]
        ]
        return {
            "sequence_name": self.sequence_name, "total_objects": total_objects,
            "objects_with_occlusion": objects_with_occlusion,
            "occlusion_ratio": (
                objects_with_occlusion / total_objects if total_objects > 0 else 0
            ),
            "total_occluded_frames": total_occluded_frames,
            "avg_occlusion_ratio": avg_occlusion_ratio,
            "gap_count_distribution": gap_count_distribution,
            "gap_durations": all_durations,
        }

    def save_results_to_csv(self):
        """将结果保存为CSV文件到序列特定的输出目录"""
        if not self.occlusion_stats:
            return # Nothing to save

        csv_path = os.path.join(
            self.output_dir, f"{self.sequence_name}_occlusion_stats.csv"
        )
        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "Sequence", "Object ID", "First Frame", "Last Frame",
                "Expected Duration", "Actual Frames", "Occluded Frames",
                "Occlusion Ratio(%)", "Gap Count",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for object_id, stats in sorted(self.occlusion_stats.items()):
                writer.writerow({
                    "Sequence": self.sequence_name, "Object ID": object_id,
                    "First Frame": stats["first_frame"], "Last Frame": stats["last_frame"],
                    "Expected Duration": stats["expected_length"],
                    "Actual Frames": stats["actual_length"],
                    "Occluded Frames": stats["occluded_frames"],
                    "Occlusion Ratio(%)": round(stats["occlusion_ratio"] * 100, 2),
                    "Gap Count": stats["gap_count"],
                })

        gaps_csv_path = os.path.join(
            self.output_dir, f"{self.sequence_name}_gap_details.csv"
        )
        with open(gaps_csv_path, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "Sequence", "Object ID", "Gap Number", "Start Frame", "End Frame", "Duration",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for object_id, stats in sorted(self.occlusion_stats.items()):
                for i, gap in enumerate(stats["gaps"]):
                    writer.writerow({
                        "Sequence": self.sequence_name, "Object ID": object_id,
                        "Gap Number": i + 1, "Start Frame": gap[0],
                        "End Frame": gap[1], "Duration": gap[2],
                    })
        # print(f"序列 {self.sequence_name}: CSV结果已保存到 {self.output_dir}") # Verbose

    def plot_gap_count_line_chart(self):
        """绘制断开次数折线图到序列特定的输出目录"""
        summary = self.generate_summary()
        gap_count_dist = summary["gap_count_distribution"]
        max_gap = max(gap_count_dist.keys()) if gap_count_dist else 0
        if max_gap == 0 and gap_count_dist.get(0, 0) == len(self.occlusion_stats):
            return # No gaps

        x = range(max_gap + 1)
        y = [gap_count_dist.get(i, 0) for i in x]
        plt.figure(figsize=(10, 6))
        plt.plot(x, y, marker="o", linewidth=2, color=self.color_scheme.hex_colors()[0])
        for i, count in enumerate(y):
            if count > 0: plt.text(i, count + max(y) * 0.02, str(count), ha="center")
        plt.title(f"Gap Count Distribution - {self.sequence_name}", fontsize=14)
        plt.xlabel("Number of Gaps", fontsize=12); plt.ylabel("Number of Objects", fontsize=12)
        plt.grid(True, linestyle="--", alpha=0.7); plt.xticks(x)
        y_max = max(y) if y else 1; plt.ylim(0, y_max * 1.1)
        output_path = os.path.join(self.output_dir, f"{self.sequence_name}_gap_count_line.png")
        plt.tight_layout(); plt.savefig(output_path, dpi=300); plt.close()

    def plot_gap_duration_histogram(self, bin_edges=None):
        """绘制断开持续时长柱状图到序列特定的输出目录"""
        summary = self.generate_summary()
        durations = summary["gap_durations"]
        if not durations: return

        if bin_edges is None:
            max_duration = max(durations)
            if max_duration <= 10: bin_edges = list(range(max_duration + 2))
            elif max_duration <= 50: bin_edges = list(range(0, max_duration + 6, 5))
            elif max_duration <= 100: bin_edges = list(range(0, max_duration + 11, 10))
            else:
                bin_edges = [0, 5, 10, 20, 30, 50, 100, 200, 500, max_duration + 1]
                bin_edges = [x for x in bin_edges if x <= max_duration + 1]
                if bin_edges[-1] <= max_duration: bin_edges.append(max_duration + 1)
        
        hist, _ = np.histogram(durations, bins=bin_edges)
        bin_labels = [f"{bin_edges[i]}-{bin_edges[i+1]-1}" if bin_edges[i+1]-bin_edges[i]>1 else f"{bin_edges[i]}" for i in range(len(bin_edges)-1)]
        
        plt.figure(figsize=(12, 6))
        colors_list = self.color_scheme.hex_colors()
        bar_colors = colors_list[1:len(hist)+1] if len(hist) <= (len(colors_list)-1) else colors_list[0]
        bars = plt.bar(range(len(hist)), hist, color=bar_colors)
        for bar, count in zip(bars, hist):
            if count > 0: plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(hist)*0.02, str(int(count)), ha="center")
        plt.title(f"Gap Duration Distribution - {self.sequence_name}", fontsize=14)
        plt.xlabel("Duration (frames)", fontsize=12); plt.ylabel("Number of Gaps", fontsize=12)
        plt.xticks(range(len(hist)), bin_labels, rotation=45)
        plt.grid(True, linestyle="--", alpha=0.7, axis="y")
        y_max = max(hist) if hist.size > 0 else 1; plt.ylim(0, y_max * 1.1)
        output_path = os.path.join(self.output_dir, f"{self.sequence_name}_gap_duration_hist.png")
        plt.tight_layout(); plt.savefig(output_path, dpi=300); plt.close()

    def plot_occlusion_ratio_pie(self):
        """绘制遮挡率饼图到序列特定的输出目录"""
        ratio_ranges = {"None (0%)":0,"Minor (0-10%)":0,"Moderate (10-30%)":0,"Severe (30-50%)":0,"Critical (>50%)":0}
        for stats in self.occlusion_stats.values():
            r = stats["occlusion_ratio"]
            if r == 0: ratio_ranges["None (0%)"] += 1
            elif r <= 0.1: ratio_ranges["Minor (0-10%)"] += 1
            elif r <= 0.3: ratio_ranges["Moderate (10-30%)"] += 1
            elif r <= 0.5: ratio_ranges["Severe (30-50%)"] += 1
            else: ratio_ranges["Critical (>50%)"] += 1
        
        labels = [k for k,v in ratio_ranges.items() if v > 0]
        sizes = [v for k,v in ratio_ranges.items() if v > 0]
        if not sizes: return

        plt.figure(figsize=(10, 7))
        plt.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90, colors=self.color_scheme.hex_colors()[:len(sizes)], wedgeprops={"edgecolor":"white"})
        plt.axis("equal"); plt.title(f"Occlusion Ratio Distribution - {self.sequence_name}", fontsize=14)
        output_path = os.path.join(self.output_dir, f"{self.sequence_name}_occlusion_ratio_pie.png")
        plt.tight_layout(); plt.savefig(output_path, dpi=300); plt.close()

    def create_dashboard(self):
        """创建组合仪表盘到序列特定的输出目录"""
        summary = self.generate_summary()
        fig = plt.figure(figsize=(15, 10))
        fig.suptitle(f"Occlusion Analysis Dashboard - {self.sequence_name}", fontsize=16)
        from matplotlib import gridspec; gs = gridspec.GridSpec(2,2,height_ratios=[1,1.2])

        # Plot 1: Gap Count
        ax1 = fig.add_subplot(gs[0,0]); gap_count_dist = summary["gap_count_distribution"]
        max_gap = max(gap_count_dist.keys()) if gap_count_dist else 0
        if max_gap == 0 and gap_count_dist.get(0,0) == len(self.occlusion_stats):
            ax1.text(0.5,0.5,"No gap data",ha="center",va="center",fontsize=12)
        else:
            x = range(max_gap+1); y = [gap_count_dist.get(i,0) for i in x]
            ax1.plot(x,y,marker="o",linewidth=2,color=self.color_scheme.hex_colors()[0])
            for i,count in enumerate(y):
                if count > 0: ax1.text(i,count + max(y)*0.02,str(count),ha="center")
            ax1.set_xticks(x); ax1.grid(True,linestyle="--",alpha=0.7)
        ax1.set_title("Gap Count Distribution",fontsize=12); ax1.set_xlabel("Number of Gaps",fontsize=10); ax1.set_ylabel("Number of Objects",fontsize=10)

        # Plot 2: Gap Duration
        ax2 = fig.add_subplot(gs[0,1]); durations = summary["gap_durations"]
        if durations:
            max_d = max(durations)
            if max_d <= 10: bin_e = list(range(max_d+2))
            elif max_d <=50: bin_e = list(range(0,max_d+6,5))
            else: bin_e = [0,5,10,20,30,50,100,200,500,max_d+1]; bin_e = [x for x in bin_e if x <= max_d+1]; bin_e.append(max_d+1) if bin_e[-1] <= max_d else None
            hist, _ = np.histogram(durations, bins=bin_e)
            bin_l = [f"{bin_e[i]}-{bin_e[i+1]-1}" if bin_e[i+1]-bin_e[i]>1 else f"{bin_e[i]}" for i in range(len(bin_e)-1)]
            colors_list = self.color_scheme.hex_colors()
            bar_colors = colors_list[1:len(hist)+1] if len(hist) <= (len(colors_list)-1) else colors_list[1]
            bars = ax2.bar(range(len(hist)), hist, color=bar_colors)
            for bar,count in zip(bars,hist):
                if count > 0: ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+max(hist)*0.02, str(int(count)), ha="center")
            ax2.set_xticks(range(len(hist))); ax2.set_xticklabels(bin_l,rotation=45); ax2.grid(True,linestyle="--",alpha=0.7,axis="y")
        else: ax2.text(0.5,0.5,"No gap data",ha="center",va="center",fontsize=12)
        ax2.set_title("Gap Duration Distribution",fontsize=12); ax2.set_xlabel("Duration (frames)",fontsize=10); ax2.set_ylabel("Number of Gaps",fontsize=10)

        # Plot 3: Occlusion Ratio Pie
        ax3 = fig.add_subplot(gs[1,0]); ratio_ranges = {"None (0%)":0,"Minor (0-10%)":0,"Moderate (10-30%)":0,"Severe (30-50%)":0,"Critical (>50%)":0}
        for stats in self.occlusion_stats.values(): # Use self.occlusion_stats directly
            r = stats["occlusion_ratio"]
            if r == 0: ratio_ranges["None (0%)"] += 1
            elif r <= 0.1: ratio_ranges["Minor (0-10%)"] += 1
            elif r <= 0.3: ratio_ranges["Moderate (10-30%)"] += 1
            elif r <= 0.5: ratio_ranges["Severe (30-50%)"] += 1
            else: ratio_ranges["Critical (>50%)"] += 1
        labels = [k for k,v in ratio_ranges.items() if v > 0]; sizes = [v for k,v in ratio_ranges.items() if v > 0]
        if sizes: ax3.pie(sizes,labels=labels,autopct="%1.1f%%",startangle=90,colors=self.color_scheme.hex_colors()[:len(sizes)],wedgeprops={"edgecolor":"white"}); ax3.axis("equal")
        else: ax3.text(0.5,0.5,"No data",ha="center",va="center",fontsize=12)
        ax3.set_title("Occlusion Ratio Distribution",fontsize=12)

        # Info Text
        ax4 = fig.add_subplot(gs[1,1]); ax4.axis("off")
        info = (f"Sequence: {self.sequence_name}\nTotal Frames: {self.total_frames}\n"
                f"Total Objects: {summary['total_objects']}\nObjects w/ Occlusion: {summary['objects_with_occlusion']} ({summary['occlusion_ratio']:.1%})\n"
                f"Total Occluded Frames: {summary['total_occluded_frames']}\nAvg Occlusion Ratio: {summary['avg_occlusion_ratio']:.1%}\n\nTop 5 Occluded:\n")
        top_occ = sorted(self.occlusion_stats.items(),key=lambda x:x[1]["occlusion_ratio"],reverse=True)[:5]
        for i,(oid,s) in enumerate(top_occ):
            if s["occlusion_ratio"] > 0: info += f"{i+1}. ID {oid}: Occ {s['occlusion_ratio']:.1%}, Gaps {s['gap_count']}\n"
        ax4.text(0.1,0.9,info,va="top",fontsize=10,transform=ax4.transAxes)
        
        plt.tight_layout(rect=[0,0.03,1,0.95])
        output_path = os.path.join(self.output_dir, f"{self.sequence_name}_occlusion_dashboard.png")
        plt.savefig(output_path,dpi=300); plt.close()

    def run_analysis(self) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        运行完整的遮挡分析流程 for a single sequence.
        Saves results to self.output_dir (temp dir for the sequence).
        Returns:
            Tuple[Optional[Dict], Optional[Dict]]: (summary, self.occlusion_stats) if occlusions exist, else (None, None)
        """
        if not self.load_data(): return None, None
        if not self.analyze_occlusions(): return None, None
        
        summary = self.generate_summary()
        
        if summary["objects_with_occlusion"] == 0:
            # print(f"序列 {self.sequence_name} 没有发生遮挡，跳过输出文件到临时目录") # Verbose
            return None, None # No occlusions, return None to filter out

        # Save individual sequence results to its temp output_dir
        self.save_results_to_csv()
        
        has_gap_data = any(count > 0 for count in summary["gap_count_distribution"].values() if count != summary["gap_count_distribution"].get(0,0)) or \
                       (summary["gap_count_distribution"].get(0,0) != len(self.occlusion_stats) if self.occlusion_stats else False)


        if has_gap_data:
            self.plot_gap_count_line_chart()
            self.plot_gap_duration_histogram()
        
        self.plot_occlusion_ratio_pie() # Sequence specific pie
        self.create_dashboard()
        
        return summary, self.occlusion_stats


def process_single_sequence(args_tuple: Tuple[str, str]) -> Optional[Tuple[str, Dict, Dict]]:
    """
    处理单个序列，用于多进程并行执行.
    Args:
        args_tuple: (sequence_directory_path, sequence_temporary_output_directory_path)
    Returns:
        Optional[Tuple[str, Dict, Dict]]: (sequence_key, summary_dict, occlusion_stats_dict) if occlusions exist, else None
    """
    seq_dir, sequence_temp_dir = args_tuple
    try:
        seq_name = os.path.basename(seq_dir)
        video_name = os.path.basename(os.path.dirname(seq_dir))
        key = f"{video_name}/{seq_name}"
        # print(f"处理序列: {key}") # Verbose

        analyzer = OcclusionAnalyzer(seq_dir, sequence_temp_dir)
        summary, occlusion_stats = analyzer.run_analysis()

        if summary and occlusion_stats:
            return key, summary, occlusion_stats
        else:
            # print(f"序列 {key} 无遮挡或分析失败，将忽略") # Verbose
            return None
    except Exception as e:
        # print(f"处理序列 {seq_dir} 时出错: {e}") # Verbose
        # import traceback; traceback.print_exc() # For debugging
        return None


# --- Global Plotting Functions for Combined Report ---

def plot_global_occlusion_duration_histogram(all_durations: List[int], output_dir: str, bins: int = 20):
    """绘制全局遮挡持续时长柱状图 (映射到指定数量的区间)"""
    if not all_durations:
        print("全局：没有遮挡持续时长数据，跳过绘制柱状图")
        return
    
    print(f"全局：绘制遮挡持续时长柱状图，映射到 {bins} 个区间...")
    
    max_duration = max(all_durations) if all_durations else 0
    
    if max_duration == 0 and not all_durations: # handles empty or all zeros
        bin_edges_calc = [0, 1]
    elif max_duration <= bins:
        bin_edges_calc = list(range(int(max_duration) + 2))
    else:
        bin_width = max_duration / bins
        bin_edges_calc = [int(i * bin_width) for i in range(bins + 1)]
        if bin_edges_calc[-1] < max_duration : # Ensure last bin edge covers max_duration
             bin_edges_calc[-1] = int(max_duration) + 1
        # Remove duplicates that might arise from int conversion if bin_width is small
        bin_edges_calc = sorted(list(set(bin_edges_calc)))
        if len(bin_edges_calc) < 2 : bin_edges_calc = [0, int(max_duration)+1]


    hist, actual_bin_edges = np.histogram(all_durations, bins=bin_edges_calc)
    bin_labels = []
    for i in range(len(actual_bin_edges) - 1):
        start, end = actual_bin_edges[i], actual_bin_edges[i+1]
        if end - start == 1: bin_labels.append(f"{int(start)}")
        else: bin_labels.append(f"{int(start)}-{int(end-1)}")
    
    plt.figure(figsize=(12, 8))
    bars = plt.bar(range(len(hist)), hist, color='skyblue')
    for bar, count in zip(bars, hist):
        if count > 0: plt.text(bar.get_x()+bar.get_width()/2, bar.get_height()+max(hist)*0.02 if max(hist)>0 else 0.1, str(int(count)), ha='center')
    
    plt.title("Global Occlusion Duration Distribution", fontsize=16)
    plt.xlabel("Occlusion Duration (frames)", fontsize=14); plt.ylabel("Number of Occurrences", fontsize=14)
    plt.xticks(range(len(hist)), bin_labels, rotation=45, ha="right")
    plt.grid(True, linestyle='--', alpha=0.7, axis='y')
    y_max = max(hist) if hist.size > 0 else 1; plt.ylim(0, y_max * 1.15)
    plt.tight_layout()
    output_path = os.path.join(output_dir, "global_occlusion_duration_histogram.png")
    plt.savefig(output_path, dpi=300); plt.close()
    print(f"全局：已保存遮挡持续时长柱状图到: {output_path}")

def plot_global_occlusion_count_line_chart(aggregated_counts: Dict[int, int], output_dir: str):
    """绘制全局遮挡次数折线图"""
    if not aggregated_counts or all(v == 0 for v in aggregated_counts.values()):
        print("全局：没有遮挡次数分布数据，跳过绘制折线图")
        return
    
    print("全局：绘制遮挡次数折线图...")
    
    # Filter out count 0 if it has objects, as we are interested in "number of occlusions"
    # However, aggregated_counts should ideally be built from gap_count > 0
    # For this plot, x-axis is "Number of Occlusions", so 0 occlusions is not typically plotted.
    # If generate_combined_report ensures only counts > 0 are passed, this is fine.
    # Let's assume aggregated_counts contains counts > 0.
    
    x_coords = sorted([k for k, v in aggregated_counts.items() if v > 0]) # Only plot if objects exist for that count
    if not x_coords:
        print("全局：没有有效的遮挡次数数据点 (>0 objects)，跳过折线图")
        return

    y_coords = [aggregated_counts[i] for i in x_coords]
    
    plt.figure(figsize=(12, 6))
    plt.plot(x_coords, y_coords, marker='o', linewidth=2, color='#FF6B6B')
    for i, count_val in zip(x_coords, y_coords):
        if count_val > 0: plt.text(i, count_val + max(y_coords)*0.03 if max(y_coords)>0 else 0.1, str(count_val), ha='center')
    
    plt.title("Global Occlusion Count Distribution", fontsize=16)
    plt.xlabel("Number of Occlusions per Object", fontsize=14); plt.ylabel("Number of Objects", fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    # Ensure all plotted x_coords are shown as ticks, if too many, matplotlib might skip some.
    # For moderate numbers, this is fine. If x_coords can be very sparse or non-integer, adjust.
    plt.xticks(x_coords) 
    y_max = max(y_coords) if y_coords else 1; plt.ylim(0, y_max * 1.15)
    plt.tight_layout()
    output_path = os.path.join(output_dir, "global_occlusion_count_line_chart.png")
    plt.savefig(output_path, dpi=300); plt.close()
    print(f"全局：已保存遮挡次数折线图到: {output_path}")

def plot_global_occlusion_ratio_pie(all_object_ratios: List[float], output_dir: str):
    """绘制全局遮挡比例饼图 based on individual object occlusion ratios"""
    if not all_object_ratios:
        print("全局：没有目标遮挡率数据，跳过绘制饼图")
        return

    print("全局：绘制遮挡比例饼图...")
    
    ratio_ranges = {"None (0%)":0, "Minor (0-10%)":0, "Moderate (10-30%)":0, "Severe (30-50%)":0, "Critical (>50%)":0}
    for ratio_val in all_object_ratios:
        if ratio_val == 0: ratio_ranges["None (0%)"] += 1
        elif ratio_val <= 0.1: ratio_ranges["Minor (0-10%)"] += 1
        elif ratio_val <= 0.3: ratio_ranges["Moderate (10-30%)"] += 1
        elif ratio_val <= 0.5: ratio_ranges["Severe (30-50%)"] += 1
        else: ratio_ranges["Critical (>50%)"] += 1
            
    labels = [k for k, v in ratio_ranges.items() if v > 0]
    sizes = [v for k, v in ratio_ranges.items() if v > 0]
    
    if not sizes:
        print("全局：过滤后无有效数据用于绘制饼图")
        return
    
    plt.figure(figsize=(10, 8))
    colors = SIGEWINNEColorScheme().hex_colors() # Get fresh colors
    pie_colors = colors[:len(sizes)] if len(sizes) <= len(colors) else colors
    
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=pie_colors,
            wedgeprops={'edgecolor': 'white', 'linewidth': 1}, textprops={'fontsize': 12})
    plt.axis('equal'); plt.title("Global Object Occlusion Ratio Distribution", fontsize=16)
    plt.tight_layout()
    output_path = os.path.join(output_dir, "global_occlusion_ratio_pie.png")
    plt.savefig(output_path, dpi=300); plt.close()
    print(f"全局：已保存遮挡比例饼图到: {output_path}")


def generate_combined_report(
    processed_data: List[Tuple[str, Dict, Dict]], 
    main_output_dir: str
):
    """
    生成所有已处理序列（有遮挡的）的综合汇总报告和图表.
    Args:
        processed_data: List of (sequence_key, summary_dict, occlusion_stats_dict)
        main_output_dir: 主输出目录路径
    """
    if not processed_data:
        print("没有已处理的序列数据（或无序列发生遮挡），无法生成综合报告。")
        return

    print("生成综合汇总报告...")
    
    all_gap_durations_list: List[int] = []
    aggregated_gap_count_dist: Dict[int, int] = defaultdict(int)
    all_individual_object_ratios: List[float] = []
    
    total_summary_objects = 0
    total_summary_objects_with_occlusion = 0
    total_summary_occluded_frames = 0

    # Aggregate data from all processed sequences
    for key, summary, seq_occlusion_stats in processed_data:
        all_gap_durations_list.extend(summary.get("gap_durations", []))
        
        for count, num_objects in summary.get("gap_count_distribution", {}).items():
            if count > 0: # Only consider actual occlusion counts for the line chart
                aggregated_gap_count_dist[count] += num_objects
        
        if seq_occlusion_stats: # Should always be true if it's in processed_data
            for obj_id, stats_data in seq_occlusion_stats.items():
                all_individual_object_ratios.append(stats_data.get('occlusion_ratio', 0.0))
        
        total_summary_objects += summary.get("total_objects", 0)
        total_summary_objects_with_occlusion += summary.get("objects_with_occlusion", 0)
        total_summary_occluded_frames += summary.get("total_occluded_frames", 0)

    # Create summary CSV for sequences that had occlusions
    summary_csv_path = os.path.join(main_output_dir, "combined_occlusion_summary_sequences.csv")
    with open(summary_csv_path, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["Sequence", "Total Objects", "Objects with Occlusion", 
                      "Occlusion Object Ratio(%)", "Total Occluded Frames", "Average Occlusion Ratio(%)"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for key, summary, _ in sorted(processed_data, key=lambda x: x[1].get("occlusion_ratio",0), reverse=True):
            writer.writerow({
                "Sequence": key,
                "Total Objects": summary.get("total_objects",0),
                "Objects with Occlusion": summary.get("objects_with_occlusion",0),
                "Occlusion Object Ratio(%)": round(summary.get("occlusion_ratio",0) * 100, 2),
                "Total Occluded Frames": summary.get("total_occluded_frames",0),
                "Average Occlusion Ratio(%)": round(summary.get("avg_occlusion_ratio",0) * 100, 2),
            })
    print(f"综合报告：已保存序列汇总CSV到: {summary_csv_path}")

    # --- Call Global Plotting Functions ---
    plot_global_occlusion_duration_histogram(all_gap_durations_list, main_output_dir, bins=20)
    plot_global_occlusion_count_line_chart(aggregated_gap_count_dist, main_output_dir)
    plot_global_occlusion_ratio_pie(all_individual_object_ratios, main_output_dir)
    
    # Create summary text report
    summary_txt_path = os.path.join(main_output_dir, "combined_occlusion_summary_report.txt")
    with open(summary_txt_path, "w", encoding="utf-8") as txtfile:
        txtfile.write("=== Combined Occlusion Analysis Summary Report ===\n\n")
        txtfile.write(f"Number of Sequences Processed (with occlusions): {len(processed_data)}\n")
        txtfile.write(f"Total Objects Across These Sequences: {total_summary_objects}\n")
        txtfile.write(f"Total Objects with Any Occlusion: {total_summary_objects_with_occlusion}\n")
        
        overall_occlusion_obj_ratio = 0
        if total_summary_objects > 0:
            overall_occlusion_obj_ratio = total_summary_objects_with_occlusion / total_summary_objects * 100
        txtfile.write(f"Overall Ratio of Objects Experiencing Occlusion: {overall_occlusion_obj_ratio:.2f}%\n")
        txtfile.write(f"Total Occluded Frames Across All Objects: {total_summary_occluded_frames}\n\n")

        if all_gap_durations_list:
            avg_duration = sum(all_gap_durations_list) / len(all_gap_durations_list)
            max_d = max(all_gap_durations_list); min_d = min(all_gap_durations_list)
            txtfile.write("Occlusion Duration Statistics (across all occlusions):\n")
            txtfile.write(f"  - Average Duration: {avg_duration:.2f} frames\n")
            txtfile.write(f"  - Maximum Duration: {max_d} frames\n")
            txtfile.write(f"  - Minimum Duration: {min_d} frames\n\n")
        
        txtfile.write("Top 10 Sequences by Highest Occlusion Object Ratio:\n")
        # Sort processed_data by occlusion_ratio in summary for this listing
        sorted_sequences = sorted(processed_data, key=lambda x: x[1].get("occlusion_ratio", 0), reverse=True)
        for i, (key, summary, _) in enumerate(sorted_sequences[:10]):
            txtfile.write(
                f"{i+1}. {key}: {summary.get('objects_with_occlusion',0)}/{summary.get('total_objects',0)} "
                f"objects occluded ({summary.get('occlusion_ratio',0):.1%}), "
                f"total occluded frames: {summary.get('total_occluded_frames',0)}\n"
            )
    print(f"综合报告：已保存总结文本报告到: {summary_txt_path}")
    print("综合汇总报告生成完毕。")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="遮挡分析工具 (多进程, 综合报告)")
    parser.add_argument(
        "--input",
        type=str,
        default="/home/konghaomin/Datasets/MaritimeTrackAllData/MT20250319/LabelMe",
        help="输入数据集的基础目录路径 (例如包含多个视频文件夹的目录)",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="主输出目录路径。如果未指定，则在脚本所在目录的 'output/occlusion_analysis/DATASET_NAME' 下创建"
    )
    parser.add_argument(
        "--black-list", nargs="+", default=[], help="要排除的视频关键词列表"
    )
    parser.add_argument(
        "--processes", type=int, default=None, 
        help="使用的CPU进程数。默认使用 cpu_count //2 - 1。"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    input_base_dir = os.path.abspath(args.input)
    dataset_name = os.path.basename(input_base_dir)

    if args.output:
        main_output_dir = os.path.abspath(args.output)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        main_output_dir = os.path.join(script_dir, "output", "occlusion_analysis", dataset_name)
    
    # Temporary directory for individual sequence outputs
    temp_overall_dir = os.path.join(main_output_dir, "temp_sequence_outputs")

    # Clean and create directories
    if os.path.exists(main_output_dir): # Clean main_output_dir for a fresh run of combined report
        print(f"警告：主输出目录 {main_output_dir} 已存在，将清空其中的临时文件并重新生成报告。")
        if os.path.exists(temp_overall_dir):
             shutil.rmtree(temp_overall_dir) # Clean up previous temp if exists
    os.makedirs(main_output_dir, exist_ok=True)
    os.makedirs(temp_overall_dir, exist_ok=True)

    print(f"输入数据集目录: {input_base_dir}")
    print(f"主输出目录 (综合报告): {main_output_dir}")
    print(f"临时序列输出目录: {temp_overall_dir}")

    video_dir_list = get_dataset_dir_list(input_base_dir)

    # Apply blacklist
    if args.black_list:
        original_count = len(video_dir_list)
        video_dir_list = [
            vd for vd in video_dir_list 
            if not any(keyword in vd for keyword in args.black_list)
        ]
        print(f"应用黑名单，从 {original_count} 个视频目录过滤后剩余 {len(video_dir_list)} 个。")

    if not video_dir_list:
        # Check if input_base_dir itself is a video directory containing sequences
        # Or even a single sequence directory. This part needs robust handling.
        # For now, assume get_dataset_dir_list gives video folders.
        # If it's a single sequence, the logic might need adjustment or a different entry point.
        # The current structure is dataset -> video -> sequence.
        # If input is a video dir:
        is_video_dir = all(os.path.isdir(os.path.join(input_base_dir, item)) for item in os.listdir(input_base_dir)) and \
                       not any(item.endswith(".json") for item in os.listdir(input_base_dir)) # Heuristic
        # If input is a sequence dir:
        is_sequence_dir = any(item.endswith(".json") for item in os.listdir(input_base_dir))


        if is_sequence_dir : # input_base_dir is a single sequence directory
             print(f"检测到输入目录 {input_base_dir} 可能是一个单独的序列目录。")
             # Create a dummy video name for structure
             seq_name_for_key = os.path.basename(input_base_dir)
             parent_dir_name = os.path.basename(os.path.dirname(input_base_dir))
             dummy_video_name = parent_dir_name if parent_dir_name != dataset_name else "single_video"
             
             seq_temp_dir = os.path.join(temp_overall_dir, dummy_video_name, seq_name_for_key)
             os.makedirs(seq_temp_dir, exist_ok=True)
             
             result = process_single_sequence((input_base_dir, seq_temp_dir))
             processed_results = [result] if result else []

        elif is_video_dir: # input_base_dir is a single video directory
            print(f"检测到输入目录 {input_base_dir} 可能是一个视频目录，包含多个序列。")
            video_name = os.path.basename(input_base_dir)
            all_sequence_dirs_tasks = []
            for item in os.listdir(input_base_dir):
                seq_path = os.path.join(input_base_dir, item)
                if os.path.isdir(seq_path):
                    seq_temp_dir = os.path.join(temp_overall_dir, video_name, item)
                    all_sequence_dirs_tasks.append((seq_path, seq_temp_dir))
            
            if not all_sequence_dirs_tasks:
                print("在指定的视频目录中未找到序列子目录。")
                shutil.rmtree(temp_overall_dir) # Clean up empty temp
                return
            
            cpu_to_use = args.processes if args.processes else max(1, multiprocessing.cpu_count() - 1)
            print(f"开始处理 {len(all_sequence_dirs_tasks)} 个序列，使用 {cpu_to_use} 个进程...")
            with multiprocessing.Pool(processes=cpu_to_use) as pool:
                results_from_pool = list(tqdm(pool.imap(process_single_sequence, all_sequence_dirs_tasks), total=len(all_sequence_dirs_tasks), desc="处理序列"))
            processed_results = [r for r in results_from_pool if r is not None]
        else:
            print(f"在 {input_base_dir} 中没有找到有效的视频目录或序列。请检查输入路径。")
            shutil.rmtree(temp_overall_dir)
            return

    else: # Standard case: dataset_dir -> video_dirs -> sequence_dirs
        all_sequence_dirs_tasks: List[Tuple[str, str]] = []
        for video_dir_path in video_dir_list:
            video_name = os.path.basename(video_dir_path)
            sequence_subdirs = [
                d for d in os.listdir(video_dir_path) 
                if os.path.isdir(os.path.join(video_dir_path, d))
            ]
            for seq_subdir_name in sequence_subdirs:
                seq_dir_path = os.path.join(video_dir_path, seq_subdir_name)
                # Define sequence-specific temporary output directory
                sequence_temp_output_dir = os.path.join(temp_overall_dir, video_name, seq_subdir_name)
                all_sequence_dirs_tasks.append((seq_dir_path, sequence_temp_output_dir))

        if not all_sequence_dirs_tasks:
            print("未找到任何序列进行分析。")
            shutil.rmtree(temp_overall_dir) # Clean up empty temp
            return

        total_sequences_to_process = len(all_sequence_dirs_tasks)
        cpu_to_use = args.processes if args.processes else max(1, multiprocessing.cpu_count() // 2 - 1)
        print(f"总计发现 {total_sequences_to_process} 个序列，开始使用 {cpu_to_use} 个进程进行并行处理...")

        with multiprocessing.Pool(processes=cpu_to_use) as pool:
            # Use imap for progress with tqdm, starmap if args were tuples of multiple items
            # process_single_sequence now takes a single tuple argument
            results_from_pool = list(tqdm(pool.imap(process_single_sequence, all_sequence_dirs_tasks), total=total_sequences_to_process, desc="处理序列"))
        
        # Filter out None results (sequences with no occlusions or errors)
        processed_results = [r for r in results_from_pool if r is not None]


    print(f"所有序列处理完成。有效（有遮挡的）序列数量: {len(processed_results)}")

    if processed_results:
        generate_combined_report(processed_results, main_output_dir)
    else:
        print("没有序列发生遮挡或所有序列处理失败，不生成综合报告。")

    # Clean up the temporary directory for individual sequence outputs
    try:
        print(f"清理临时文件目录: {temp_overall_dir}")
        shutil.rmtree(temp_overall_dir)
    except Exception as e:
        print(f"清理临时文件时出错: {e}")

    print("遮挡分析全部完成!")


if __name__ == "__main__":
    # Example Usage:
    # python occlusion.py --input /path/to/your/dataset --output /path/to/your/output_reports
    # Ensure matplotlib backend is suitable for non-interactive use if running in headless environment
    # import matplotlib
    # matplotlib.use('Agg') 
    main()
