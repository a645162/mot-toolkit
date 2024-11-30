import os
from typing import List


def get_dataset_dir_list(
        dataset_dir_path: str,
        depth: int = 2,
        black_list: List[str] = None
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
    datasets_dir_path = r"/mnt/h/Datasets/TrackShipOnlineVideo/LabelMe"

    dir_list = get_dataset_dir_list(
        dataset_dir_path=datasets_dir_path,
        depth=2,
        black_list=["Task"]
    )

    for dir_path in dir_list:
        print(dir_path)
