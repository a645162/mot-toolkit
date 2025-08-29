"""
Part1	BV12J411V7cP-RkczpvzFD8NFWId5	00001492-00009695
该目录内含00000000.jpg与json文件，请你将该目录按照以下规则进行分割：

1492-2770
2810-3450
3510-5470
5650-7550
7590-9695
"""

import os
import shutil
import re
import concurrent.futures
from tqdm import tqdm  # 添加进度条显示


def parse_segments(segments_text):
    """
    解析需要分割的区间

    Args:
        segments_text: 包含区间的文本

    Returns:
        segments_list: 区间列表，每个区间为(start, end)的元组
    """
    segments_list = []
    for line in segments_text.strip().split("\n"):
        line = line.strip()
        if re.match(r"\d+-\d+", line):
            start, end = map(int, line.split("-"))
            segments_list.append((start, end))
    return segments_list


def copy_single_file(src_path, dst_path):
    """
    复制单个文件

    Args:
        src_path: 源文件路径
        dst_path: 目标文件路径
    """
    if os.path.exists(src_path):
        shutil.copy2(src_path, dst_path)
        return True
    return False


def copy_files_to_segment(original_dir, target_base_dir, start_frame, end_frame):
    """
    将指定区间的文件复制到新的目录

    Args:
        original_dir: 原始目录路径
        target_base_dir: 目标基础目录
        start_frame: 开始帧号
        end_frame: 结束帧号
    """
    # 创建目标目录
    segment_dir_name = f"{start_frame:08d}-{end_frame:08d}"
    target_dir = os.path.join(target_base_dir, segment_dir_name)
    if os.path.exists(target_dir):
        if os.path.isdir(target_dir):
            shutil.rmtree(target_dir)
        else:
            os.remove(target_dir)

    os.makedirs(target_dir, exist_ok=True)

    print(f"创建目录: {target_dir}")

    # 创建复制任务列表
    copy_tasks = []

    # 收集所有复制任务
    for frame in range(start_frame, end_frame + 1):
        # 处理图片文件
        img_filename = f"{frame :08d}.jpg"
        src_img_path = os.path.join(original_dir, img_filename)
        dst_img_path = os.path.join(target_dir, img_filename)
        copy_tasks.append((src_img_path, dst_img_path))

        # 处理JSON文件
        json_filename = f"{frame:08d}.json"
        src_json_path = os.path.join(original_dir, json_filename)
        dst_json_path = os.path.join(target_dir, json_filename)
        copy_tasks.append((src_json_path, dst_json_path))

    # 使用多线程执行复制任务
    successful_copies = 0
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # 提交所有复制任务
        futures = [
            executor.submit(copy_single_file, src, dst) for src, dst in copy_tasks
        ]

        # 使用tqdm显示进度
        for future in tqdm(
            concurrent.futures.as_completed(futures),
            total=len(futures),
            desc=f"复制 {segment_dir_name}",
        ):
            if future.result():
                successful_copies += 1

    faild_count = len(copy_tasks) - successful_copies

    print(
        f"分割完成: {segment_dir_name}, "
        f"成功复制 {successful_copies} 个文件, "
        f"失败 {faild_count} 个文件"
    )


def split_sequence(original_dir_path, segments_text):
    """
    根据给定的区间分割序列

    Args:
        original_dir_path: 原始文件夹路径
        segments: 区间列表，每个区间为(start, end)的元组
    """
    # 提取基础目录
    base_dir = os.path.dirname(original_dir_path)

    # 解析区间
    segments = parse_segments(segments_text)

    # 处理每个区间
    for start, end in segments:
        copy_files_to_segment(original_dir_path, base_dir, start, end)


if __name__ == "__main__":
    split_sequence(
        r"/mnt/h/Datasets/MaritimeTrackAllData/LabelMe/sea_video_20240313_part1/Onboard/BV12J411V7cP-RkczpvzFD8NFWId5/00001492-00009695",
        """
1492-2770
2810-3450
3510-5470
5650-7550
7590-9695
""",
    )

    split_sequence(
        r"/mnt/h/Datasets/MaritimeTrackAllData/LabelMe/sea_video_20240313_part3/Onshore/BV12Z4y1X79d-4qMJVY5V4y6RPxQu/00000000-00010903",
        """
        0-1950
2020-5520
5700-8400
8500-10903
""",
    )

    split_sequence(
        r"/mnt/h/Datasets/MaritimeTrackAllData/LabelMe/sea_video_20240313_part3/Onshore/BV13r4y1B7pi-dUaEwQF8UAg4b1b7/00000000-00002274",
        """
        0-1840
1870-2274
""",
    )

    split_sequence(
        r"/mnt/h/Datasets/MaritimeTrackAllData/LabelMe/sea_video_20240313_part3/Onshore/BV18a411K7At-qYyHv2ssCTHn4UA8/00002719-00005160",
        """
        2719-3500
3520-5160
""",
    )

    split_sequence(
        r"/mnt/h/Datasets/MaritimeTrackAllData/LabelMe/sea_video_20241211_night/BV1To4y1D7fJ-RcRvkaavDTJqQOjv/00000000-00003602",
        """
        0-1540
1650-3602
""",
    )

    print("所有分割任务完成!")
