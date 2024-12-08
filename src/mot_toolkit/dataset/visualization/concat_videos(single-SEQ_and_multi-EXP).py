import os

import cv2
import numpy as np

for video in ["example-0.4.mp4", "test_final-0.4.mp4"]:
    model1_path = r"D:\Experments-logs\2023-11\11-16\train\rtdetr-l_11-15_noFinalTrain"
    model2_path = r"D:\Experments-logs\2023-11\11-16\train\rtdetr-l_11-15_FinalTrain100"
    model3_path = r"D:\Experments-logs\2023-11\11-16\train\rtdetr-x_11-15_noFinalTrain"
    model4_path = r"D:\Experments-logs\2023-11\11-16\train\rtdetr-x_11-15_FinalTrain100"

    video_1 = cv2.VideoCapture(os.path.join(model1_path, video))
    video_2 = cv2.VideoCapture(os.path.join(model2_path, video))
    video_3 = cv2.VideoCapture(os.path.join(model3_path, video))
    video_4 = cv2.VideoCapture(os.path.join(model4_path, video))

    fps = video_1.get(cv2.CAP_PROP_FPS)
    video_dir = os.path.join(r"D:\Experments-logs\2023-11\11-16\train", video)
    fourcc = cv2.VideoWriter_fourcc("m", "p", "4", "v")
    videowriter = cv2.VideoWriter(video_dir, fourcc, fps, (1920 * 2, 1080 * 2))
    while True:
        ret, frame1 = video_1.read()
        _, frame2 = video_2.read()
        _, frame3 = video_3.read()
        _, frame4 = video_4.read()
        if not ret:
            break

        lw = max(round(sum(frame1.shape) / 2 * 0.003), 2)
        tf = max(lw - 1, 1)  # font thickness
        sf = lw / 3  # font scale

        frame1 = cv2.putText(
            frame1,
            "RTDETR-L-No",
            (0, int(0.05 * frame1.shape[0])),
            0,
            sf,
            (0, 255, 255),
            thickness=tf,
            lineType=cv2.LINE_AA,
        )
        frame2 = cv2.putText(
            frame2,
            "RTDETR-L",
            (0, int(0.05 * frame1.shape[0])),
            0,
            sf,
            (0, 255, 255),
            thickness=tf,
            lineType=cv2.LINE_AA,
        )
        frame3 = cv2.putText(
            frame3,
            "RTDETR-X-No",
            (0, int(0.05 * frame1.shape[0])),
            0,
            sf,
            (0, 255, 255),
            thickness=tf,
            lineType=cv2.LINE_AA,
        )
        frame4 = cv2.putText(
            frame4,
            "RTDETR-X",
            (0, int(0.05 * frame1.shape[0])),
            0,
            sf,
            (0, 255, 255),
            thickness=tf,
            lineType=cv2.LINE_AA,
        )

        frame_up = np.hstack((frame1, frame2))
        frame_down = np.hstack((frame3, frame4))
        out_frame = np.vstack((frame_up, frame_down))

        videowriter.write(out_frame)

    videowriter.release()
