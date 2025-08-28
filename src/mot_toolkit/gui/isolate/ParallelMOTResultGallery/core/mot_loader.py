"""MOT结果加载器 - 使用新的MOTResult数据类"""

import os
from pathlib import Path
from typing import List, Dict, Optional

from mot_toolkit.datatype.dataset.mot_result import MOTResult, MOTResultLoader as BaseMOTResultLoader
from mot_toolkit.utils.logs import get_logger

LOGGER = get_logger()


class MOTResultLoader:
    """MOT结果加载器 - 适配器类，用于向后兼容"""

    def __init__(self):
        self.base_loader = BaseMOTResultLoader()
        self.results = {}  # {sequence_name: {algorithm_name: result_path}}
        self.sequences = set()
        self.algorithms = {}

    def add_algorithm_directory(self, directory: str, algorithm_name: str) -> bool:
        """添加算法结果目录"""
        directory = Path(directory)
        if not directory.exists():
            LOGGER.error(f"[MOTResultLoader] 目录不存在: {directory}")
            return False

        # 使用基础加载器添加目录
        added_results = self.base_loader.add_result_directory(directory, algorithm_name)
        if not added_results:
            LOGGER.warning(f"[MOTResultLoader] 目录 {directory} 中没有找到有效的txt文件")
            return False

        # 更新内部状态
        self.algorithms[algorithm_name] = str(directory)
        for seq_name in added_results.keys():
            self.sequences.add(seq_name)
            if seq_name not in self.results:
                self.results[seq_name] = {}
            self.results[seq_name][algorithm_name] = str(directory / f"{seq_name}.txt")

        LOGGER.info(f"[MOTResultLoader] 添加算法: {algorithm_name} -> {directory}")
        LOGGER.info(f"[MOTResultLoader] 当前算法: {list(self.algorithms.keys())}")
        LOGGER.info(f"[MOTResultLoader] 当前序列: {list(self.sequences)}")
        return True

    def remove_algorithm(self, algorithm_name: str) -> bool:
        """移除算法"""
        if algorithm_name not in self.algorithms:
            return False

        # 从基础加载器中移除相关结果
        sequences_to_remove = []
        for seq_name in self.sequences:
            key = f"{algorithm_name}_{seq_name}"
            if key in self.base_loader.results:
                del self.base_loader.results[key]

        # 更新内部状态
        del self.algorithms[algorithm_name]
        
        to_remove_sequences = []
        for seq_name, algo_results in self.results.items():
            if algorithm_name in algo_results:
                del algo_results[algorithm_name]
            if not algo_results:  # 如果没有算法了，移除序列
                to_remove_sequences.append(seq_name)

        for seq_name in to_remove_sequences:
            del self.results[seq_name]
            self.sequences.discard(seq_name)

        return True

    def get_sequences(self) -> List[str]:
        """获取所有序列名称"""
        return sorted(list(self.sequences))

    def get_algorithms(self) -> List[str]:
        """获取所有算法名称"""
        return sorted(list(self.algorithms.keys()))

    def get_result_path(self, sequence: str, algorithm: str) -> Optional[str]:
        """获取指定序列和算法的结果文件路径"""
        path = self.results.get(sequence, {}).get(algorithm)
        LOGGER.debug(
            f"[MOTResultLoader] 获取结果路径: 序列={sequence}, 算法={algorithm}, 路径={path}"
        )
        return path

    def get_algorithm_directory(self, algorithm: str) -> Optional[str]:
        """获取算法目录路径"""
        return self.algorithms.get(algorithm)

    def get_results_for_frame(
        self, sequence: str, algorithm: str, frame_idx: int
    ) -> List[Dict]:
        """获取指定帧的跟踪结果"""
        # 使用新的MOTResult类获取结果
        key = f"{algorithm}_{sequence}"
        result = self.base_loader.results.get(key)
        if not result:
            return []

        # MOT格式通常从1开始计数
        frame_id = frame_idx + 1
        tracks = result.get_tracks_for_frame(frame_id)
        
        # 转换为旧格式以保持兼容性
        results = []
        for track in tracks:
            results.append({
                "track_id": track.track_id,
                "x1": track.x,
                "y1": track.y,
                "x2": track.x + track.width,
                "y2": track.y + track.height,
                "width": track.width,
                "height": track.height,
                "confidence": track.confidence,
            })

        LOGGER.debug(
            f"[MOTResultLoader] 序列={sequence}, 算法={algorithm}, 帧={frame_idx}, 结果数量={len(results)}"
        )
        return results

    def get_mot_result(self, sequence: str, algorithm: str) -> Optional[MOTResult]:
        """获取MOTResult对象（新方法）"""
        key = f"{algorithm}_{sequence}"
        return self.base_loader.results.get(key)