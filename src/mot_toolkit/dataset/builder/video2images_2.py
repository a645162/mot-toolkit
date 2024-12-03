import os

import cv2
import numpy as np
from tqdm import tqdm


def video_to_images(
    video_path, seq_path, sample_interval: int, is_sceonds_interval: bool
):
    frame_count = 0
    video_cap = cv2.VideoCapture(video_path)
    fps = video_cap.get(cv2.CAP_PROP_FPS)

    if sample_interval != 0:
        if is_sceonds_interval:
            sample_interval *= fps
        while True:
            ret, frame = video_cap.read()
            if not ret:
                break
            # cv2.imshow("video", frame)
            if frame_count % sample_interval == 0:
                index = frame_count // sample_interval
                cv2.imwrite(r"{}\{:>04d}.jpg".format(seq_path, index), frame)
                # print(r'save {}\{:>04d}.jpg successfully!'.format(seq_path, index))
            frame_count += 1
    else:
        while True:
            ret, frame = video_cap.read()
            if not ret:
                break
            # cv2.imshow("video", frame)
            cv2.imwrite(r"{}\{:>04d}.jpg".format(seq_path, frame_count), frame)
            # print(r'save {}\{:>04d}.jpg successfully!'.format(seq_path, frame_count))
            frame_count += 1

    video_cap.release()
    cv2.destroyAllWindows()


def run_video_to_imgs(
    videos_path, imgs_path, sample_interval: int, is_sceonds_interval: bool
):
    """将视频转换为图片序列
    Args:
        videos_path (str): 输入视频的根路径

        imgs_path (str): 转换后的图片序列输出路径（不能包含中文）

        sample_interval (int): 采样间隔
    """
    videos_list = os.listdir(videos_path)
    for video in tqdm(videos_list, desc="video"):
        video_path = os.path.join(videos_path, video)

        seq_path = os.path.join(imgs_path, video.split(".")[0])
        if not os.path.exists(seq_path):
            os.makedirs(seq_path)

        video_to_images(video_path, seq_path, sample_interval, is_sceonds_interval)


if __name__ == "__main__":
    source_dir = ""
    target_dir = ""
    sample_interval = 0
    is_sceonds_interval = False

    run_video_to_imgs(source_dir, target_dir, sample_interval, is_sceonds_interval)
