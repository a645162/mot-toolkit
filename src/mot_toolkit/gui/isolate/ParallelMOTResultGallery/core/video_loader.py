"""视频加载器"""

import os
import cv2
import numpy as np
from typing import List, Optional


class VideoFrameLoader:
    """视频帧加载器"""

    def __init__(self):
        self.video_path = None
        self.cap = None
        self.total_frames = 0
        self.current_frame = 0

    def set_video(self, video_path: str) -> bool:
        """设置视频路径"""
        if not video_path or not os.path.exists(video_path):
            return False

        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            return False

        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_frame = 0
        return True

    def get_frame(self, frame_num: int) -> Optional[np.ndarray]:
        """获取指定帧"""
        if not self.cap or frame_num >= self.total_frames or frame_num < 0:
            return None

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = self.cap.read()
        return frame if ret else None

    def get_frames_range(self, start_frame: int, count: int = 5) -> List[np.ndarray]:
        """获取连续的多帧"""
        frames = []
        for i in range(count):
            frame_num = start_frame + i
            if frame_num < self.total_frames:
                frame = self.get_frame(frame_num)
                if frame is not None:
                    frames.append(frame)
        return frames

    def get_total_frames(self) -> int:
        """获取总帧数"""
        return self.total_frames

    def release(self):
        """释放资源"""
        if self.cap:
            self.cap.release()
            self.cap = None

    def __del__(self):
        """析构函数"""
        self.release()
