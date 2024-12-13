import os
from typing import List


def check_dir_is_disable(
        dir_path: str,
        disable_file_name: str = "disable"
) -> bool:
    dir_path = os.path.abspath(dir_path)

    result = False

    file_path = os.path.join(dir_path, disable_file_name)
    if os.path.exists(file_path):
        print("Found disable file:", file_path)
        result = True

    # Check Parent Dir
    # Check is have parent dir
    parent_dir = os.path.dirname(dir_path)
    if parent_dir != dir_path:
        result = (
                result or
                check_dir_is_disable(
                    dir_path=parent_dir,
                    disable_file_name=disable_file_name
                )
        )

    return result


def get_dataset_dir_list(
        dataset_dir_path: str,
        depth: int = 2,
        black_list: List[str] = None,
        check_disable: bool = True
) -> List[str]:
    if black_list is None:
        black_list = []

    final_dir_list: List[str] = []

    jpeg_dir_path_list: List[str] = []

    for root, dirs, files in os.walk(dataset_dir_path):
        for file in files:
            if file.endswith(".jpg"):
                jpeg_dir_path_list.append(root)
                break

    for jpeg_dir_name in jpeg_dir_path_list:
        if jpeg_dir_name not in final_dir_list:
            # Black list
            found = False
            for keywords in black_list:
                if keywords in jpeg_dir_name:
                    found = True
                    break
            if found:
                continue

            final_dir_list.append(jpeg_dir_name)

    # Remove disable dir
    if check_disable:
        new_path_list = []
        for dir_path in final_dir_list:
            if not check_dir_is_disable(dir_path):
                new_path_list.append(dir_path)
        final_dir_list = new_path_list

    depth -= 1
    while depth > 0:
        new_dir_list: List[str] = []
        for dir_path in final_dir_list:
            new_path = os.path.dirname(dir_path)

            new_dir_list.append(new_path)

        final_dir_list = new_dir_list
        depth -= 1

    # Remove Redundant
    # Will keep sorted order
    new_path_list: List[str] = []
    for dir_path in final_dir_list:
        if dir_path not in new_path_list:
            new_path_list.append(dir_path)
    final_dir_list = new_path_list

    return final_dir_list


if __name__ == "__main__":
    datasets_dir_path = r"H:\Datasets\MaritimeTrackAllData\LabelMe"

    dir_list = get_dataset_dir_list(
        dataset_dir_path=datasets_dir_path,
        depth=2,
        black_list=["Task"]
    )

    print("Final Dir List:")
    for dir_path in dir_list:
        print(dir_path)
