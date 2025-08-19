"""视频加载器"""

import os
import cv2
import numpy as np
from typing import List, Optional
from pathlib import Path


class VideoFrameLoader:
    """视频帧加载器 - 支持视频文件和图像序列"""

    def __init__(self):
        self.video_path = None
        self.cap = None
        self.total_frames = 0
        self.current_frame = 0
        self.is_image_sequence = False
        self.image_files = []
        self.image_dir = None

    def set_video(self, video_path: str) -> bool:
        """设置视频路径或图像序列目录"""
        if not video_path or not os.path.exists(video_path):
            return False

        self.video_path = video_path
        
        # 检查是否为图像序列目录
        if os.path.isdir(video_path):
            # 检查是否为img1目录（DanceTrack格式）
            if os.path.basename(video_path) == 'img1':
                self.image_dir = video_path
            else:
                # 检查是否有img1子目录
                img1_path = os.path.join(video_path, 'img1')
                if os.path.exists(img1_path) and os.path.isdir(img1_path):
                    self.image_dir = img1_path
                else:
                    # 直接使用该目录
                    self.image_dir = video_path
            
            # 获取图像文件列表
            self.image_files = sorted([
                f for f in os.listdir(self.image_dir)
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))
            ])
            
            if not self.image_files:
                return False
            
            self.total_frames = len(self.image_files)
            self.is_image_sequence = True
            self.current_frame = 0
            return True
        
        # 处理视频文件
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            return False

        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.is_image_sequence = False
        self.current_frame = 0
        return True

    def get_frame(self, frame_num: int) -> Optional[np.ndarray]:
        """获取指定帧"""
        if frame_num >= self.total_frames or frame_num < 0:
            return None

        if self.is_image_sequence:
            # 从图像序列加载
            if frame_num < len(self.image_files):
                image_path = os.path.join(self.image_dir, self.image_files[frame_num])
                frame = cv2.imread(image_path)
                return frame
            return None
        else:
            # 从视频文件加载
            if not self.cap:
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
        self.image_files = []
        self.image_dir = None

    def __del__(self):
        """析构函数"""
        self.release()
