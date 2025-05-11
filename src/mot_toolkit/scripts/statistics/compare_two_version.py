"""
比较同一数据集的两个版本

用于人工优化标注后，与旧版进行对比

工作原理：
1. 同时读取两个版本的数据集，得到两个版本的数据集的文件列表
2. 对应帧的每一个ID的BBox进行比较
        对于相同的ID，每帧的BBox进行比较
                如果old版本存在，new版本不存在，则为旧版标注错误，记录为旧版标注错误
                如果old版本不存在，new版本存在，则为旧版漏标注，记录为补充标注
                如果old版本和new版本都存在，则进行BBox的比较
                        如果old版本和new版本的BBox的IoU大于0.9，则为未修改
                        如果old版本和new版本的BBox的IoU小于阈值，则为修改标注，记录为修改标注
    对于不同的ID
            如果old版本存在这个ID，new版本不存在这个ID，则为旧版标注错误，记录为旧版标注错误
        如果old版本不存在这个ID，new版本存在这个ID，则为新增标注，记录为新增标注
"""

import os
import csv
import time
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass

import numpy as np
import tqdm

from mot_toolkit.datatype.xanylabeling import (
    XAnyLabelingAnnotationDirectory,
    XAnyLabelingAnnotation,
    XAnyLabelingRect,
)
from mot_toolkit.utils.logs import get_logger

logger = get_logger()

current_py_dir_path = os.path.dirname(os.path.abspath(__file__))

# 配置路径
old_version_path = r"H:\Datasets\SMD\SMD_LabelMe_Ori"
new_version_path = r"H:\Datasets\SMD\SMD_LabelMe_Fix_20250509"

# 定义对比时使用的IoU阈值
IOU_THRESHOLD = 0.9


@dataclass
class ComparisonResult:
    """存储对比结果的数据类"""

    # 视频名称
    video_name: str = ""
    # 序列名称
    sequence_name: str = ""
    # 帧数
    frame_count: int = 0
    # 旧版ID数
    old_id_count: int = 0
    # 新版ID数
    new_id_count: int = 0
    # 相同ID数
    same_id_count: int = 0
    # 旧版删除ID数
    deleted_id_count: int = 0
    # 新版新增ID数
    added_id_count: int = 0
    # 修改的实例数
    modified_instance_count: int = 0
    # 未修改的实例数
    unmodified_instance_count: int = 0
    # 删除的实例数
    deleted_instance_count: int = 0
    # 新增的实例数
    added_instance_count: int = 0


def calculate_iou(box1: XAnyLabelingRect, box2: XAnyLabelingRect) -> float:
    """
    计算两个矩形框的IoU (Intersection over Union)

    Args:
        box1: 第一个矩形框
        box2: 第二个矩形框

    Returns:
        float: IoU值，范围为[0, 1]
    """
    # 获取两个矩形框的坐标
    x1_1, y1_1, x2_1, y2_1 = box1.get_rect_two_point_tuple_int()
    x1_2, y1_2, x2_2, y2_2 = box2.get_rect_two_point_tuple_int()

    # 计算交集区域的坐标
    x_left = max(x1_1, x1_2)
    y_top = max(y1_1, y1_2)
    x_right = min(x2_1, x2_2)
    y_bottom = min(y2_1, y2_2)

    # 如果没有交集，IoU为0
    if x_right < x_left or y_bottom < y_top:
        return 0.0

    # 计算交集面积
    intersection_area = (x_right - x_left) * (y_bottom - y_top)

    # 计算两个矩形框的面积
    box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
    box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)

    # 计算并集面积
    union_area = box1_area + box2_area - intersection_area

    # 计算IoU
    iou = intersection_area / union_area if union_area > 0 else 0.0

    return iou


def compare_annotation_files(
    old_file: XAnyLabelingAnnotation, new_file: XAnyLabelingAnnotation
) -> Dict:
    """
    比较两个标注文件的差异

    Args:
        old_file: 旧版标注文件
        new_file: 新版标注文件

    Returns:
        Dict: 包含比较结果的字典
    """
    result = {
        "modified_instances": 0,  # 修改的实例数
        "unmodified_instances": 0,  # 未修改的实例数
        "deleted_instances": 0,  # 删除的实例数
        "added_instances": 0,  # 新增的实例数
    }

    # 获取旧版和新版的ID集合
    old_ids = {rect.label for rect in old_file.rect_annotation_list}
    new_ids = {rect.label for rect in new_file.rect_annotation_list}

    # 计算相同的ID、删除的ID和新增的ID
    same_ids = old_ids.intersection(new_ids)
    deleted_ids = old_ids - new_ids
    added_ids = new_ids - old_ids

    # 对于删除的ID，增加删除实例计数
    for label in deleted_ids:
        for rect in old_file.rect_annotation_list:
            if rect.label == label:
                result["deleted_instances"] += 1

    # 对于新增的ID，增加新增实例计数
    for label in added_ids:
        for rect in new_file.rect_annotation_list:
            if rect.label == label:
                result["added_instances"] += 1

    # 对于相同的ID，比较BBox
    for label in same_ids:
        old_rects = [
            rect for rect in old_file.rect_annotation_list if rect.label == label
        ]
        new_rects = [
            rect for rect in new_file.rect_annotation_list if rect.label == label
        ]

        # 如果旧版有但新版没有，记为删除
        if len(old_rects) > len(new_rects):
            result["deleted_instances"] += len(old_rects) - len(new_rects)
        # 如果新版有但旧版没有，记为新增
        elif len(new_rects) > len(old_rects):
            result["added_instances"] += len(new_rects) - len(old_rects)

        # 比较相同ID的BBox
        for old_rect in old_rects:
            best_iou = 0
            best_match = None

            # 寻找最佳匹配的新版BBox
            for new_rect in new_rects:
                iou = calculate_iou(old_rect, new_rect)
                if iou > best_iou:
                    best_iou = iou
                    best_match = new_rect

            # 根据IoU阈值判断是否为修改的标注
            if best_iou > IOU_THRESHOLD:
                result["unmodified_instances"] += 1
            else:
                result["modified_instances"] += 1

    return result


