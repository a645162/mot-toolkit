from typing import List

import os
import shutil

import cv2

img_path_list: List[str] = [
    "/mnt/h/Datasets/TrackShipOnlineVideo/LabelMe/sea_video_20240313_part3/Onshore/BV12Z4y1X79d-4qMJVY5V4y6RPxQu/00000000-00010903/00010725.jpg",
    "/mnt/h/Datasets/TrackShipOnlineVideo/LabelMe/sea_video_20240313_part2/OnboardTL/BV14S4y147jX-t5PTpDLBGiSESMzw/00009610-00029018/00022327.jpg"
]

for img_path in img_path_list:
    filename = os.path.basename(img_path)
    file_name_no_ext = os.path.splitext(filename)[0]
    file_name_index = int(file_name_no_ext)

    file_name_length = len(file_name_no_ext)

    new_index = file_name_index - 1
    if new_index < 0:
        new_index = 1

    new_filename = str(new_index).zfill(file_name_length) + ".jpg"

    print("Copy", new_filename, "to", filename)

    new_img_path = os.path.join(os.path.dirname(img_path), new_filename)
    shutil.copyfile(new_img_path, img_path)

    # img = cv2.imread(img_path)
    #
    # cv2.imshow("img", img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
