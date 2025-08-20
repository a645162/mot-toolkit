"""MOT结果加载器"""

import os
from pathlib import Path
from typing import List, Dict, Optional

from mot_toolkit.utils.logs import get_logger

LOGGER = get_logger()


class MOTResultLoader:
    """MOT结果加载器"""

    def __init__(self):
        self.results = {}  # {sequence_name: {algorithm_name: result_path}}
        self.sequences = set()
        self.algorithms = {}

    def add_algorithm_directory(self, directory: str, algorithm_name: str) -> bool:
        """添加算法结果目录"""
        directory = Path(directory)
        if not directory.exists():
            LOGGER.error(f"[MOTResultLoader] 目录不存在: {directory}")
            return False

        # 扫描目录中的txt文件
        txt_files = list(directory.glob("*.txt"))
        LOGGER.info(
            f"[MOTResultLoader] 在 {directory} 中找到 {len(txt_files)} 个txt文件"
        )

        for txt_file in txt_files:
            LOGGER.debug(f"[MOTResultLoader] 发现文件: {txt_file.name}")

        if not txt_files:
            LOGGER.warning(f"[MOTResultLoader] 目录 {directory} 中没有找到txt文件")
            return False

        self.algorithms[algorithm_name] = str(directory)
        LOGGER.info(f"[MOTResultLoader] 添加算法: {algorithm_name} -> {directory}")

        # 提取序列名称
        for txt_file in txt_files:
            seq_name = txt_file.stem
            self.sequences.add(seq_name)

            if seq_name not in self.results:
                self.results[seq_name] = {}
            self.results[seq_name][algorithm_name] = str(txt_file)
            LOGGER.debug(f"[MOTResultLoader] 添加序列: {seq_name} -> {txt_file}")

        LOGGER.info(f"[MOTResultLoader] 当前算法: {list(self.algorithms.keys())}")
        LOGGER.info(f"[MOTResultLoader] 当前序列: {list(self.sequences)}")
        return True

    def remove_algorithm(self, algorithm_name: str) -> bool:
        """移除算法"""
        if algorithm_name not in self.algorithms:
            return False

        del self.algorithms[algorithm_name]

        # 从结果中移除该算法的所有记录
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
        result_path = self.get_result_path(sequence, algorithm)
        if not result_path or not os.path.exists(result_path):
            return []

        results = []
        try:
            with open(result_path, "r") as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                parts = line.split(",")
                if len(parts) < 6:
                    continue

                try:
                    frame = int(parts[0])
                    if frame != frame_idx + 1:  # MOT格式通常从1开始
                        continue

                    track_id = int(parts[1])
                    x1 = float(parts[2])
                    y1 = float(parts[3])
                    width = float(parts[4])
                    height = float(parts[5])
                    confidence = float(parts[6]) if len(parts) > 6 else 1.0

                    results.append(
                        {
                            "track_id": track_id,
                            "x1": x1,
                            "y1": y1,
                            "x2": x1 + width,
                            "y2": y1 + height,
                            "width": width,
                            "height": height,
                            "confidence": confidence,
                        }
                    )

                except (ValueError, IndexError):
                    continue

        except Exception as e:
            LOGGER.error(f"[MOTResultLoader] 读取结果文件失败: {e}")

        LOGGER.debug(
            f"[MOTResultLoader] 序列={sequence}, 算法={algorithm}, 帧={frame_idx}, 结果数量={len(results)}"
        )
        return results
