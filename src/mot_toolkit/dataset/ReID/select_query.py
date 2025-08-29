import os
import shutil
import tqdm

base_dir = r"H:\Datasets\MaritimeTrackAllData\Spilt\ReIDDataset"

gallery_dir = os.path.join(base_dir, "gallery")
query_dir = os.path.join(base_dir, "query")

if os.path.exists(query_dir):
    shutil.rmtree(query_dir)
os.makedirs(query_dir, exist_ok=True)

gallery_list = os.listdir(gallery_dir)
gallery_list = [
    os.path.join(gallery_dir, seq)
    for seq in gallery_list
]

for i, dir_path in enumerate(tqdm.tqdm(gallery_list)):
    if not os.path.isdir(dir_path):
        continue

    id = os.path.basename(dir_path)

    file_name_list = os.listdir(dir_path)
    file_name_list = [
        file_name
        for file_name in file_name_list
        if file_name.endswith(".jpg")
    ]

    # Select center file
    center_index = len(file_name_list) // 2

    center_file_name = file_name_list[center_index]

    file_path = os.path.join(dir_path, center_file_name)

    target_path = os.path.join(query_dir, f"{id}.jpg")

    # Copy Image
    shutil.copy(file_path, target_path)
