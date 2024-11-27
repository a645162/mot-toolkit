import os
import multiprocessing
import datetime
from typing import List

import PIL.Image as pillow
import torchvision.transforms as T
import torchvision.transforms.functional as F

from mot_toolkit.config.hardware import io_cpu_count
from mot_toolkit.dataset.dataset_dir import get_dataset_dir_list


def check_pillow_error(img_path: str) -> bool:
    try:
        # Open With Pillow
        with pillow.open(img_path) as img:
            new_image = img.copy()
            new_image = F.hflip(new_image)
            new_image = F.hflip(new_image)
            new_image = F.vflip(new_image)
            new_image = F.vflip(new_image)
        return True
    except Exception as e:
        print(f"Error: {img_path} - {e}")
        return False


def handle_dir(
        dir_path: str
):
    if not (
            os.path.exists(dir_path) and
            os.path.isdir(dir_path)
    ):
        return

    jpg_list: List[str] = []
    error_list: List[str] = []

    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith(".jpg"):
                jpg_list.append(os.path.join(root, file))

    for jpg_path in jpg_list:
        if not check_pillow_error(jpg_path):
            error_list.append(jpg_path)
            print(f"Error: {jpg_path}")

    for jpg_path in error_list:
        pass


def main():
    work_directory_path = r"/mnt/h/Datasets/TrackShipOnlineVideo/LabelMe/"
    work_directory_path = os.path.normpath(work_directory_path)
    work_directory_path = os.path.abspath(work_directory_path)

    dir_list = get_dataset_dir_list(
        dataset_dir_path=work_directory_path,
        depth=1,
        black_list=["Task"]
    )

    print(f"Found {len(dir_list)} directories.")
    input("Press Enter to continue...")

    print("Start fixing pillow errors...")
    processes_count = io_cpu_count

    # Record Start Time
    start_time = datetime.datetime.now()

    with multiprocessing.Pool(processes=processes_count) as pool:
        pool.map(handle_dir, dir_list)

    # Record End Time
    end_time = datetime.datetime.now()

    # Calculate Time Delta
    time_delta: datetime.timedelta = end_time - start_time

    print(f"Use Time: {time_delta}")

    print("Done.")


if __name__ == "__main__":
    main()
