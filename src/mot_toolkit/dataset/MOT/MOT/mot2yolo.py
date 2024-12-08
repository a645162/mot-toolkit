import os
import os.path as osp

import cv2
from tqdm import tqdm


def convert_mot_to_yolo(lines, i, output_file):
    with open(output_file, "w") as f:
        for line in lines:  # Skip header line
            parts = line.strip().split(",")
            frame_id, obj_id, x, y, width, height, _, _, _ = map(float, parts)
            if frame_id == i + 1:
                # Calculate YOLO format values
                x_center = x + width / 2
                y_center = y + height / 2
                yolo_x = x_center / image_width  # Normalize by image width
                yolo_y = y_center / image_height  # Normalize by image height
                yolo_width = width / image_width  # Normalize by image width
                yolo_height = height / image_height  # Normalize by image height

                # Write YOLO format to file
                f.write(
                    f"0 {yolo_x:08f} {yolo_y:08f} {yolo_width:08f} {yolo_height:08f}\n"
                )


# Replace with your actual image dimensions

if __name__ == "__main__":
    dataset_root = r"D:\BaiduNetdiskDownload\DanceTrack\val"
    output_root = r"D:\BaiduNetdiskDownload\DanceTrackLabels\val"
    seq_list = osp.join(dataset_root)

    for seq in os.listdir(seq_list):
        img_dir_per_seq = osp.join(dataset_root, seq, "img1")

        yolo_label_dir_per_seq = osp.join(output_root, seq, "labels")
        if not os.path.exists(yolo_label_dir_per_seq):
            os.makedirs(yolo_label_dir_per_seq)

        img_list_per_seq = os.listdir(img_dir_per_seq)
        mot_label_per_seq = osp.join(dataset_root, seq, "gt", "gt.txt")
        with open(mot_label_per_seq, "r") as f:
            lines = f.readlines()
            for i, img in tqdm(
                enumerate(img_list_per_seq), total=len(img_list_per_seq), desc=seq
            ):
                if i == 0:
                    image = cv2.imread(osp.join(img_dir_per_seq, img))
                    image_height, image_width, _ = image.shape
                yolo_label_per_seq = osp.join(
                    yolo_label_dir_per_seq, img.replace("jpg", "txt")
                )
                convert_mot_to_yolo(lines, i, yolo_label_per_seq)