def compare_sequence_dirs(old_seq_dir: str, new_seq_dir: str) -> ComparisonResult:
    """
    比较两个序列目录的标注差异

    Args:
        old_seq_dir: 旧版标注目录路径
        new_seq_dir: 新版标注目录路径

    Returns:
        ComparisonResult: 包含比较结果的数据类对象
    """
    # 初始化结果对象
    result = ComparisonResult()
    result.video_name = os.path.basename(os.path.dirname(old_seq_dir))
    result.sequence_name = os.path.basename(old_seq_dir)

    # 加载旧版标注目录
    old_annotation_dir = XAnyLabelingAnnotationDirectory()
    old_annotation_dir.dir_path = old_seq_dir
    old_annotation_dir.walk_dir(recursive=False)
    old_annotation_dir.sort_path(group_directory=True)
    old_annotation_dir.load_json_files()

    # 加载新版标注目录
    new_annotation_dir = XAnyLabelingAnnotationDirectory()
    new_annotation_dir.dir_path = new_seq_dir
    new_annotation_dir.walk_dir(recursive=False)
    new_annotation_dir.sort_path(group_directory=True)
    new_annotation_dir.load_json_files()

    # 统计旧版和新版的ID集合
    old_ids: Set[str] = set()
    new_ids: Set[str] = set()

    # 遍历旧版标注文件，收集所有ID
    for anno_file in old_annotation_dir.annotation_file_list:
        for rect in anno_file.rect_annotation_list:
            old_ids.add(rect.label)

    # 遍历新版标注文件，收集所有ID
    for anno_file in new_annotation_dir.annotation_file_list:
        for rect in anno_file.rect_annotation_list:
            new_ids.add(rect.label)

    # 计算相同的ID、删除的ID和新增的ID
    same_ids = old_ids.intersection(new_ids)
    deleted_ids = old_ids - new_ids
    added_ids = new_ids - old_ids

    # 更新结果对象中的ID统计
    result.old_id_count = len(old_ids)
    result.new_id_count = len(new_ids)
    result.same_id_count = len(same_ids)
    result.deleted_id_count = len(deleted_ids)
    result.added_id_count = len(added_ids)

    # 更新帧数
    result.frame_count = min(
        len(old_annotation_dir.annotation_file_list),
        len(new_annotation_dir.annotation_file_list),
    )

    # 对每一帧进行比较
    for i in range(result.frame_count):
        old_file = old_annotation_dir.annotation_file_list[i]
        new_file = new_annotation_dir.annotation_file_list[i]

        # 比较相同文件名的标注文件
        if old_file.file_name == new_file.file_name:
            comparison = compare_annotation_files(old_file, new_file)

            # 累加比较结果
            result.modified_instance_count += comparison["modified_instances"]
            result.unmodified_instance_count += comparison["unmodified_instances"]
            result.deleted_instance_count += comparison["deleted_instances"]
            result.added_instance_count += comparison["added_instances"]

    return result


def get_sequence_dirs(base_path: str) -> List[str]:
    """
    获取指定路径下的所有序列目录

    Args:
        base_path: 基础路径

    Returns:
        List[str]: 序列目录路径列表
    """
    dirs = []

    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path):
            dirs.append(item_path)

    return dirs


