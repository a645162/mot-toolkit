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
from typing import List

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list
from mot_toolkit.datatype.dataset.object_classfication import ObjectClassConfigure
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


def get_class_config(base_dir: str):
    config_path = os.path.join(base_dir, "class_config.json")
    return ObjectClassConfigure.create_by_configure_file(config_path)


def save_to_csv(
        result_list: List,
        class_config: ObjectClassConfigure,
        csv_file_path="result.csv"
):
    # 视频名称	序列数	序列名称	帧数	总目标数	类别数
    headers = [
        "Video Name", "Sequence Count",
        "Sequence Name",
        "Frame Count",
        "Object Count", "Object Instance Count",
        "Class Count",
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
        class_config: ObjectClassConfigure
) -> List:
    return_list = []

    class_count_list: List[int] = [
        0 for _ in range(len(class_config.object_classes))
    ]

    annotation_directory = XAnyLabelingAnnotationDirectory()
    annotation_directory.dir_path = sequence_dir_path
    annotation_directory.walk_dir(recursive=False)
    annotation_directory.sort_path(group_directory=True)

    # Frame Count
    frame_count = len(annotation_directory.file_list)

    annotation_directory.load_json_files()

    id_list: List[str] = []
    object_instance_count = 0
    for annotation_file in annotation_directory.annotation_file_list:
        for rect_annotation in annotation_file.rect_annotation_list:
            object_instance_count += 1

            if rect_annotation.label not in id_list:
                id_list.append(rect_annotation.label)

            # Stats Class Count
            for obj_class in class_config.object_classes:
                if obj_class.class_id == rect_annotation.group_id:
                    class_count_list[class_config.object_classes.index(obj_class)] += 1
                    break

    # Find not 0 class count
    class_count_list_no_zero = [
        count
        for count in class_count_list
        if count != 0
    ]
    class_count = len(class_count_list_no_zero)

    return_list.append(frame_count)
    return_list.append(len(id_list))
    return_list.append(object_instance_count)
    return_list.append(class_count)
    return_list.extend(class_count_list)

    print("\t\tFrame Count:", return_list[0])
    print("\t\tObject Count:", return_list[1])
    print("\t\tObject Instance Count:", return_list[2])
    print("\t\tClass Count:", return_list[3])
    print("\t\tClass Instance Count List:")
    for idx, count in enumerate(return_list[4:]):
        print(f"\t\t\t{class_config.object_classes[idx].class_name}: {count}")

    return return_list


if __name__ == "__main__":
    base_path = r"H:\Datasets\TrackShipOnlineVideo\LabelMe"

    class_config = get_class_config(base_path)

    result_list: List = []

    black_list = [
        "BV14S4y147jX-t5PTpDLBGiSESMzw"
    ]

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

    # video_dir_list = [
    #     path
    #     for path in video_dir_list
    #     if ("part1" not in path) and ("part2" not in path) and ("part3" not in path)
    # ]
    for video_dir_path in video_dir_list:
        video_name = os.path.basename(video_dir_path)

        sequence_dir_list = walk_dir_get_dir_list(video_dir_path)
        sequence_count = len(sequence_dir_list)
        print(video_name, sequence_count)

        for sequence_dir_path in sequence_dir_list:
            sequence_name = os.path.basename(sequence_dir_path)
            print("\t" + sequence_name)

            seq_result = handle_sequence_dir(sequence_dir_path, class_config)

            result_list.append([
                video_name, sequence_count, sequence_name,
                *seq_result
            ])

        result_list.append([])

    save_to_csv(result_list, class_config, "result.csv")

    print("Done")
