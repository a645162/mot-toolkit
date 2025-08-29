import os
import time

import cv2
import tqdm

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list

import multiprocessing

base_dir = r"H:\Datasets\MaritimeTrackAllData\Spilt\MaritimeTrack_Full_Same"
output_dir = r"H:\Datasets\MaritimeTrackAllData\Spilt\MaritimeTrack_Full_Same_ReID"

seq_list = get_dataset_dir_list(
    dataset_dir_path=base_dir,
    depth=2
)


def handle_seq(seq_dir_path):
    print(f"Process {seq_dir_path}")
    gt_dir = os.path.join(seq_dir_path, "gt")
    gt_txt_path = os.path.join(gt_dir, "gt.txt")
    image_dir = os.path.join(seq_dir_path, "img1")

    seq_name = os.path.basename(seq_dir_path)

    if not os.path.exists(gt_dir):
        print(f"GT {gt_dir} not exists!")
        return
    if not os.path.exists(gt_txt_path):
        print(f"GT {gt_txt_path} not exists!")
        return
    if not os.path.exists(image_dir):
        print(f"Image {image_dir} not exists!")
        return

    with open(gt_txt_path, "r") as f:
        lines = f.readlines()
        lines = [
            line.strip()
            for line in lines
            if line.strip()
        ]

    # print("Parse GT")
    gt_frame_dict = {}
    for line in tqdm.tqdm(lines):
        line_list = line.split(",")
        frame_index, id, x, y, w, h, _, _, _ = line_list
        frame_index = str(int(frame_index))
        id = str(int(id))

        if frame_index not in gt_frame_dict.keys():
            gt_frame_dict[frame_index] = []

        gt_frame_dict[frame_index].append([id, x, y, w, h])

    # print("Parse GT Done")

    def get_id_dir(id):
        return os.path.join(output_dir, f"{seq_name}_{id}")

    for file_name in tqdm.tqdm(os.listdir(image_dir)):
        if not file_name.endswith(".jpg"):
            continue

        image_path = os.path.join(image_dir, file_name)
        image_name_no_ext = os.path.splitext(file_name)[0]
        image_index = str(int(image_name_no_ext))

        if image_index not in gt_frame_dict.keys():
            continue

        for gt_obj in gt_frame_dict[image_index]:
            id, x, y, w, h = gt_obj
            x, y, w, h = int(float(x)), int(float(y)), int(float(w)), int(float(h))

            if not (x > 0 and y > 0 and w > 0 and h > 0):
                continue

            # Crop
            if not os.path.exists(image_path):
                print(f"Image {image_path} not exists!")
                continue
            original_image = cv2.imread(image_path)
            if original_image is None:
                print(f"Image {image_path} read failed!")
                continue
            # Check is Empty
            if original_image.size == 0:
                print(f"Image {image_path} is empty!")
                continue

            cropped_image = original_image[y:y + h, x:x + w]
            # Check is Empty
            if cropped_image.size == 0:
                print(f"Cropped Image {image_path} is empty!")
                continue

            image_name = f"{id}_{image_name_no_ext}.jpg"

            target_dir = get_id_dir(id)
            os.makedirs(target_dir, exist_ok=True)

            target_image_path = os.path.join(target_dir, image_name)
            try:
                cv2.imwrite(target_image_path, cropped_image)
            except Exception as e:
                print(f"Write Image {target_image_path} failed!")
                print(e)


def main():
    start_time = time.time()

    with multiprocessing.Pool(16) as pool:
        pool.map(handle_seq, seq_list)

    end_time = time.time()

    print(f"Time: {round(end_time - start_time)} s")


if __name__ == "__main__":
    main()
