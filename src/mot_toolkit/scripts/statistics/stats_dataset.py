# 视频-序列-图片
# 视频数
#     切之后的序列数
#         每个序列的帧数
#         每个序列的目标数(ID数)
#         每个序列的标注目标数(实例数)
#           每个序列的类别数(有几类目标)
#           每个分类的目标数(每个类别的实例数)
import csv
import os
import time
import math
from typing import List, Dict

import tqdm
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list
from mot_toolkit.datatype.dataset.object_classfication import ObjectClassConfigure
from mot_toolkit.datatype.dataset.object_property import ObjectSizeType
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


def walk_dir_get_dir_list(dir_path: str) -> List[str]:
    dir_path = dir_path.strip()

    if dir_path == "":
        return []

    dir_path = os.path.abspath(dir_path)

    dir_list = []
    # Not include child directory

    for dir_name in os.listdir(dir_path):
        dir_path_tmp = os.path.join(dir_path, dir_name)
        if os.path.isdir(dir_path_tmp):
            dir_list.append(dir_path_tmp)

    return dir_list


def get_class_config(base_dir: str, config_file_name: str = "class_config.json"):
    config_path = os.path.join(base_dir, config_file_name)
    print("Class Config Path:", config_path)
    return ObjectClassConfigure.create_by_configure_file(config_path)


def calculate_ocpmd(
    x1_prev,
    y1_prev,
    x2_prev,
    y2_prev,
    x1_curr,
    y1_curr,
    x2_curr,
    y2_curr,
    img_width,
    img_height,
):
    """
    计算两帧之间目标中心点的移动距离 (OCPMD)
    使用归一化坐标来计算，避免因图像尺寸不同而导致的不一致

    Args:
        x1_prev, y1_prev, x2_prev, y2_prev: 前一帧的目标边界框坐标
        x1_curr, y1_curr, x2_curr, y2_curr: 当前帧的目标边界框坐标
        img_width, img_height: 图像尺寸

    Returns:
        float: 归一化后的中心点移动距离
    """
    # 计算前一帧的中心点归一化坐标
    center_x_prev = (x1_prev + x2_prev) / (2 * img_width)
    center_y_prev = (y1_prev + y2_prev) / (2 * img_height)

    # 计算当前帧的中心点归一化坐标
    center_x_curr = (x1_curr + x2_curr) / (2 * img_width)
    center_y_curr = (y1_curr + y2_curr) / (2 * img_height)

    # 计算欧几里得距离
    ocpmd = math.sqrt(
        (center_x_curr - center_x_prev) ** 2 + (center_y_curr - center_y_prev) ** 2
    )
    return ocpmd


def save_to_csv(
    result_list: List, class_config: ObjectClassConfigure, csv_file_path="result.csv"
):
    # 视频名称	序列数	序列名称	帧数	总目标数	类别数
    headers = [
        "Video Name",
        "Sequence Count",
        "Sequence Name",
        "Frame Count",
        "Object Count",
        "Object Instance Count",
        "Class Count",
        "Object Size Type",
        "Small",
        "Medium",
        "Large",
        "Trimmed Sum OCPMD",  # 修改列名，表示去除极值后的累计OCPMD
        "Valid AOCPMD Object Count",  # 有效的AOCPMD目标数量
        "Static Object Count (<T)",  # 静止目标数量
        "Moving Object Count (>=T)",  # 移动目标数量
        "Static BBox Count",  # 静止目标BBox数量
        "Static BBox Ratio (%)",  # 静止目标BBox占比
        "Moving Target Avg Movement",  # 移动目标平均移动距离
    ]

    # Append Class Title
    for obj_class in class_config.object_classes:
        headers.append(f"[{obj_class.class_id}] {obj_class.class_name}")

    with open(csv_file_path, "w", newline="", encoding="utf-8") as csv_file:
        # 创建 CSV 写入器
        csv_writer = csv.writer(csv_file)

        # 写入头部
        csv_writer.writerow(headers)

        # 写入列表中的数据
        for row in result_list:
            while len(row) < len(headers):
                row.append("")

            csv_writer.writerow(row)


