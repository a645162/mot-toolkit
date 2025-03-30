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

import tqdm

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list
from mot_toolkit.datatype.dataset.object_classfication import ObjectClassConfigure
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


def get_class_config(
        base_dir: str,
        config_file_name: str = "class_config.json"
):
    config_path = os.path.join(base_dir, config_file_name)
    print("Class Config Path:", config_path)
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

        "Object Size Type",
        "Small",
        "Medium",
        "Large",
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
        resize: bool = True
) -> List:
    if sequence_dir_path == "":
        return []

    if not os.path.isdir(sequence_dir_path):
        return []

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

    if frame_count == 0:
        print(f"Sequence {sequence_dir_path} has no frame!")
        return []

    annotation_directory.load_json_files()

    width_ratio = 1
    height_ratio = 1

    if resize:
        first_file_obj = annotation_directory.annotation_file_list[0]
        image_width, image_height = first_file_obj.image_width, first_file_obj.image_height
        target_width, target_height = 640, 480
        width_ratio = target_width / image_width
        height_ratio = target_height / image_height

    id_list: List[str] = []
    object_instance_count = 0

    object_id_dict: dict = {}

    for annotation_file in annotation_directory.annotation_file_list:
        for rect_annotation in annotation_file.rect_annotation_list:
            object_instance_count += 1

            if rect_annotation.label not in id_list:
                id_list.append(rect_annotation.label)

            if rect_annotation.label not in object_id_dict.keys():
                object_id_dict[rect_annotation.label] = {}

            object_dict = object_id_dict[rect_annotation.label]
            if "object_size_type_list" not in object_dict.keys():
                object_dict["object_size_type_list"] = []
            object_size_type_list: List[ObjectSizeType] = \
                object_dict["object_size_type_list"]

            new_width = rect_annotation.width * width_ratio
            new_height = rect_annotation.height * height_ratio
            object_size_type = ObjectSizeType.get_coco_object_size_type(
                width=new_width,
                height=new_height
            )
            object_size_type_list.append(object_size_type)

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

    seq_object_size_type_list = []

    # Get most frequent object size type
    for id in object_id_dict.keys():
        object_size_type_list: List[ObjectSizeType] = \
            object_id_dict[id]["object_size_type_list"]

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
        str(size_type)
        for size_type in seq_object_size_type_list
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

    return_list.extend(class_count_list)

    print("\t\tFrame Count:", return_list[0])
    print("\t\tObject Count:", return_list[1])
    print("\t\tObject Instance Count:", return_list[2])
    print("\t\tClass Count:", return_list[3])
    print("\t\tObject Size Type:", return_list[4])
    print("\t\t\tSmall Object Count:", return_list[5])
    print("\t\t\tMedium Object Count:", return_list[6])
    print("\t\t\tLarge Object Count:", return_list[7])
    print("\t\tClass Instance Count List:")
    for idx, count in enumerate(return_list[8:]):
        print(f"\t\t\t{class_config.object_classes[idx].class_name}: {count}")

    return return_list


if __name__ == "__main__":
    base_path = r"H:\Datasets\MaritimeTrackAllData\LabelMe"
    # base_path = r"/mnt/h/Datasets/MaritimeTrackAllData/LabelMe"

    empty_line_spilt = True

    start_time = time.time()

    class_config = get_class_config(base_path)

    if class_config is None:
        print("Class Config Not Found!")
        exit(1)

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

    # print(video_dir_list)
    # input()

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

        for sequence_dir_path in tqdm.tqdm(sequence_dir_list):
            sequence_name = os.path.basename(sequence_dir_path)
            print("\t" + sequence_name)

            seq_result = handle_sequence_dir(sequence_dir_path, class_config)

            result_list.append([
                video_name, sequence_count, sequence_name,
                *seq_result
            ])

        if empty_line_spilt:
            result_list.append([])

    save_to_csv(result_list, class_config, "20250305.csv")

    end_time = time.time()

    print("Done")

    print("Time:", round(end_time - start_time, 2), "s")
