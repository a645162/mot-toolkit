import os

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list


def stat_jpg(original_dir):
    """
    统计jpg文件数量
    Args:
        original_dir: 原始目录路径
    """
    # 创建目标目录
    jpg_count = 0
    for root, dirs, files in os.walk(original_dir):
        for file in files:
            if file.endswith(".jpg"):
                jpg_count += 1

    return jpg_count


def main():
    keyword = "LabelMe"

    base_dir = r"/mnt/h/Datasets/MaritimeTrackAllData"
    dir_list = os.listdir(base_dir)
    for dir_name in dir_list:
        if keyword not in dir_name:
            continue
        dir_path = os.path.join(base_dir, dir_name)
        if os.path.isdir(dir_path):
            jpg_count = stat_jpg(dir_path)
            seq_dir_list = get_dataset_dir_list(dir_path, depth=1)
            print(dir_name, "jpg", jpg_count, "seq", len(seq_dir_list))


if __name__ == "__main__":
    main()
