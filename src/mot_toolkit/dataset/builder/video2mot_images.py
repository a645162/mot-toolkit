import os

import cv2
from tqdm import tqdm

video_types = ["train", "test"]
root_dir = r"D:\Dataset\SFIST"

for video_type in video_types:
    video_dir = os.path.join(root_dir, video_type, "video")
    video_list = os.listdir(video_dir)

    for video in tqdm(video_list):
        dst_folder = os.path.join(root_dir, video_type, video.split(".")[0], "img1")
        if not os.path.exists(dst_folder):
            os.makedirs(dst_folder)

        video = os.path.join(video_dir, video)
        video_cap = cv2.VideoCapture(video)
        fps = video_cap.get(cv2.CAP_PROP_FPS)
        frame_count = 0
        while True:
            ret, frame = video_cap.read()
            if ret is False:
                break
            if frame_count > 0:
                cv2.imwrite(
                    r"{}\{:>06d}.jpg".format(dst_folder, frame_count - 1), frame
                )
                # print(r'save {}\{:>04d}.jpg successfully!'.format(dst_folder, frame_count))
            frame_count = frame_count + 1

        video_cap.release()
        cv2.destroyAllWindows()
        print(video, fps, frame_count)
