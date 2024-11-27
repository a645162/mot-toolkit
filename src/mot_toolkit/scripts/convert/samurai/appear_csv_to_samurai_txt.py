# Zero Shot samurai based on SAM2
# https://yangchris11.github.io/samurai/

from typing import List
import os
import tqdm

base_path: str = r"/mnt/h/Datasets/TrackShipOnlineVideo/LabelMe/"
csv_list: List[str] = []

for root, dirs, files in os.walk(base_path):
    for file in files:
        if file.endswith(".csv"):
            csv_list.append(os.path.join(root, file))

print(f"Found {len(csv_list)} csv files.")
input("Press Enter to continue...")

for csv_path in tqdm.tqdm(csv_list):
    with open(csv_path, "r") as f:
        lines = f.readlines()

    lines = [line.strip() for line in lines]
    if len(lines) != 1:
        continue

    frame, id, x, y, w, h = lines[0].split(",")
    x, y, w, h = map(float, [x, y, w, h])

    new_line = f"{x},{y},{w},{h}"

    save_path = csv_path.replace(".csv", "_samurai.txt")
    with open(save_path, "w") as f:
        f.write(new_line)
