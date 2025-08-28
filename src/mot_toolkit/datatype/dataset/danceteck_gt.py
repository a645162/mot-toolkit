"""DanceTrack数据集GT（Ground Truth）读取器"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from mot_toolkit.utils.logs import get_logger

LOGGER = get_logger()


@dataclass
class DanceTrackGT:
    """DanceTrack GT数据结构"""
    frame_id: int
    track_id: int
    x: float
    y: float
    width: float
    height: float
    confidence: float = 1.0
    class_id: int = 1  # 通常为1（行人）


class DanceTrackGTReader:
    """DanceTrack GT读取器"""
    
    def __init__(self):
        self.gt_data: Dict[int, List[DanceTrackGT]] = {}  # frame_id -> list of GT
        self.track_ids: set = set()
        
    def load_gt_file(self, gt_file_path: str) -> bool:
        """
        加载GT文件
        
        Args:
            gt_file_path: GT文件路径（通常是seq/gt/gt.txt）
            
        Returns:
            是否加载成功
        """
        gt_file = Path(gt_file_path)
        if not gt_file.exists():
            LOGGER.error(f"GT文件不存在: {gt_file_path}")
            return False
            
        try:
            with open(gt_file, "r", encoding="utf-8") as f:
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
                        class_id = int(parts[7]) if len(parts) > 7 else 1
                        
                        gt = DanceTrackGT(
                            frame_id=frame_id,
                            track_id=track_id,
                            x=x,
                            y=y,
                            width=width,
                            height=height,
                            confidence=confidence,
                            class_id=class_id
                        )
                        
                        if frame_id not in self.gt_data:
                            self.gt_data[frame_id] = []
                        self.gt_data[frame_id].append(gt)
                        self.track_ids.add(track_id)
                        
                    except (ValueError, IndexError) as e:
                        LOGGER.warning(f"第{line_num}行解析失败: {e}")
                        continue
                        
            LOGGER.info(f"GT加载完成: 总帧数={len(self.gt_data)}, 总目标数={len(self.track_ids)}")
            return True
            
        except Exception as e:
            LOGGER.error(f"加载GT文件失败: {e}")
            return False
            
    def get_gt_for_frame(self, frame_id: int) -> List[DanceTrackGT]:
        """获取指定帧的GT数据"""
        return self.gt_data.get(frame_id, [])
        
    def get_gt_for_frames(self, start_frame: int, count: int) -> Dict[int, List[DanceTrackGT]]:
        """获取连续多帧的GT数据"""
        results = {}
        for i in range(count):
            frame_id = start_frame + i
            if frame_id in self.gt_data:
                results[frame_id] = self.gt_data[frame_id]
        return results
        
    def get_frame_range(self) -> tuple:
        """获取有GT数据的帧范围"""
        if not self.gt_data:
            return (0, 0)
        frames = sorted(self.gt_data.keys())
        return (min(frames), max(frames))
        
    def convert_to_mot_format(self, frame_id: int) -> List[Dict]:
        """转换为MOT格式（用于绘制）"""
        gts = self.get_gt_for_frame(frame_id)
        results = []
        for gt in gts:
            results.append({
                "track_id": gt.track_id,
                "x1": gt.x,
                "y1": gt.y,
                "x2": gt.x + gt.width,
                "y2": gt.y + gt.height,
                "width": gt.width,
                "height": gt.height,
                "confidence": gt.confidence,
                "class_id": gt.class_id,
                "is_gt": True  # 标记为GT数据
            })
        return results


def find_gt_file(sequence_path: str) -> Optional[str]:
    """
    在序列目录中查找GT文件
    
    Args:
        sequence_path: 序列目录路径
        
    Returns:
        GT文件路径，如果找不到返回None
    """
    seq_path = Path(sequence_path)
    
    # 检查标准DanceTrack格式：seq/gt/gt.txt
    gt_path = seq_path / "gt" / "gt.txt"
    if gt_path.exists():
        return str(gt_path)
        
    # 检查其他可能的位置
    possible_paths = [
        seq_path / "gt.txt",
        seq_path / "annotations.txt",
        seq_path / "labels.txt",
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path)
            
    return None