def handle_sequence_dir(
    sequence_dir_path: str,
    class_config: ObjectClassConfigure,
    resize: bool = True,
    ocpmd_threshold: float = 0.01,  # 静止目标的AOCPMD阈值
    collect_movement_data: Dict = None,  # 收集全局移动数据的字典
) -> List:
    if sequence_dir_path == "":
        return []

    if not os.path.isdir(sequence_dir_path):
        return []

    return_list = []

    class_count_list: List[int] = [0 for _ in range(len(class_config.object_classes))]

    annotation_directory = XAnyLabelingAnnotationDirectory()
    annotation_directory.dir_path = sequence_dir_path
    annotation_directory.walk_dir(recursive=False)
    annotation_directory.sort_path(group_directory=True)

    # Frame Count
    frame_count = len(annotation_directory.file_list)

    if frame_count == 0:
        print(f"Sequence {sequence_dir_path} has no frame!")
        return []

    annotation_directory.load_json_files()

    width_ratio = 1
    height_ratio = 1

    if resize:
        first_file_obj = annotation_directory.annotation_file_list[0]
        image_width, image_height = (
            first_file_obj.image_width,
            first_file_obj.image_height,
        )
        target_width, target_height = 640, 480
        width_ratio = target_width / image_width
        height_ratio = target_height / image_height

    id_list: List[str] = []
    object_instance_count = 0

    object_id_dict: Dict[str, Dict] = {}

    # 用于跟踪每个目标的位置历史
    object_position_history: Dict[str, List[Dict]] = {}

    # 记录每个目标出现的帧数
    object_frame_counts = {}

    # 遍历所有标注文件（按时间顺序）
    for frame_idx, annotation_file in enumerate(
        annotation_directory.annotation_file_list
    ):
        img_width, img_height = (
            annotation_file.image_width,
            annotation_file.image_height,
        )

        for rect_annotation in annotation_file.rect_annotation_list:
            object_id = rect_annotation.label
            object_instance_count += 1

            if object_id not in id_list:
                id_list.append(object_id)

            # 统计每个目标的帧数
            if object_id not in object_frame_counts:
                object_frame_counts[object_id] = 0
            object_frame_counts[object_id] += 1

            if object_id not in object_id_dict.keys():
                object_id_dict[object_id] = {}
                object_position_history[object_id] = []

            object_dict = object_id_dict[object_id]
            if "object_size_type_list" not in object_dict.keys():
                object_dict["object_size_type_list"] = []
            object_size_type_list: List[ObjectSizeType] = object_dict[
                "object_size_type_list"
            ]

            new_width = rect_annotation.width * width_ratio
            new_height = rect_annotation.height * height_ratio
            object_size_type = ObjectSizeType.get_coco_object_size_type(
                width=new_width, height=new_height
            )
            object_size_type_list.append(object_size_type)

            # Stats Class Count
            for obj_class in class_config.object_classes:
                if obj_class.class_id == rect_annotation.group_id:
                    class_count_list[class_config.object_classes.index(obj_class)] += 1
                    break

            # 记录当前帧中目标的位置信息
            object_position_history[object_id].append(
                {
                    "frame_idx": frame_idx,
                    "x1": rect_annotation.x1,
                    "y1": rect_annotation.y1,
                    "x2": rect_annotation.x2,
                    "y2": rect_annotation.y2,
                }
            )

    # 计算每个目标的OCPMD值
    ocpmd_values: Dict[str, List[float]] = {}
    for obj_id, positions in object_position_history.items():
        # 按帧索引排序
        positions.sort(key=lambda x: x["frame_idx"])

        # 初始化当前目标的OCPMD列表
        ocpmd_values[obj_id] = []

        # 计算连续帧之间的OCPMD
        for i in range(1, len(positions)):
            prev_pos = positions[i - 1]
            curr_pos = positions[i]

            # 检查是否为连续帧
            if curr_pos["frame_idx"] - prev_pos["frame_idx"] == 1:
                ocpmd = calculate_ocpmd(
                    prev_pos["x1"],
                    prev_pos["y1"],
                    prev_pos["x2"],
                    prev_pos["y2"],
                    curr_pos["x1"],
                    curr_pos["y1"],
                    curr_pos["x2"],
                    curr_pos["y2"],
                    img_width,
                    img_height,
                )
                ocpmd_values[obj_id].append(ocpmd)

    # 计算每个目标的AOCPMD
    aocpmd_values: Dict[str, float] = {}
    valid_aocpmd_list = []
    static_object_count = 0
    moving_object_count = 0

    for obj_id, ocpmds in ocpmd_values.items():
        if len(ocpmds) > 0:
            aocpmd = sum(ocpmds) / len(ocpmds)
            aocpmd_values[obj_id] = aocpmd
            valid_aocpmd_list.append(aocpmd)

            # 将AOCPMD值添加到目标字典中
            object_id_dict[obj_id]["aocpmd"] = aocpmd

            # 计算累计移动距离
            object_id_dict[obj_id]["total_movement"] = sum(ocpmds)

            # 收集全局移动数据
            if collect_movement_data is not None:
                global_id = f"{sequence_dir_path}_{obj_id}"
                collect_movement_data[global_id] = sum(ocpmds)

    # 计算去除极值后的累计OCPMD
    sequence_aocpmd_sum = 0
    if len(valid_aocpmd_list) > 2:  # 确保有足够的数据
        sorted_aocpmd = sorted(valid_aocpmd_list)
        # 去掉前后各5%的值
        trim_count = int(len(sorted_aocpmd) * 0.05)
        if trim_count < 1:
            trim_count = 1  # 至少去掉一个值

        # 去除前后极值后的列表
        trimmed_aocpmd = sorted_aocpmd[trim_count : len(sorted_aocpmd) - trim_count]

        if trimmed_aocpmd:
            sequence_aocpmd_sum = sum(trimmed_aocpmd)
    elif valid_aocpmd_list:  # 如果数据太少，则使用所有数据
        sequence_aocpmd_sum = sum(valid_aocpmd_list)

    # 根据累计移动距离判断静止和运动目标
    static_object_ids = []  # 记录所有静止目标的ID
    moving_object_ids = []  # 记录所有移动目标的ID
    for obj_id in object_id_dict:
        if "total_movement" in object_id_dict[obj_id]:
            total_movement = object_id_dict[obj_id]["total_movement"]
            # 使用阈值判断静止和运动目标
            if total_movement >= ocpmd_threshold:
                moving_object_count += 1
                moving_object_ids.append(obj_id)
            else:
                static_object_count += 1
                static_object_ids.append(obj_id)  # 添加到静止目标列表

    # 计算移动目标的平均移动距离
    moving_target_avg_movement = 0.0
    if moving_object_ids:
        total_moving_distance = sum(
            object_id_dict[obj_id]["total_movement"] for obj_id in moving_object_ids
        )
        moving_target_avg_movement = total_moving_distance / len(moving_object_ids)

    # 计算静止目标的总BBox数
    static_bbox_count = 0
    for obj_id in static_object_ids:
        if obj_id in object_frame_counts:
            static_bbox_count += object_frame_counts[obj_id]

    # 计算静止目标BBox数占总BBox数(实例数)的比例
    static_bbox_ratio = (
        static_bbox_count / object_instance_count if object_instance_count > 0 else 0
    )

    # 计算静止目标的总帧数
    static_object_frame_count = 0
    for obj_id in static_object_ids:
        if obj_id in object_frame_counts:
            static_object_frame_count += object_frame_counts[obj_id]

    # 计算静止目标帧数占总帧数的比例
    total_object_frame_count = sum(object_frame_counts.values())
    static_frame_ratio = (
        static_object_frame_count / total_object_frame_count
        if total_object_frame_count > 0
        else 0
    )

    # 将静止目标信息添加到目标字典中
    for obj_id in static_object_ids:
        object_id_dict[obj_id]["is_static"] = True
        object_id_dict[obj_id]["frame_count"] = object_frame_counts.get(obj_id, 0)

    # Find not 0 class count
    class_count_list_no_zero = [count for count in class_count_list if count != 0]
    class_count = len(class_count_list_no_zero)

    seq_object_size_type_list = []

    # Get most frequent object size type
    for id in object_id_dict.keys():
        object_size_type_list: List[ObjectSizeType] = object_id_dict[id][
            "object_size_type_list"
        ]

        type_list: List[ObjectSizeType] = list(set(object_size_type_list))

        type_dict = {}
        for type in type_list:
            count = object_size_type_list.count(type)
            type_dict[type.name] = count

        max_key = max(type_dict, key=type_dict.get)

        max_type = ObjectSizeType[max_key]

        object_id_dict[id]["object_size_type"] = max_type

        if max_type not in seq_object_size_type_list:
            seq_object_size_type_list.append(max_type)

    # # Sort By Value
    # object_size_type_list.sort(key=lambda x: int(x))

    object_size_type_str_list = [
        str(size_type) for size_type in seq_object_size_type_list
    ]
    object_size_type_str = ",".join(object_size_type_str_list).strip()

    count_small = 0
    count_medium = 0
    count_large = 0

    for id in object_id_dict.keys():
        object_size_type: ObjectSizeType = object_id_dict[id]["object_size_type"]
        if object_size_type == ObjectSizeType.SMALL:
            count_small += 1
        elif object_size_type == ObjectSizeType.MEDIUM:
            count_medium += 1
        elif object_size_type == ObjectSizeType.LARGE:
            count_large += 1

    return_list.append(frame_count)
    return_list.append(len(id_list))
    return_list.append(object_instance_count)
    return_list.append(class_count)

    return_list.append(object_size_type_str)
    return_list.append(count_small)
    return_list.append(count_medium)
    return_list.append(count_large)

    # 添加OCPMD相关统计数据
    return_list.append(round(sequence_aocpmd_sum, 6))  # 序列累计OCPMD值（去除极值后）
    return_list.append(len(valid_aocpmd_list))  # 有效AOCPMD计算的目标数
    return_list.append(static_object_count)  # 静止目标数量
    return_list.append(moving_object_count)  # 移动目标数量

    # 添加静止目标相关统计
    return_list.append(static_object_frame_count)  # 静止目标帧数
    return_list.append(round(static_frame_ratio * 100, 2))  # 静止目标帧数占比(%)
    return_list.append(static_bbox_count)  # 静止目标BBox数
    return_list.append(round(static_bbox_ratio * 100, 2))  # 静止目标BBox占比(%)
    return_list.append(round(moving_target_avg_movement, 6))  # 移动目标平均移动距离

    return_list.extend(class_count_list)

    print("\t\tFrame Count:", return_list[0])
    print("\t\tObject Count:", return_list[1])
    print("\t\tObject Instance Count:", return_list[2])
    print("\t\tClass Count:", return_list[3])
    print("\t\tObject Size Type:", return_list[4])
    print("\t\t\tSmall Object Count:", return_list[5])
    print("\t\t\tMedium Object Count:", return_list[6])
    print("\t\t\tLarge Object Count:", return_list[7])
    print("\t\tTrimmed Sum OCPMD:", return_list[8])
    print("\t\tValid AOCPMD Object Count:", return_list[9])
    print("\t\tStatic Object Count", f"(<{ocpmd_threshold}):", return_list[10])
    print("\t\tMoving Object Count", f"(>={ocpmd_threshold}):", return_list[11])
    print("\t\tStatic Object Frame Count:", static_object_frame_count)
    print("\t\tStatic Frame Ratio:", f"{static_frame_ratio * 100:.2f}%")
    print(
        f"\t\tStatic BBox Count: {static_bbox_count} / {object_instance_count} ({static_bbox_ratio*100:.2f}%)"
    )
    print(
        f"\t\tMoving Target Average Movement Distance: {moving_target_avg_movement:.6f}"
    )

    if class_config.object_classes:
        print("\t\tClass Instance Count List:")
        for idx, count in enumerate(
            return_list[17:]  # 索引调整为17，因为增加了移动目标平均移动距离字段
        ):
            if idx < len(class_config.object_classes):  # 添加边界检查
                print(
                    f"\t\t\t[{idx}] {class_config.object_classes[idx].class_name}: {count}"
                )

    return return_list


