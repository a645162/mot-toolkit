import os

import cv2
from tqdm import tqdm


def video2images(Video_Dir, Save_dir, Video_idx):
    """
    function: video to pictures
    author: AIJun
    date:2021/3/17
    """
    frame_count = 0
    video = cv2.VideoCapture(Video_Dir)
    fps = video.get(cv2.CAP_PROP_FPS)
    (_, video_name) = os.path.split(Video_Dir)
    pbar = tqdm(range(int(video.get(cv2.CAP_PROP_FRAME_COUNT))))
    pbar.set_description(
        f"正在处理——{video_name}（第{Video_idx + 1}个/共{len(video_list)}个） {fps}fps"
    )

    while video.isOpened():
        ret, frame = video.read()
        if not ret:
            break
        # if frame_count % fps == 0:
        #     cv2.imwrite('pictures/' + str(index) + '.jpg', frame)
        #     cv2.imwrite(r"{}\{:>08d}.jpg".format(Save_dir, index), frame)
        #     index += 1
        # cv2.imshow("video", frame)
        if not os.path.exists(r"{}\{:>08d}.jpg".format(Save_dir, frame_count)):
            # frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
            cv2.imwrite(r"{}\{:>08d}.jpg".format(Save_dir, frame_count), frame)
        # print(r'save {}\{:>08d}.jpg successfully!'.format(Save_dir, frame_count))
        frame_count += 1
        pbar.update()

    video.release()
    cv2.destroyAllWindows()


root_path = r"D:\shipvideos"
seq_path = r"D:\shipvideos_seqs"
# data_type = ['NIR', 'VIS_Onshore', 'VIS_Onboard']
data_types = ["bilibili_ori"]

for data_type in data_types:
    video_list = sorted(os.listdir(os.path.join(root_path, data_type)))
    for video_idx, video in enumerate(video_list):
        # if data_type == 'bilibili_bv':
        #     video_new = 'BV' + video.split('BV')[-1]
        #     os.rename(os.path.join(root_path, data_type, video),
        #               os.path.join(root_path, data_type, video_new))
        #     video = video_new
        video_dir = os.path.join(root_path, data_type, video)
        seq_dir = os.path.join(seq_path, data_type, video[:-4])
        if not os.path.exists(seq_dir):
            os.makedirs(seq_dir)
        # else:
        #     continue
        video2images(video_dir, seq_dir, video_idx)
