import os
import cv2
import shutil

import tqdm

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list
from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotation, XAnyLabelingRect

base_dir = r"H:\Datasets\MYZ\YOLO_Format"
output_dir = r"H:\Datasets\MYZ\LabelMe_Format"

yolo_seq_list = get_dataset_dir_list(
    dataset_dir_path=base_dir,
    depth=2
)

for yolo_seq_dir in yolo_seq_list:
    print(yolo_seq_dir)
    seq_name = os.path.basename(yolo_seq_dir)

    img_dir = os.path.join(yolo_seq_dir, "images")
    label_dir = os.path.join(yolo_seq_dir, "labels")
    if not os.path.exists(img_dir) or not os.path.exists(label_dir):
        print(f"Error: {seq_name} does not have images or labels directory.")
        continue

    target_dir = os.path.join(output_dir, seq_name)
    os.makedirs(target_dir, exist_ok=True)

    img_list = os.listdir(img_dir)
    img_list = [
        file_name
        for file_name in img_list
        if file_name.endswith(".jpg")
    ]

    image_width, image_height = 0, 0

    for img_file_name in tqdm.tqdm(img_list):
        img_file_path = os.path.join(img_dir, img_file_name)
        img_name_no_ext = os.path.splitext(img_file_name)[0]

        label_file_path = os.path.join(label_dir, img_name_no_ext + ".txt")

        if image_width == 0 or image_height == 0:
            cv2_img = cv2.imread(img_file_path)
            image_shape = cv2_img.shape
            if len(image_shape) == 3:
                image_height, image_width, _ = image_shape
            else:
                image_height, image_width = image_shape

        with open(label_file_path, "r") as f:
            lines = f.readlines()
        lines = [
            line.strip()
            for line in lines
            if line.strip()
        ]

        target_img_path = os.path.join(target_dir, img_file_name)
        target_label_path = os.path.join(target_dir, img_name_no_ext + ".json")

        # Copy Image
        shutil.copyfile(img_file_path, target_img_path)

        file_obj = XAnyLabelingAnnotation()

        file_obj.file_path = target_label_path

        file_obj.version = "0.2.4"
        file_obj.image_width = image_width
        file_obj.image_height = image_height
        file_obj.image_name = img_file_name

        for line in lines:
            line = line.strip()
            (
                group_id,
                center_x_ratio, center_y_ratio,
                width_ratio, height_ratio
            ) = line.split(" ")

            center_x = image_width * float(center_x_ratio)
            center_y = image_height * float(center_y_ratio)
            width = image_width * float(width_ratio)
            height = image_height * float(height_ratio)

            x1 = center_x - width / 2
            y1 = center_y - height / 2

            round_count = 2
            x1, y1, width, height = (
                round(x1, round_count),
                round(y1, round_count),
                round(width, round_count),
                round(height, round_count)
            )

            rect_obj = XAnyLabelingRect()

            rect_obj.x1 = x1
            rect_obj.y1 = y1
            rect_obj.x2 = x1 + width
            rect_obj.y2 = y1 + height

            rect_obj.label = group_id
            rect_obj.group_id = group_id

            file_obj.rect_annotation_list.append(rect_obj)

        file_obj.modifying()
        file_obj.save(with_log=False)

    # Only for debug
    # break
