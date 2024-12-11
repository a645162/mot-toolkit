import os
from typing import List

base_dir = r"H:\Datasets\MaritimeTrackAllData\LabelMe\sea_video_20241211_part5"

ext_list: List[str] = ["mp4", "avi", "flv"]

video_list: List[str] = []
video_dict: dict = {}

for root, dirs, files in os.walk(base_dir):
    for file_name in files:
        ext_name = os.path.splitext(file_name)[1][1:]
        file_path = os.path.join(root, file_name)
        if ext_name in ext_list:
            video_list.append(file_path)
            video_dict[file_path] = ""

for video_path in video_list:
    video_name = os.path.basename(video_path)
    dir_path = os.path.dirname(video_path)

    bv_index = video_name.find("BV")
    if bv_index != -1:
        video_name = video_name[bv_index:]
        new_path = os.path.join(dir_path, video_name)
        video_dict[video_path] = new_path

for video_path, new_path in video_dict.items():
    if new_path != "":
        os.rename(video_path, new_path)
        print(f"Rename {video_path} -> {new_path}")
    else:
        print(f"Skip {video_path}")
