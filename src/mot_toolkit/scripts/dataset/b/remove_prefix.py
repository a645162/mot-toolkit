import os

import tqdm

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list

base_dir = r"H:\Datasets\MYZ\YOLO_Format"

seq_list = get_dataset_dir_list(
    dataset_dir_path=base_dir,
    depth=2
)

for seq_dir_path in seq_list:
    print(f"Process {seq_dir_path}")
    image_dir = os.path.join(seq_dir_path, "images")
    label_dir = os.path.join(seq_dir_path, "labels")

    for file_name in tqdm.tqdm(os.listdir(image_dir)):
        txt_name = file_name.replace(".jpg", ".txt")
        if not file_name.endswith(".jpg"):
            continue

        image_path = os.path.join(image_dir, file_name)
        txt_path = os.path.join(label_dir, txt_name)

        if not os.path.exists(image_path):
            print(f"Image {image_path} not exists!")
            continue

        if not os.path.exists(txt_path):
            print(f"Label {txt_path} not exists!")
            continue

        new_img_name = file_name
        find_index = new_img_name.find("_")
        while find_index != -1:
            new_img_name = new_img_name[find_index + 1:]

            find_index = new_img_name.find("_")

        no_ext= new_img_name.replace(".jpg", "")

        new_img_name = no_ext.zfill(8) + ".jpg"

        new_txt_name = new_img_name.replace(".jpg", ".txt")

        new_image_path = os.path.join(image_dir, new_img_name)
        new_txt_path = os.path.join(label_dir, new_txt_name)

        # print(f"Rename {image_path} -> {new_image_path}")
        # print(f"Rename {txt_path} -> {new_txt_path}")

        os.rename(image_path, new_image_path)
        os.rename(txt_path, new_txt_path)
