# https://github.com/yangchris11/samurai

import os
from typing import List

import tqdm

base_path: str = r"/mnt/h/Datasets/TrackShipOnlineVideo/LabelMe/"
txt_list: List[str] = []

for root, dirs, files in os.walk(base_path):
    for file in files:
        if file.endswith("_samurai.txt"):
            txt_list.append(os.path.join(root, file))

print(f"Found {len(txt_list)} txt files.")
input("Press Enter to continue...")

for txt_path in tqdm.tqdm(txt_list):
    os.remove(txt_path)
