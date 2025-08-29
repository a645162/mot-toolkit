"""MOT结果数据类型和解析器

提供MOT（多目标跟踪）结果文件的解析和基本数据操作功能。
支持标准MOT格式：frame_id, track_id, x, y, w, h, confidence, ...
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from mot_toolkit.utils.logs import get_logger

LOGGER = get_logger()


@dataclass
class MOTTrack:
    """单个跟踪目标的数据结构"""
    track_id: int
    frame_id: int
    x: float
    y: float
    width: float
    height: float
    confidence: float = 1.0
    extra_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.extra_data is None:
            self.extra_data = {}

    @property
    def bbox(self) -> List[float]:
        """获取边界框 [x, y, width, height]"""
        return [self.x, self.y, self.width, self.height]

    @property
    def bbox_xyxy(self) -> List[float]:
        """获取边界框 [x1, y1, x2, y2] 格式"""
        return [self.x, self.y, self.x + self.width, self.y + self.height]

    @property
    def center(self) -> Tuple[float, float]:
        """获取边界框中心点"""
        return (self.x + self.width / 2, self.y + self.height / 2)

    @property
    def area(self) -> float:
        """获取边界框面积"""
        return self.width * self.height


class MOTResult:
    """MOT结果数据类
    
    提供MOT结果的加载、解析和基本数据查询功能。
    """

    def __init__(self, file_path: str):
        """
        初始化MOT结果
        
        Args:
            file_path: MOT结果文件路径
        """
        self.file_path = Path(file_path)
        self.sequence_name = self.file_path.stem
        
        # 原始数据
        self._tracks: List[MOTTrack] = []
        self._frame_tracks: Dict[int, List[MOTTrack]] = {}
        self._track_ids: set = set()
        
    @property
    def is_loaded(self) -> bool:
        """检查数据是否已加载"""
        return len(self._tracks) > 0
    
    @property
    def total_tracks(self) -> int:
        """获取总跟踪目标数"""
        return len(self._track_ids)
    
    @property
    def total_frames(self) -> int:
        """获取总帧数"""
        return len(self._frame_tracks)
    
    @property
    def frame_range(self) -> Tuple[int, int]:
        """获取帧范围 (min_frame, max_frame)"""
        if not self._frame_tracks:
            return (0, 0)
        frames = list(self._frame_tracks.keys())
        return (min(frames), max(frames))
    
    @property
    def track_ids(self) -> List[int]:
        """获取所有跟踪ID"""
        return sorted(list(self._track_ids))
    
    def load(self) -> bool:
        """
        加载MOT结果文件
        
        Returns:
            是否加载成功
        """
        if self.is_loaded:
            return True
            
        if not self.file_path.exists():
            LOGGER.error(f"MOT结果文件不存在: {self.file_path}")
            return False
            
        try:
            LOGGER.info(f"解析MOT结果文件: {self.file_path}")
            return self._parse_file()
            
        except Exception as e:
            LOGGER.error(f"加载MOT结果失败: {e}")
            return False

    def _parse_file(self) -> bool:
        """解析MOT结果文件"""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                        
                    parts = line.split(",")
                    if len(parts) < 6:
                        LOGGER.warning(f"第{line_num}行格式错误: {line}")
                        continue
                        
                    try:
                        frame_id = int(parts[0])
                        track_id = int(parts[1])
                        x = float(parts[2])
                        y = float(parts[3])
                        width = float(parts[4])
                        height = float(parts[5])
                        confidence = float(parts[6]) if len(parts) > 6 else 1.0
                        
                        track = MOTTrack(
                            track_id=track_id,
                            frame_id=frame_id,
                            x=x,
                            y=y,
                            width=width,
                            height=height,
                            confidence=confidence
                        )
                        
                        self._tracks.append(track)
                        self._track_ids.add(track_id)
                        
                        if frame_id not in self._frame_tracks:
                            self._frame_tracks[frame_id] = []
                        self._frame_tracks[frame_id].append(track)
                        
                    except (ValueError, IndexError) as e:
                        LOGGER.warning(f"第{line_num}行解析失败: {e}")
                        continue
            
            LOGGER.info(f"解析完成: 总帧数={len(self._frame_tracks)}, 总目标数={len(self._track_ids)}")
            return True
            
        except Exception as e:
            LOGGER.error(f"解析文件失败: {e}")
            return False
            
    def get_tracks_for_frame(self, frame_id: int) -> List[MOTTrack]:
        """获取指定帧的所有跟踪目标"""
        return self._frame_tracks.get(frame_id, [])
        
    def get_track_by_id(self, track_id: int) -> List[MOTTrack]:
        """获取指定ID的所有跟踪记录"""
        return [track for track in self._tracks if track.track_id == track_id]
        
    def get_frame_range_with_data(self) -> Tuple[int, int]:
        """获取有数据的帧范围"""
        if not self._frame_tracks:
            return (0, 0)
        frames = sorted(self._frame_tracks.keys())
        return (min(frames), max(frames))
        
    def get_tracks_for_frames(self, start_frame: int, count: int) -> Dict[int, List[MOTTrack]]:
        """获取连续多帧的跟踪结果"""
        results = {}
        for i in range(count):
            frame_id = start_frame + i
            if frame_id in self._frame_tracks:
                results[frame_id] = self._frame_tracks[frame_id]
        return results
        
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_frames": len(self._frame_tracks),
            "total_tracks": len(self._track_ids),
            "frame_range": self.frame_range,
            "min_frame": min(self._frame_tracks.keys()) if self._frame_tracks else 0,
            "max_frame": max(self._frame_tracks.keys()) if self._frame_tracks else 0,
            "avg_tracks_per_frame": len(self._tracks) / len(self._frame_tracks) if self._frame_tracks else 0
        }


class MOTResultLoader:
    """MOT结果加载器 - 用于批量加载和管理多个结果文件"""
    
    def __init__(self):
        self.results: Dict[str, MOTResult] = {}
        
    def add_result_file(self, file_path: str, algorithm_name: str = None) -> Optional[MOTResult]:
        """添加MOT结果文件"""
        try:
            result = MOTResult(file_path)
            if result.load():
                key = algorithm_name or result.sequence_name
                self.results[key] = result
                return result
        except Exception as e:
            LOGGER.error(f"添加结果文件失败: {e}")
        return None
        
    def add_result_directory(self, directory: str, algorithm_name: str) -> Dict[str, MOTResult]:
        """添加算法结果目录"""
        directory = Path(directory)
        if not directory.exists():
            LOGGER.error(f"目录不存在: {directory}")
            return {}
            
        txt_files = list(directory.glob("*.txt"))
        added_results = {}
        
        for txt_file in txt_files:
            result = self.add_result_file(str(txt_file), algorithm_name)
            if result:
                added_results[result.sequence_name] = result
                
        return added_results
        
    def get_result(self, algorithm_name: str, sequence_name: str) -> Optional[MOTResult]:
        """获取指定算法和序列的结果"""
        key = f"{algorithm_name}_{sequence_name}"
        return self.results.get(key)
        
    def get_all_sequences(self) -> List[str]:
        """获取所有序列名称"""
        sequences = set()
        for result in self.results.values():
            sequences.add(result.sequence_name)
        return sorted(list(sequences))
        
    def get_algorithms_for_sequence(self, sequence_name: str) -> List[str]:
        """获取支持指定序列的所有算法"""
        algorithms = []
        for key, result in self.results.items():
            if result.sequence_name == sequence_name:
                # 从key中提取算法名称
                if "_" in key:
                    algo_name = key.split("_")[0]
                    algorithms.append(algo_name)
                else:
                    algorithms.append(key)
        return sorted(list(set(algorithms)))