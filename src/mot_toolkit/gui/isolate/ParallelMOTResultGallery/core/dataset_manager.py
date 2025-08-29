"""数据集管理器 - 处理DanceTrack格式的数据集"""

import os
from typing import List, Dict, Optional
from mot_toolkit.utils.logs import get_logger

LOGGER = get_logger()


class DatasetManager:
    """数据集管理器 - 支持DanceTrack格式的多split管理"""

    def __init__(self):
        self.dataset_path = ""
        self.sequence_paths = {}  # {sequence_name: full_path}
        self.available_splits = {"train", "val", "test"}
        self.selected_splits = {"train", "val", "test"}

    def set_dataset_path(self, path: str) -> bool:
        """设置数据集路径"""
        if not path or not os.path.exists(path):
            return False

        self.dataset_path = path
        self.scan_sequences()
        return True

    def set_selected_splits(self, splits: List[str]) -> None:
        """设置选择的split"""
        self.selected_splits = set(splits)
        self.scan_sequences()

    def scan_sequences(self) -> None:
        """扫描所有选择的split中的序列"""
        self.sequence_paths = {}

        if not self.dataset_path:
            LOGGER.debug("数据集路径为空，跳过扫描")
            return

        for split in self.selected_splits:
            split_path = os.path.join(self.dataset_path, split)
            if not os.path.exists(split_path):
                continue

            items = os.listdir(split_path)

            # 扫描该split下的所有序列
            for item in items:
                seq_path = os.path.join(split_path, item)
                if os.path.isdir(seq_path):
                    # 检查DanceTrack格式：必须有img1目录
                    all_files = os.listdir(seq_path)
                    has_img1 = "img1" in all_files and os.path.isdir(
                        os.path.join(seq_path, "img1")
                    )

                    # 只要是有效的DanceTrack序列就添加
                    if has_img1:
                        self.sequence_paths[item] = seq_path

        LOGGER.info(f"[DatasetManager] 扫描完成，共找到{len(self.sequence_paths)}个序列")

    def get_sequences(self) -> List[str]:
        """获取所有可用序列名称"""
        return sorted(list(self.sequence_paths.keys()))

    def get_sequence_path(self, sequence: str) -> Optional[str]:
        """获取序列的完整路径"""
        return self.sequence_paths.get(sequence)

    def get_video_path(self, sequence: str) -> Optional[str]:
        """获取序列的视频文件路径"""
        seq_path = self.get_sequence_path(sequence)
        if not seq_path:
            return None

        # 优先查找视频文件
        for ext in [".mp4", ".avi", ".mov", ".mkv"]:
            video_path = os.path.join(seq_path, f"{sequence}{ext}")
            if os.path.exists(video_path):
                return video_path

        # 查找目录中的视频文件
        video_files = [
            f
            for f in os.listdir(seq_path)
            if f.endswith((".mp4", ".avi", ".mov", ".mkv"))
        ]
        if video_files:
            return os.path.join(seq_path, video_files[0])

        # 检查是否为DanceTrack格式（img1目录）
        img1_path = os.path.join(seq_path, "img1")
        if os.path.exists(img1_path) and os.path.isdir(img1_path):
            # 返回img1目录路径，视频加载器会处理图像序列
            return img1_path

        return None

    def get_available_splits(self) -> List[str]:
        """获取可用的split列表"""
        splits = []
        if not self.dataset_path:
            return splits

        for split in self.available_splits:
            split_path = os.path.join(self.dataset_path, split)
            if os.path.exists(split_path):
                splits.append(split)
        return sorted(splits)

    def get_sequence_info(self) -> Dict[str, Dict]:
        """获取序列信息，包括所属split"""
        info = {}
        for seq_name, seq_path in self.sequence_paths.items():
            split = os.path.basename(os.path.dirname(seq_path))
            info[seq_name] = {"path": seq_path, "split": split}
        return info
