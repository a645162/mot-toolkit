import csv
import os

import cv2


def get_video_info(file_path):
    video_info = {}

    # 使用 OpenCV 打开视频文件
    video_capture = cv2.VideoCapture(file_path)

    # 获取视频文件名
    video_info["File Name"] = os.path.basename(file_path)

    # 获取帧率
    fps = video_capture.get(cv2.CAP_PROP_FPS)
    video_info["FPS"] = fps

    # 获取分辨率
    width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video_info["Resolution"] = f"{width}x{height}"

    # 获取视频总帧数
    total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
    video_info["Frame Count"] = total_frames

    # 获取视频时长
    duration = total_frames / fps
    video_info["Duration (s)"] = duration

    # 关闭视频文件
    video_capture.release()

    return video_info


def write_to_csv(video_info_list, output_file):
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        fieldnames = ["File Name", "FPS", "Resolution", "Frame Count", "Duration (s)"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        for video_info in video_info_list:
            writer.writerow(video_info)


# 要处理的视频文件夹路径
folder_path = r"D:\shipvideos\bilibili_bv"

# 存储视频信息的列表
video_info_list = []

# 遍历文件夹中的视频文件
for file_name in os.listdir(folder_path):
    if file_name.endswith(".mp4") or file_name.endswith(
        ".avi"
    ):  # 确认文件是视频文件格式
        file_path = os.path.join(folder_path, file_name)
        video_info = get_video_info(file_path)
        video_info_list.append(video_info)

# 写入 CSV 文件
output_csv = r"D:\shipvideos\video_info.csv"
write_to_csv(video_info_list, output_csv)
