import os
import shutil

profile_name = "val"
dir_path = "/mnt/d/Datasets/MaritimeTrack_Full/DanceTrack"
target_dir = "/mnt/h/Datasets/MaritimeTrack_Full/YOLO"

dir_path = os.path.join(dir_path, profile_name)

yolo_img = os.path.join(target_dir, "images", profile_name)
yolo_label = os.path.join(target_dir, "labels", profile_name)

if os.path.exists(yolo_img):
    shutil.rmtree(yolo_img)
if os.path.exists(yolo_label):
    shutil.rmtree(yolo_label)

os.makedirs(yolo_img, exist_ok=True)
os.makedirs(yolo_label, exist_ok=True)

subdir_list = os.listdir(dir_path)


def handle_dir(dir_name):
    current_dir_path = os.path.join(dir_path, dir_name)

    img_dir = os.path.join(current_dir_path, "img1")
    list_file = os.listdir(img_dir)
    for img_name in list_file:
        img_path = os.path.join(img_dir, img_name)

        new_img_name = dir_name + "_" + img_name

        target_path = os.path.join(yolo_img, new_img_name)

        shutil.copyfile(img_path, target_path)

    def get_label_path(index):
        return os.path.join(yolo_label, f"{dir_name}_{index:08}.txt")

    gt_path = os.path.join(current_dir_path, "gt", "gt.txt")
    gt_content = open(gt_path).readlines()
    for line in gt_content:
        frame, id, x, y, w, h, _, _, _ = line.split(",")
        frame = int(frame)
        x = int(x)
        y = int(y)
        w = int(w)
        h = int(h)
        label_path = get_label_path(frame)

        if not os.path.exists(label_path):
            open(label_path, "w").close()

        image_width = 1920
        image_height = 1080

        # YOLO Format
        x = x + w / 2
        y = y + h / 2

        x = float(x) / image_width
        y = float(y) / image_height
        w = float(w) / image_width
        h = float(h) / image_height

        x = round(x, 6)
        y = round(y, 6)
        w = round(w, 6)
        h = round(h, 6)

        # 追加
        with open(label_path, "a") as f:
            f.write(f"0 {x} {y} {w} {h}\n")


# for dir_name in subdir_list:
#     handle_dir(dir_name)
from multiprocessing import Pool

with Pool(14) as p:
    p.map(handle_dir, subdir_list)

print("Done!")
