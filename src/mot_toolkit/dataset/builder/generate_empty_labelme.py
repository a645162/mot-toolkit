from typing import List
import os

import cv2
import tqdm

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list
from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotation


def walk_dir(dir_path: str, ext_name: str = ".jpg"):
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith(ext_name):
                yield os.path.join(root, file)


def handle_seq(seq_dir_path: str):
    img_path_list = [
        img_path
        for img_path in walk_dir(seq_dir_path)
    ]
    json_count = len(
        [
            json_path
            for json_path in walk_dir(seq_dir_path, ".json")
        ]
    )
    if json_count > 0:
        print(f"Found json file, Skip {seq_dir_path}")
        return
    if len(img_path_list) == 0:
        print(f"No image in {seq_dir_path}")
        return

    cv_img = cv2.imread(img_path_list[0])
    shape = cv_img.shape
    if len(shape) == 3:
        height, width, _ = shape
    else:
        height, width = shape

    for img_path in img_path_list:
        dir_path = os.path.dirname(img_path)

        img_name = os.path.basename(img_path)
        img_name_no_ext = os.path.splitext(img_name)[0]
        json_name = img_name_no_ext + ".json"

        json_path = os.path.join(dir_path, json_name)

        file_obj = XAnyLabelingAnnotation()

        file_obj.file_path = json_path

        file_obj.image_name = img_name
        file_obj.image_width = width
        file_obj.image_height = height

        file_obj.modifying()
        file_obj.save(with_log=False)


def handle_dir(dir_path: str):
    print(f"Process {dir_path}")
    seq_list: List[str] = get_dataset_dir_list(
        dataset_dir_path=dir_path,
        depth=1,
        check_disable=False
    )

    for seq_dir_path in tqdm.tqdm(seq_list):
        handle_seq(seq_dir_path)


def main():
    base_dir = r"H:\Datasets\MaritimeTrackAllData\LabelMe\sea_video_20241211_night"
    handle_dir(base_dir)


if __name__ == "__main__":
    main()
