import os
from typing import List


def get_dataset_dir_list(
        dataset_dir_path: str,
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
        parent_dir_path = os.path.dirname(jpeg_dir_name)

        if parent_dir_path not in final_dir_list:
            # Black list
            found = False
            for keywords in black_list:
                if keywords in parent_dir_path:
                    found = True
                    break
            if found:
                continue

            final_dir_list.append(parent_dir_path)

    return final_dir_list


if __name__ == "__main__":
    datasets_dir_path = r"/mnt/h/Datasets/TrackShipOnlineVideo/LabelMe"

    dir_list = get_dataset_dir_list(
        dataset_dir_path=datasets_dir_path,
        black_list=["Task"]
    )

    for dir_path in dir_list:
        print(dir_path)
