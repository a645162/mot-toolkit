import os
import shutil
from typing import List

import tqdm

base_dir = r"H:\Datasets\MaritimeTrackAllData\Spilt\ReIDDataset"

train = os.path.join(base_dir, "train")
gallery = os.path.join(base_dir, "gallery")

train_list = os.listdir(train)
train_list = [os.path.join(train, seq) for seq in train_list]
gallery_list = os.listdir(gallery)
gallery_list = [os.path.join(gallery, seq) for seq in gallery_list]


# all_dir_path_list = train_list + gallery_list


def plan_id(dir_path_list: List[str]):
    for i in tqdm.tqdm(range(len(dir_path_list)), desc="Move to temp position"):
        original_path = dir_path_list[i]
        dir_name = os.path.basename(original_path)
        parent_path = os.path.dirname(original_path)
        new_name = f"temp_{i:08d}"
        new_path = os.path.join(parent_path, new_name)

        # Move
        shutil.move(original_path, new_path)

        dir_path_list[i] = new_path

    id = 0
    for i, dir_path in enumerate(tqdm.tqdm(dir_path_list, desc="Plan Id")):
        if not os.path.isdir(dir_path):
            continue

        seq_name = os.path.basename(dir_path)
        parent_name = os.path.dirname(dir_path)

        id += 1
        new_dir_name = f"{id:04d}"

        new_dir_path = os.path.join(parent_name, new_dir_name)

        # os.rename(dir_path, new_dir_path)
        # OSError: [Errno 39] Directory not empty
        shutil.move(dir_path, new_dir_path)


plan_id(train_list)
plan_id(gallery_list)