def save_to_csv(
    results: List[ComparisonResult], csv_file_path: str = "comparison_result.csv"
):
    """
    将比较结果保存到CSV文件

    Args:
        results: 比较结果列表
        csv_file_path: CSV文件保存路径
    """
    headers = [
        "视频名称",
        "序列名称",
        "帧数",
        "旧版ID数",
        "新版ID数",
        "相同ID数",
        "旧版删除ID数",
        "新版新增ID数",
        "修改的实例数",
        "未修改的实例数",
        "删除的实例数",
        "新增的实例数",
    ]

    # 计算总计
    total_result = ComparisonResult()
    total_result.video_name = "总计"
    total_result.sequence_name = f"{len(results)}个序列"

    # 累加所有结果
    for result in results:
        total_result.frame_count += result.frame_count
        total_result.old_id_count += result.old_id_count
        total_result.new_id_count += result.new_id_count
        total_result.same_id_count += result.same_id_count
        total_result.deleted_id_count += result.deleted_id_count
        total_result.added_id_count += result.added_id_count
        total_result.modified_instance_count += result.modified_instance_count
        total_result.unmodified_instance_count += result.unmodified_instance_count
        total_result.deleted_instance_count += result.deleted_instance_count
        total_result.added_instance_count += result.added_instance_count

    with open(csv_file_path, "w", newline="", encoding="utf-8") as csv_file:
        csv_writer = csv.writer(csv_file)

        # 写入表头
        csv_writer.writerow(headers)

        # 写入数据
        for result in results:
            row = [
                result.video_name,
                result.sequence_name,
                result.frame_count,
                result.old_id_count,
                result.new_id_count,
                result.same_id_count,
                result.deleted_id_count,
                result.added_id_count,
                result.modified_instance_count,
                result.unmodified_instance_count,
                result.deleted_instance_count,
                result.added_instance_count,
            ]
            csv_writer.writerow(row)

        # 写入总计行
        total_row = [
            total_result.video_name,
            total_result.sequence_name,
            total_result.frame_count,
            total_result.old_id_count,
            total_result.new_id_count,
            total_result.same_id_count,
            total_result.deleted_id_count,
            total_result.added_id_count,
            total_result.modified_instance_count,
            total_result.unmodified_instance_count,
            total_result.deleted_instance_count,
            total_result.added_instance_count,
        ]
        csv_writer.writerow(total_row)

    return total_result


def main():
    """主函数"""
    print(f"开始比较两个版本的数据集")
    print(f"旧版路径: {old_version_path}")
    print(f"新版路径: {new_version_path}")

    start_time = time.time()

    # 获取旧版和新版的序列目录
    old_sequence_dirs = get_sequence_dirs(old_version_path)
    new_sequence_dirs = get_sequence_dirs(new_version_path)

    # 查找两个版本中都存在的序列
    old_seq_names = [os.path.basename(d) for d in old_sequence_dirs]
    new_seq_names = [os.path.basename(d) for d in new_sequence_dirs]
    common_seq_names = set(old_seq_names).intersection(set(new_seq_names))

    print(f"共找到 {len(common_seq_names)} 个相同序列")

    # 存储比较结果
    comparison_results: List[ComparisonResult] = []

    # 比较每个序列
    for seq_name in tqdm.tqdm(common_seq_names):
        old_seq_dir = os.path.join(old_version_path, seq_name)
        new_seq_dir = os.path.join(new_version_path, seq_name)

        # 比较序列目录
        result = compare_sequence_dirs(old_seq_dir, new_seq_dir)
        comparison_results.append(result)

        # 打印序列比较结果
        print(f"\n序列: {seq_name}")
        print(f"  帧数: {result.frame_count}")
        print(f"  旧版ID数: {result.old_id_count}, 新版ID数: {result.new_id_count}")
        print(f"  相同ID数: {result.same_id_count}")
        print(
            f"  旧版删除ID数: {result.deleted_id_count}, 新版新增ID数: {result.added_id_count}"
        )
        print(f"  修改的实例数: {result.modified_instance_count}")
        print(f"  未修改的实例数: {result.unmodified_instance_count}")
        print(f"  删除的实例数: {result.deleted_instance_count}")
        print(f"  新增的实例数: {result.added_instance_count}")

    # 保存结果到CSV文件，并获取总计
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    csv_file_path = f"dataset_comparison_{timestamp}.csv"
    csv_file_path = os.path.join(current_py_dir_path, csv_file_path)
    total_result = save_to_csv(comparison_results, csv_file_path)

    # 打印总计结果
    print("\n" + "=" * 50)
    print("总计统计:")
    print(f"  总序列数: {len(comparison_results)}")
    print(f"  总帧数: {total_result.frame_count}")
    print(
        f"  总旧版ID数: {total_result.old_id_count}, 总新版ID数: {total_result.new_id_count}"
    )
    print(f"  总相同ID数: {total_result.same_id_count}")
    print(
        f"  总旧版删除ID数: {total_result.deleted_id_count}, 总新版新增ID数: {total_result.added_id_count}"
    )
    print(f"  总修改的实例数: {total_result.modified_instance_count}")
    print(f"  总未修改的实例数: {total_result.unmodified_instance_count}")
    print(f"  总删除的实例数: {total_result.deleted_instance_count}")
    print(f"  总新增的实例数: {total_result.added_instance_count}")
    print("=" * 50)

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"\n比较完成！用时 {elapsed_time:.2f} 秒")
    print(f"结果已保存到: {csv_file_path}")


if __name__ == "__main__":
    main()
