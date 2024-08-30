# 视频-序列-图片
# 视频数
#     切之后的序列数
#         每个序列的帧数
#         每个序列的目标数
#         每个序列的标注目标数
import csv
import os
from typing import List, Tuple

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


def stat_count(dir_path: str) -> List[Tuple[str, str, str, str, str, str]]:
    dir_path = dir_path.strip()
    if not os.path.isdir(dir_path):
        return []

    print(dir_path)
    # 视频名称	序列数	序列名称	帧数	总目标数	类别数
    csv_ori_data_list: List[Tuple[str, str, str, str, str, str]] = []

    video_list = walk_dir_get_dir_list(dir_path)
    video_count = len(video_list)
    print("Video Count:", video_count)
    csv_ori_data_list.append((dir_path, str(video_count), "", "", "", ""))

    for video_dir_path in video_list:
        print(video_dir_path)
        video_name = os.path.basename(video_dir_path)
        sequence_list = walk_dir_get_dir_list(video_dir_path)
        sequence_count = len(sequence_list)
        print("\tSequence Count:", sequence_count)

        for sequence_dir_path in sequence_list:
            print("\t" + sequence_dir_path)
            sequence_name = os.path.basename(sequence_dir_path)

            annotation_directory = XAnyLabelingAnnotationDirectory()
            annotation_directory.dir_path = sequence_dir_path
            annotation_directory.walk_dir(recursive=False)
            annotation_directory.sort_path(group_directory=True)

            # Frame Count
            frame_count = len(annotation_directory.file_list)
            print("\t\tFrame:", frame_count)

            annotation_directory.load_json_files()

            # Class Sum(Same Tag)
            class_sum_list = annotation_directory.update_label_list()
            class_sum_count = len(class_sum_list)
            print("\t\tClass Sum:", class_sum_count)

            # Object Sum in each annotation files
            object_sum_list = []
            for annotation_file in annotation_directory.annotation_file:
                object_sum_list.append(len(annotation_file.rect_annotation_list))
            object_sum_count = sum(object_sum_list)

            print("\t\tObject Sum:", object_sum_count)

            csv_ori_data_list.append(
                (
                    video_name, str(sequence_count),
                    sequence_name,
                    str(frame_count), str(object_sum_count), str(class_sum_count)
                )
            )

    # print(csv_ori_data_list)
    return csv_ori_data_list


def save_to_csv(
        result_list: List[Tuple[str, str, str, str, str, str]],
        csv_file_path="result.csv"
):
    # 视频名称	序列数	序列名称	帧数	总目标数	类别数
    headers = [
        "Video Name", "Sequence Count",
        "Sequence Name",
        "Frame Count", "Object Count", "Class Count",
    ]

    with open(csv_file_path, "w", newline="", encoding="utf-8") as csv_file:
        # 创建 CSV 写入器
        csv_writer = csv.writer(csv_file)

        # 写入头部
        csv_writer.writerow(headers)

        # 写入列表中的数据
        for row in result_list:
            csv_writer.writerow(row)


if __name__ == "__main__":
    result_list = \
        stat_count(r"C:\Users\user\Desktop\Datasets\TrackShipOnlineVideo\sea_video_20240313_part2\OnboardTL")
    save_to_csv(result_list, "part2.csv")

    result_list = \
        stat_count(r"C:\Users\user\Desktop\Datasets\TrackShipOnlineVideo\sea_video_20240313_part4\OnshoreTL")
    save_to_csv(result_list, "part4.csv")