def plot_movement_histogram(
    movement_data: Dict,
    output_path: str,
    ocpmd_threshold: float,
    additional_title: bool = False,
):
    """
    绘制目标移动特性的分布直方图

    Args:
        movement_data: 包含目标ID和总移动距离的字典
        output_path: 输出图像的路径
        ocpmd_threshold: 静止/移动目标的阈值
    """
    # 设置绘图样式
    setup_plot_style()

    # 提取移动数据值
    movement_values = list(movement_data.values())

    # 确保数据不为空
    if not movement_values:
        print("警告: 没有移动数据可供绘图")
        return

    # 创建图形
    plt.figure(figsize=(12, 8))

    # 获取希格雯配色方案
    color_scheme = SIGEWINNEColorScheme()

    # 按亮度排序获取颜色（从浅到深，反序）
    sorted_colors_rgb = color_scheme.get_sorted_colors_by_brightness(reverse=True)
    sorted_colors = [f"#{r:02x}{g:02x}{b:02x}".upper() for r, g, b in sorted_colors_rgb]

    # 计算数据的最大值和最小值
    max_value = max(movement_values)
    min_value = min(movement_values)

    # 设置直方图区间，从0到数据最大值，分成100个区间
    if max_value < 1:
        bins = np.linspace(0, 1, 101)
    else:
        max_bin = math.ceil(max_value) + 0.5
        bins = np.linspace(0, max_bin, 101)

    # 绘制直方图
    n, bins, patches = plt.hist(
        movement_values, bins=bins, alpha=0.7, edgecolor="black"
    )

    # 定义固定的区间边界
    # 区间1: [0, 0.1)        - 颜色1（浅色）
    # 区间2: [0.1, 0.5)      - 颜色2
    # 区间3: [0.5, 1.0)      - 颜色3
    # 区间4: [1.0, 1.5)      - 颜色4
    # 区间5: [1.5, +∞)       - 颜色5（深色）
    interval_boundaries = [0, 0.1, 0.5, 1.0, 1.5, float("inf")]

    # 为每个柱子分配颜色：根据bin的中心值所在的区间
    for i, patch in enumerate(patches):
        # 获取当前bin的中心值
        bin_center = (bins[i] + bins[i + 1]) / 2

        # 判断bin_center属于哪个区间
        color_idx = 0
        for j in range(len(interval_boundaries) - 1):
            if interval_boundaries[j] <= bin_center < interval_boundaries[j + 1]:
                color_idx = j
                break

        # 确保索引不越界
        color_idx = min(color_idx, len(sorted_colors) - 1)
        color_idx = max(color_idx, 0)

        patch.set_facecolor(sorted_colors[color_idx])

    # 标记静止/移动阈值 - 使用大红色和更粗的线
    plt.axvline(
        x=ocpmd_threshold,
        color="red",
        linestyle="--",
        linewidth=3,
        label=f"Static/Moving Threshold ({ocpmd_threshold})",
        alpha=0.9,
    )

    # 计算静止和移动的比例
    static_count = sum(1 for v in movement_values if v < ocpmd_threshold)
    moving_count = len(movement_values) - static_count
    static_percent = static_count / len(movement_values) * 100 if movement_values else 0
    moving_percent = moving_count / len(movement_values) * 100 if movement_values else 0

    # 添加数据范围信息
    avg_value = sum(movement_values) / len(movement_values)

    # 添加标题和标签 - 使用英文替代中文
    additional_title_text = (
        (
            "\n"
            f"Static Objects (<{ocpmd_threshold}): {static_count} ({static_percent:.1f}%)\n"
            f"Moving Objects (≥{ocpmd_threshold}): {moving_count} ({moving_percent:.1f}%)\n"
            f"Range: [{min_value:.4f}, {max_value:.4f}], Avg: {avg_value:.4f}"
        )
        if additional_title
        else ""
    )
    # plt.title(
    #     "Object Movement Distribution Histogram" + additional_title_text,
    #     fontsize=14,
    # )

    plt.xlabel("Normalized Cumulative Movement Distance", fontsize=12)
    plt.ylabel("Object Count", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend(handlelength=2.0, handletextpad=0.8)

    # 保存图像
    plt.savefig(output_path, dpi=300, bbox_inches="tight")

    # Save svg
    svg_output_path = output_path.replace(".png", ".svg")
    plt.savefig(svg_output_path, format="svg", bbox_inches="tight")

    # Save eps
    eps_output_path = output_path.replace(".png", ".eps")
    plt.savefig(eps_output_path, format="eps", bbox_inches="tight")

    plt.close()

    print(f"已保存移动特性分布直方图到: {output_path}")
    print(f"移动距离范围: [{min_value:.4f}, {max_value:.4f}], 平均: {avg_value:.4f}")
    print(
        f"使用了 {len(sorted_colors)} 种颜色，划分为 {len(interval_boundaries) - 1} 个固定区间"
    )

    # 打印区间信息
    print("颜色区间划分:")
    interval_labels = [
        "[0, 0.1) (静止目标区间)",
        "[0.1, 0.5)",
        "[0.5, 1.0)",
        "[1.0, 1.5)",
        "[1.5, +∞)",
    ]
    for j in range(min(len(interval_labels), len(sorted_colors))):
        print(f"\t区间 {j+1}: {interval_labels[j]} -> 颜色 {sorted_colors[j]}")


def output_summary(
    result_list: List,
    class_config: ObjectClassConfigure,
    all_movement_data: Dict,
    ocpmd_threshold: float,
    total_static_bbox_count: int,
    total_bbox_count: int,
    max_frame_info: Dict,  # 新增参数：最长帧数信息
    output_txt_path: str = None,
) -> str:
    """
    输出数据集统计的总结信息，并可选择保存到文本文件

    Args:
        result_list: 包含所有序列统计结果的列表
        class_config: 类别配置对象
        all_movement_data: 目标移动数据字典
        ocpmd_threshold: 静止目标阈值
        total_static_bbox_count: 静止目标BBox总数
        total_bbox_count: BBox总数
        max_frame_info: 最长帧数信息字典
        output_txt_path: 输出文本文件路径，如果为None则不保存

    Returns:
        str: 总结信息文本
    """
    # 计算并打印总计统计信息
    total_frame_count = 0
    total_object_count = 0
    total_object_instance_count = 0
    total_small_count = 0
    total_medium_count = 0
    total_large_count = 0
    total_static_object_count = 0
    total_moving_object_count = 0

    # 每个类别的总数
    total_class_counts = [0 for _ in range(len(class_config.object_classes))]

    # 统计有效行（跳过空行）
    valid_sequences = 0

    for row in result_list:
        if not row:  # 跳过空行
            continue

        valid_sequences += 1

        # 帧数在索引3，目标数在索引4，实例数在索引5
        total_frame_count += row[3] if len(row) > 3 and isinstance(row[3], int) else 0
        total_object_count += row[4] if len(row) > 4 and isinstance(row[4], int) else 0
        total_object_instance_count += (
            row[5] if len(row) > 5 and isinstance(row[5], int) else 0
        )

        # 小、中、大目标数量在索引8, 9, 10
        total_small_count += row[8] if len(row) > 8 and isinstance(row[8], int) else 0
        total_medium_count += row[9] if len(row) > 9 and isinstance(row[9], int) else 0
        total_large_count += (
            row[10] if len(row) > 10 and isinstance(row[10], int) else 0
        )

        # 静止和移动目标数在索引13, 14
        total_static_object_count += (
            row[13] if len(row) > 13 and isinstance(row[13], int) else 0
        )
        total_moving_object_count += (
            row[14] if len(row) > 14 and isinstance(row[14], int) else 0
        )

        # 各类别目标数从索引17开始
        for i in range(len(total_class_counts)):
            idx = 17 + i
            if len(row) > idx and isinstance(row[idx], int):
                total_class_counts[i] += row[idx]

    # 生成总结文本
    summary_lines = []
    summary_lines.append("=" * 60)
    summary_lines.append("总计统计:")
    summary_lines.append("=" * 60)
    summary_lines.append(f"总序列数: {valid_sequences}")
    summary_lines.append(f"总帧数: {total_frame_count}")
    summary_lines.append(f"最长序列帧数: {max_frame_info['max_frames']}")
    summary_lines.append(
        f"最长序列: {max_frame_info['video_name']} / {max_frame_info['sequence_name']}"
    )
    summary_lines.append(f"总目标数: {total_object_count}")
    summary_lines.append(f"总实例数: {total_object_instance_count}")
    summary_lines.append("目标尺寸分布:")
    summary_lines.append(f"\t小目标: {total_small_count}")
    summary_lines.append(f"\t中目标: {total_medium_count}")
    summary_lines.append(f"\t大目标: {total_large_count}")
    summary_lines.append("目标运动特性:")
    summary_lines.append(f"\t静止目标(<{ocpmd_threshold}): {total_static_object_count}")
    summary_lines.append(
        f"\t移动目标(>={ocpmd_threshold}): {total_moving_object_count}"
    )
    summary_lines.append(f"\t静止BBox数: {total_static_bbox_count}")
    summary_lines.append(f"\t总BBox数: {total_bbox_count}")

    static_bbox_ratio = "0.00%"
    if total_bbox_count > 0:
        static_bbox_ratio = f"{total_static_bbox_count/total_bbox_count*100:.2f}%"
    summary_lines.append(f"\t静止BBox占比: {static_bbox_ratio}")

    # 如果有类别配置且类别列表不为空，才输出类别统计
    if class_config and class_config.object_classes:
        summary_lines.append("各类别目标数量:")
        for idx, count in enumerate(total_class_counts):
            summary_lines.append(
                f"\t[{idx}] {class_config.object_classes[idx].class_name}: {count}"
            )
    else:
        summary_lines.append("已跳过类别统计.")
    summary_lines.append("=" * 60)

    # 在总计统计中添加更多关于移动特性的详情
    if all_movement_data:
        movement_values = list(all_movement_data.values())
        static_objects = [v for v in movement_values if v < ocpmd_threshold]
        moving_objects = [v for v in movement_values if v >= ocpmd_threshold]

        # 计算各种数量，避免重复调用 len()
        total_obj_count = len(movement_values)
        static_obj_count = len(static_objects)
        moving_obj_count = len(moving_objects)

        # 计算百分比
        static_percent = (
            static_obj_count / total_obj_count * 100 if total_obj_count else 0
        )
        moving_percent = (
            moving_obj_count / total_obj_count * 100 if total_obj_count else 0
        )

        summary_lines.append("移动特性详细统计:")
        summary_lines.append(f"\t目标总数: {total_obj_count}")
        summary_lines.append(
            f"\t静止目标(<{ocpmd_threshold}): {static_obj_count} ({static_percent:.2f}%)"
        )
        summary_lines.append(
            f"\t移动目标(>={ocpmd_threshold}): {moving_obj_count} ({moving_percent:.2f}%)"
        )

        if moving_objects:
            summary_lines.append(
                f"\t移动目标平均移动距离: {sum(moving_objects)/moving_obj_count:.4f}"
            )
            summary_lines.append(f"\t移动目标最大移动距离: {max(moving_objects):.4f}")
            summary_lines.append(f"\t移动目标最小移动距离: {min(moving_objects):.4f}")

        summary_lines.append(f"\t静止BBox总数: {total_static_bbox_count}")
        static_bbox_ratio_text = "0.00%"
        if total_bbox_count > 0:
            static_bbox_ratio_text = (
                f"{total_static_bbox_count/total_bbox_count*100:.2f}%"
            )
        summary_lines.append(f"\t静止BBox占比: {static_bbox_ratio_text}")

        if static_obj_count > 0:
            summary_lines.append(
                f"\t每个静止目标平均BBox数: {total_static_bbox_count/static_obj_count:.2f}"
            )
        if moving_obj_count > 0:
            summary_lines.append(
                f"\t每个移动目标平均BBox数: {(total_bbox_count-total_static_bbox_count)/moving_obj_count:.2f}"
            )

    # 将总结信息合并为字符串
    summary_text = "\n".join(summary_lines)

    # 打印总结信息
    print("\n" + summary_text)

    # 如果提供了输出路径，则保存到文本文件
    if output_txt_path:
        with open(output_txt_path, "w", encoding="utf-8") as f:
            f.write(summary_text)
        print(f"已将总结信息保存到: {output_txt_path}")

    return summary_text


def plot_sequence_moving_avg_distance(
    result_list: List, output_path: str, top_n: int = 20
):
    """
    绘制序列移动目标平均移动距离的柱状图

    Args:
        result_list: 序列结果列表
        output_path: 输出路径
        top_n: 显示前N个序列
    """
    # 提取有效序列数据 (video_name, sequence_name, moving_avg_distance)
    sequence_data = []
    for row in result_list:
        if not row or len(row) < 17:  # 跳过空行或数据不完整的行
            continue

        video_name = row[0]
        sequence_name = row[2]
        moving_avg_distance = row[16] if isinstance(row[16], (int, float)) else 0.0

        # 只包含有移动距离的序列
        if moving_avg_distance > 0:
            sequence_data.append((video_name, sequence_name, moving_avg_distance))

    if not sequence_data:
        print("Warning: No valid sequences with moving target average distance > 0")
        return

    # 按移动距离排序并取前top_n个
    sequence_data.sort(key=lambda x: x[2], reverse=True)
    if len(sequence_data) > top_n:
        sequence_data = sequence_data[:top_n]

    # 提取数据用于绘图
    # data[0]: 视频名称
    # data[1]: 序列名称
    # 暂时不使用data[0]
    sequence_labels = [f"{data[1]}" for data in sequence_data]
    # sequence_labels = [f"{data[0]}_{data[1]}" for data in sequence_data]

    moving_distances = [data[2] for data in sequence_data]

    # 设置绘图样式
    setup_plot_style()

    plt.figure(figsize=(20, 10))

    # 获取希格雯配色
    color_scheme = SIGEWINNEColorScheme()
    colors = color_scheme.hex_colors()

    # 创建柱状图，每个柱子交替使用希格雯配色
    bar_colors = [colors[i % len(colors)] for i in range(len(sequence_labels))]
    bars = plt.bar(
        range(len(sequence_labels)),
        moving_distances,
        alpha=0.7,
        color=bar_colors,
        edgecolor="black",
    )

    # 设置x轴标签 (旋转45度以避免重叠)
    plt.xticks(range(len(sequence_labels)), sequence_labels, rotation=45, ha="right")

    # 添加数值标签到柱子顶部
    for i, bar in enumerate(bars):
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + height * 0.01,
            f"{height:.4f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    # 计算统计信息
    mean_distance = np.mean(moving_distances)
    plt.axhline(
        y=mean_distance,
        color=colors[0],
        linestyle="--",
        linewidth=2,
        label=f"Mean Distance: {mean_distance:.4f}",
    )

    # plt.title(
    #     f"Top {len(sequence_data)} Sequences by Moving Target Average Movement Distance",
    #     fontsize=16,
    # )
    plt.xlabel("Sequence (Video_Sequence)", fontsize=12)
    plt.ylabel("Average Movement Distance", fontsize=12)
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

    print(f"Moving target average distance bar chart saved to: {output_path}")
    print(
        f"Statistics - Mean: {mean_distance:.6f}, Max: {max(moving_distances):.6f}, Min: {min(moving_distances):.6f}"
    )


def parse_args():
    """
    解析命令行参数
    """
    import argparse

    parser = argparse.ArgumentParser(description="生成数据集统计信息")

    # H:\Datasets\MaritimeTrackAllData\LabelMe
    # H:\Datasets\SMD\SMD_LabelMe_Fix_20250509
    parser.add_argument(
        "--base-path",
        type=str,
        default=r"/home/konghaomin/Datasets/MaritimeTrackAllData/MT20250319/LabelMe",
        help="数据集基础路径",
    )
    parser.add_argument(
        "--output-csv", type=str, default="dataset_stats.csv", help="输出CSV文件路径"
    )
    parser.add_argument(
        "--config-file", type=str, default="class_config.json", help="类别配置文件名"
    )
    parser.add_argument(
        "--ocpmd-threshold", type=float, default=0.1, help="静止目标的AOCPMD阈值"
    )
    parser.add_argument(
        "--empty-line-split",
        action="store_true",
        default=True,
        help="在CSV中不同视频之间添加空行",
    )
    parser.add_argument(
        "--black-list",
        nargs="+",
        default=["BV14S4y147jX-t5PTpDLBGiSESMzw"],
        help="要排除的视频关键词列表",
    )
    parser.add_argument(
        "--skip-class-stats",
        action="store_true",
        help="跳过类别统计，即使未找到类别配置文件也不退出",
    )

    parser.add_argument(
        "--movement-hist",
        type=str,
        default="movement_histogram.png",
        help="移动特性分布直方图输出路径",
    )
    parser.add_argument(
        "--moving-avg-bar",
        type=str,
        default="moving_avg_distance_bar.png",
        help="移动目标平均移动距离柱状图输出路径",
    )

    # 开关
    parser.add_argument(
        "--additional-title",
        action="store_true",
        help="在输出的图表标题中添加额外信息",
    )

    opt = parser.parse_args()

    # opt.base_path = r"/home/konghaomin/Datasets/SMD_LabelMe_Fix_20250509"
    # opt.base_path = r"H:\Datasets\MaritimeTrackAllData\LabelMe"
    # opt.base_path = r"H:\Datasets\SMD\SMD_LabelMe_Fix_20250509"
    opt.base_path = r"/home/konghaomin/Datasets/SMD_LabelMe_Ori"
    # opt.base_path = r"/home/konghaomin/Datasets/MaritimeTrackAllData/MT20250319/LabelMe_Ocean"

    return opt


def main():
    """
    主函数，处理参数并运行统计功能
    """
    args = parse_args()

    base_path = os.path.abspath(args.base_path)
    output_csv = args.output_csv
    config_file_name = args.config_file
    ocpmd_threshold = args.ocpmd_threshold
    empty_line_spilt = args.empty_line_split
    black_list = args.black_list
    skip_class_stats = args.skip_class_stats
    movement_hist_path = args.movement_hist
    moving_avg_bar_path = args.moving_avg_bar

    # 输出目录为当前py目录
    output_dir_path = os.path.dirname(os.path.abspath(__file__))

    output_dir_path = os.path.join(output_dir_path, "output")
    output_dir_path = os.path.join(output_dir_path, "stats_dataset")

    # 获取base_path的两级目录名level1
    level1 = os.path.basename(base_path)
    level2 = os.path.basename(os.path.dirname(base_path))

    # 拼接输出目录路径
    output_dir_path = os.path.join(output_dir_path, level1, level2)
    if not os.path.exists(output_dir_path):
        os.makedirs(output_dir_path, exist_ok=True)

    # 确保所有输出文件保存到output_dir_path目录
    output_csv_path = os.path.join(output_dir_path, output_csv)
    movement_hist_output_path = os.path.join(output_dir_path, movement_hist_path)
    moving_avg_bar_output_path = os.path.join(output_dir_path, moving_avg_bar_path)
    output_txt_path = os.path.join(output_dir_path, "results_summary.txt")

    # 用于收集所有序列中目标的移动数据
    all_movement_data = {}

    # 记录总的静止目标信息
    total_static_object_frame_count = 0
    total_object_frame_count = 0
    total_static_bbox_count = 0
    total_bbox_count = 0  # 总BBox数

    # 记录最长帧数信息
    max_frame_info = {
        'max_frames': 0,
        'video_name': '',
        'sequence_name': ''
    }

    start_time = time.time()

    # 尝试获取类别配置，如果指定跳过类别统计则允许配置为None
    class_config = get_class_config(base_path, config_file_name)

    if class_config is None or skip_class_stats:
        print("警告: 类别配置文件未找到，将跳过类别统计。")
        # 创建一个空的配置对象以避免空引用错误
        class_config = ObjectClassConfigure()
        class_config.object_classes = []
    else:
        class_config.sort()

    result_list: List = []

    video_dir_list = get_dataset_dir_list(base_path)

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

    for video_dir_path in video_dir_list:
        video_name = os.path.basename(video_dir_path)

        sequence_dir_list = walk_dir_get_dir_list(video_dir_path)
        sequence_count = len(sequence_dir_list)
        print(video_name, sequence_count)

        for sequence_dir_path in tqdm.tqdm(sequence_dir_list):
            sequence_name = os.path.basename(sequence_dir_path)
            print("\t" + sequence_name)

            seq_result = handle_sequence_dir(
                sequence_dir_path,
                class_config,
                ocpmd_threshold=ocpmd_threshold,
                collect_movement_data=all_movement_data,  # 传入收集数据的字典
            )

            # 更新最长帧数记录
            if len(seq_result) > 0 and isinstance(seq_result[0], int):
                current_frames = seq_result[0]
                if current_frames > max_frame_info['max_frames']:
                    max_frame_info['max_frames'] = current_frames
                    max_frame_info['video_name'] = video_name
                    max_frame_info['sequence_name'] = sequence_name

            # 累加静止目标帧数统计
            if len(seq_result) > 15 and isinstance(seq_result[14], int):  # 静止目标帧数
                total_static_object_frame_count += seq_result[14]

            # 累加总目标帧数
            if len(seq_result) > 5 and isinstance(
                seq_result[5], int
            ):  # 实例数(总bbox数)
                total_object_frame_count += seq_result[5]

            # 累加静止目标BBox数统计
            if len(seq_result) > 14 and isinstance(
                seq_result[14], int
            ):  # 静止目标BBox数
                total_static_bbox_count += seq_result[14]

            # 累加总BBox数
            if len(seq_result) > 2 and isinstance(
                seq_result[2], int
            ):  # object_instance_count
                total_bbox_count += seq_result[2]

            result_list.append([video_name, sequence_count, sequence_name, *seq_result])

        if empty_line_spilt:
            result_list.append([])

    save_to_csv(result_list, class_config, output_csv_path)

    # 绘制移动特性分布直方图
    if all_movement_data:
        plot_movement_histogram(
            all_movement_data,
            movement_hist_output_path,
            ocpmd_threshold,
            args.additional_title,
        )

    # 绘制移动目标平均移动距离柱状图
    plot_sequence_moving_avg_distance(result_list, moving_avg_bar_output_path)

    # 输出总结统计信息并保存到文本文件
    output_summary(
        result_list,
        class_config,
        all_movement_data,
        ocpmd_threshold,
        total_static_bbox_count,
        total_bbox_count,
        max_frame_info,  # 传入最长帧数信息
        output_txt_path,
    )

    end_time = time.time()

    print(f"已将CSV文件保存到: {output_csv_path}")
    print(f"已将移动特性分布直方图保存到: {movement_hist_output_path}")
    print(f"已将移动目标平均距离柱状图保存到: {moving_avg_bar_output_path}")
    print("完成")

    print("耗时:", round(end_time - start_time, 2), "秒")


if __name__ == "__main__":
    main()
