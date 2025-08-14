"""MOT结果解析器"""

from typing import Dict, List


class MOTResultParser:
    """MOT结果解析器"""

    @staticmethod
    def parse_result_file(file_path: str) -> Dict[int, List[Dict]]:
        """解析MOT结果文件

        Args:
            file_path: MOT结果文件路径

        Returns:
            按帧号组织的跟踪结果字典
        """
        results = {}

        try:
            with open(file_path, "r") as f:
                for line in f:
                    parts = line.strip().split(",")
                    if len(parts) >= 7:
                        frame_id = int(parts[0])
                        track_id = int(parts[1])
                        x, y, w, h = (
                            float(parts[2]),
                            float(parts[3]),
                            float(parts[4]),
                            float(parts[5]),
                        )
                        confidence = float(parts[6])

                        if frame_id not in results:
                            results[frame_id] = []

                        results[frame_id].append(
                            {
                                "track_id": track_id,
                                "bbox": [x, y, w, h],
                                "confidence": confidence,
                            }
                        )
        except Exception as e:
            print(f"解析文件失败 {file_path}: {e}")

        return results

    @staticmethod
    def parse_results_for_frames(
        file_path: str, start_frame: int, count: int = 5
    ) -> Dict[int, List[Dict]]:
        """解析指定帧范围的结果

        Args:
            file_path: MOT结果文件路径
            start_frame: 起始帧号（从0开始）
            count: 帧数

        Returns:
            指定帧范围的跟踪结果
        """
        all_results = MOTResultParser.parse_result_file(file_path)

        # MOT结果通常从1开始计数
        frame_results = {}
        for i in range(count):
            frame_id = start_frame + i + 1
            if frame_id in all_results:
                frame_results[i] = all_results[frame_id]

        return frame_results
