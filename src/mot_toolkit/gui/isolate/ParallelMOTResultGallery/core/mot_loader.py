"""MOT结果加载器"""

import os
from pathlib import Path
from typing import List, Dict, Optional


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
            print(f"[DEBUG] MOTResultLoader: 目录不存在 {directory}")
            return False

        # 扫描目录中的txt文件
        txt_files = list(directory.glob("*.txt"))
        print(f"[DEBUG] MOTResultLoader: 在 {directory} 中找到 {len(txt_files)} 个txt文件")
        
        if not txt_files:
            print(f"[DEBUG] MOTResultLoader: 没有找到txt文件")
            return False

        self.algorithms[algorithm_name] = str(directory)
        print(f"[DEBUG] MOTResultLoader: 添加算法 {algorithm_name} -> {directory}")

        # 提取序列名称
        for txt_file in txt_files:
            seq_name = txt_file.stem
            self.sequences.add(seq_name)

            if seq_name not in self.results:
                self.results[seq_name] = {}
            self.results[seq_name][algorithm_name] = str(txt_file)
            print(f"[DEBUG] MOTResultLoader: 添加序列 {seq_name} -> {txt_file}")

        print(f"[DEBUG] MOTResultLoader: 当前算法列表: {list(self.algorithms.keys())}")
        print(f"[DEBUG] MOTResultLoader: 当前序列列表: {list(self.sequences)}")
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
        return self.results.get(sequence, {}).get(algorithm)

    def get_algorithm_directory(self, algorithm: str) -> Optional[str]:
        """获取算法目录路径"""
        return self.algorithms.get(algorithm)
