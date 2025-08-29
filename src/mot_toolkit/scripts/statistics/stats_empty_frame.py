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
from typing import List
import concurrent.futures
import threading

import tqdm

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list
from mot_toolkit.datatype.dataset.object_property import ObjectSizeType
from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotationDirectory


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


# 全局变量，用于存储总计数
global_frame_count = 0
global_empty_frame_count = 0
count_lock = threading.Lock()  # 用于保护全局变量的线程锁


def handle_sequence_dir(sequence_dir_path: str) -> tuple:
    """处理序列文件夹，返回帧总数和空帧数"""
    global global_frame_count, global_empty_frame_count

    if sequence_dir_path == "":
        return 0, 0

    if not os.path.isdir(sequence_dir_path):
        return 0, 0

    annotation_directory = XAnyLabelingAnnotationDirectory()
    annotation_directory.dir_path = sequence_dir_path
    annotation_directory.walk_dir(recursive=False)
    annotation_directory.sort_path(group_directory=True)

    # 帧总数
    frame_count = len(annotation_directory.file_list)

    if frame_count == 0:
        print(f"Sequence {sequence_dir_path} has no frame!")
        return 0, 0

    annotation_directory.load_json_files()

    # 统计空帧数量
    empty_frame_count = 0

    for annotation_file in annotation_directory.annotation_file_list:
        # 如果没有矩形标注，则为空帧
        if len(annotation_file.rect_annotation_list) == 0:
            empty_frame_count += 1

    sequence_name = os.path.basename(sequence_dir_path)
    print(
        f"\t序列: {sequence_name}, 总帧数: {frame_count}, 空帧数: {empty_frame_count}"
    )

    # 使用线程锁更新全局计数
    with count_lock:
        global_frame_count += frame_count
        global_empty_frame_count += empty_frame_count

    return frame_count, empty_frame_count


if __name__ == "__main__":
    # base_path = r"H:\Datasets\MaritimeTrackAllData\LabelMe"
    # base_path = r"/mnt/h/Datasets/MaritimeTrackAllData/LabelMe"
    base_path = r"/home/konghaomin/Datasets/SMD_LabelMe"

    start_time = time.time()

    black_list = []

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

    # 使用16个线程的线程池
    max_workers = 16
    print(f"使用 {max_workers} 个线程处理序列")

    # 收集所有序列路径
    all_sequence_paths = []
    for video_dir_path in video_dir_list:
        video_name = os.path.basename(video_dir_path)
        sequence_dir_list = walk_dir_get_dir_list(video_dir_path)
        sequence_count = len(sequence_dir_list)
        print(f"视频 {video_name}, 序列数量 {sequence_count}")
        all_sequence_paths.extend(sequence_dir_list)

    print(f"总共需要处理 {len(all_sequence_paths)} 个序列")

    # 使用线程池并行处理所有序列
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(handle_sequence_dir, seq_path)
            for seq_path in all_sequence_paths
        ]

        # 使用tqdm显示进度
        for _ in tqdm.tqdm(
            concurrent.futures.as_completed(futures),
            total=len(futures),
            desc="处理进度",
        ):
            pass

    end_time = time.time()

    # 输出最终结果
    print("\n==================== 统计结果 ====================")
    print(f"总帧数: {global_frame_count}")
    print(f"空帧数: {global_empty_frame_count}")
    print(f"空帧占比: {global_empty_frame_count/global_frame_count*100:.2f}%")
    print("=================================================")

    print(f"处理时间: {round(end_time - start_time, 2)} 秒")
