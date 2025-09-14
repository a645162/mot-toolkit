"""结果绘制器 - 集成plot_result.py功能到GUI"""

import os
import cv2
import numpy as np
from typing import List, Dict, Tuple
from PySide6.QtCore import QObject, Signal, QThread
from mot_toolkit.utils.logs import get_logger

LOGGER = get_logger()


class ResultPlotter(QObject):
    """结果绘制器 - 将MOT结果绘制到图像上"""

    progress_updated = Signal(int, int)  # 当前进度, 总进度
    plot_completed = Signal(str)  # 输出目录路径
    plot_error = Signal(str)  # 错误信息

    def __init__(self):
        super().__init__()
        self.colors = {}
        self.max_colors = 50
        self.color_map = {}
        self.config = {
            "show_bbox": True,
            "show_id": True,
            "bbox_thickness": 2,
            "fill_alpha": 0.3,
            "show_fill": True,
        }

    def set_config(self, config: dict):
        """设置绘制配置"""
        self.config.update(config)

    def generate_colors(self, num_colors: int) -> List[Tuple[int, int, int]]:
        """生成颜色列表"""
        colors = []
        for i in range(num_colors):
            hue = i / max(1, num_colors)
            hsv_color = np.array([[[hue * 180, 0.8 * 255, 0.9 * 255]]], dtype=np.uint8)
            bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR).flatten()
            colors.append((int(bgr_color[0]), int(bgr_color[1]), int(bgr_color[2])))
        return colors

    def parse_mot_result(self, file_path: str) -> Dict[int, List[Dict]]:
        """解析MOT结果文件"""
        detections = {}

        try:
            with open(file_path, "r") as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                parts = line.split(",")
                if len(parts) < 6:
                    continue

                try:
                    frame_idx = int(parts[0])
                    track_id = int(parts[1])
                    x1 = float(parts[2])
                    y1 = float(parts[3])
                    width = float(parts[4])
                    height = float(parts[5])
                    confidence = float(parts[6]) if len(parts) > 6 else 1.0

                    detection = {
                        "track_id": track_id,
                        "x1": x1,
                        "y1": y1,
                        "x2": x1 + width,
                        "y2": y1 + height,
                        "width": width,
                        "height": height,
                        "confidence": confidence,
                    }

                    if frame_idx not in detections:
                        detections[frame_idx] = []
                    detections[frame_idx].append(detection)

                except (ValueError, IndexError):
                    continue

        except Exception as e:
            self.plot_error.emit(f"解析文件失败: {str(e)}")
            return {}

        return detections

    def draw_bbox(
        self,
        img: np.ndarray,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        color: Tuple[int, int, int],
        thickness: int = None,
    ) -> None:
        """绘制边界框"""
        if not self.config.get("show_bbox", True):
            return

        pt1 = (int(round(x1)), int(round(y1)))
        pt2 = (int(round(x2)), int(round(y2)))
        # 如果指定了线宽，使用指定线宽，否则使用配置的线宽
        draw_thickness = thickness if thickness is not None else self.config.get("bbox_thickness", 2)
        cv2.rectangle(img, pt1, pt2, color, draw_thickness)

        # 绘制半透明填充
        if self.config.get("show_fill", True):
            alpha = self.config.get("fill_alpha", 0.3)
            overlay = img.copy()
            cv2.rectangle(overlay, pt1, pt2, color, -1)
            cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

    def draw_track_id(
        self,
        img: np.ndarray,
        track_id: int,
        x: float,
        y: float,
        color: Tuple[int, int, int],
    ) -> None:
        """绘制跟踪ID"""
        if not self.config.get("show_id", True):
            return

        text = f"ID:{track_id}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2

        (text_width, text_height), baseline = cv2.getTextSize(
            text, font, font_scale, thickness
        )

        # 绘制背景
        background_y1 = max(0, int(y) - text_height - baseline - 5)
        background_y2 = int(y) - baseline + 5

        cv2.rectangle(
            img,
            (int(x), background_y1),
            (int(x) + text_width, background_y2),
            (0, 0, 0),
            cv2.FILLED,
        )

        # 绘制文本
        cv2.putText(
            img,
            text,
            (int(x), int(y) - baseline),
            font,
            font_scale,
            color,
            thickness,
            cv2.LINE_AA,
        )

    def draw_results_on_frame(
        self, frame: np.ndarray, results: List[Dict], algorithm_name: str = "",
        color: Tuple[int, int, int] = None, thickness: int = None
    ) -> np.ndarray:
        """在帧上绘制跟踪结果"""
        if not results:
            LOGGER.debug("[ResultPlotter] 没有结果需要绘制")
            return frame

        # 获取所有跟踪ID
        track_ids = [det["track_id"] for det in results]
        unique_ids = sorted(set(track_ids))

        LOGGER.debug(
            f"[ResultPlotter] 算法={algorithm_name}, 结果数量={len(results)}, 唯一ID数量={len(unique_ids)}"
        )

        # 为算法生成颜色映射（如果还没有）
        if algorithm_name not in self.color_map:
            colors = self.generate_colors(len(unique_ids))
            self.color_map[algorithm_name] = {
                tid: colors[i % len(colors)] for i, tid in enumerate(unique_ids)
            }

        color_map = self.color_map[algorithm_name]

        # 创建图像副本
        result_img = frame.copy()

        # 绘制每个检测结果
        for i, det in enumerate(results):
            track_id = det["track_id"]
            # 如果指定了颜色，使用指定颜色，否则使用算法颜色映射
            if color is not None:
                draw_color = color
            else:
                draw_color = color_map.get(track_id, (255, 0, 255))  # 默认紫色

            # 如果指定了线宽，使用指定线宽，否则使用配置的线宽
            draw_thickness = thickness if thickness is not None else self.config.get("bbox_thickness", 2)

            LOGGER.debug(
                f"[ResultPlotter] 绘制第{i + 1}个结果: ID={track_id}, 坐标=({det['x1']:.1f}, {det['y1']:.1f}, {det['x2']:.1f}, {det['y2']:.1f})"
            )

            # 绘制边界框
            self.draw_bbox(
                result_img,
                det["x1"],
                det["y1"],
                det["x2"],
                det["y2"],
                draw_color,
                thickness=draw_thickness,
            )

            # 绘制跟踪ID
            self.draw_track_id(result_img, track_id, det["x1"], det["y1"], draw_color)

        return result_img

    def plot_sequence(
        self,
        algorithm_path: str,
        sequence_path: str,
        output_dir: str,
        sequence_name: str,
        render_config: dict = None
    ) -> bool:
        """绘制单个序列的结果"""
        try:
            # 获取结果文件路径
            result_file = os.path.join(algorithm_path, f"{sequence_name}.txt")
            if not os.path.exists(result_file):
                return False

            # 解析结果
            detections = self.parse_mot_result(result_file)
            if not detections:
                return False

            # 获取图像目录
            img_dir = os.path.join(sequence_path, "img1")
            if not os.path.exists(img_dir):
                return False

            # 获取所有图像文件
            img_files = sorted(
                [
                    f
                    for f in os.listdir(img_dir)
                    if f.lower().endswith((".jpg", ".jpeg", ".png"))
                ]
            )

            if not img_files:
                return False

            # 生成颜色
            track_ids = set()
            for frame_dets in detections.values():
                for det in frame_dets:
                    track_ids.add(det["track_id"])

            colors = self.generate_colors(len(track_ids))
            color_map = {
                tid: colors[i % len(colors)] for i, tid in enumerate(sorted(track_ids))
            }

            # 创建输出目录
            output_seq_dir = os.path.join(output_dir, sequence_name)
            os.makedirs(output_seq_dir, exist_ok=True)

            # 处理每一帧
            total_frames = len(img_files)
            for idx, img_file in enumerate(img_files):
                img_path = os.path.join(img_dir, img_file)
                img = cv2.imread(img_path)
                if img is None:
                    continue

                # 应用渲染配置
                if render_config:
                    img = self._apply_render_config(img, render_config)

                # 获取帧索引
                try:
                    frame_idx = int(os.path.splitext(img_file)[0])
                except ValueError:
                    frame_idx = idx + 1

                # 绘制检测结果
                if frame_idx in detections:
                    for det in detections[frame_idx]:
                        color = color_map.get(det["track_id"], (255, 0, 255))
                        self.draw_bbox(
                            img, det["x1"], det["y1"], det["x2"], det["y2"], color
                        )
                        self.draw_track_id(
                            img, det["track_id"], det["x1"], det["y1"], color
                        )

                # 保存结果
                output_path = os.path.join(output_seq_dir, img_file)
                cv2.imwrite(output_path, img, [cv2.IMWRITE_JPEG_QUALITY, render_config.get("quality", 85) if render_config else 85])

                # 发送进度信号
                self.progress_updated.emit(idx + 1, total_frames)

            return True

        except Exception as e:
            self.plot_error.emit(str(e))
            return False
            
    def _apply_render_config(self, img, render_config):
        """应用渲染配置到图像"""
        if render_config.get("render_mode") == "limit_resolution":
            h, w = img.shape[:2]
            max_width = render_config.get("max_width", 800)
            max_height = render_config.get("max_height", 600)
            
            if w > max_width or h > max_height:
                # 计算缩放比例
                scale = min(max_width / w, max_height / h)
                new_width = int(w * scale)
                new_height = int(h * scale)
                
                # 使用高质量缩放
                img = cv2.resize(img, (new_width, new_height),
                               interpolation=cv2.INTER_LANCZOS4)
        
        return img

    def plot_all_algorithms(self, config: dict, output_base_dir: str) -> None:
        """绘制所有算法的结果"""
        try:
            algorithms = config.get("algorithms", {})
            sequence_paths = config.get("sequence_paths", {})
            render_config = config.get("render_config", {})

            if not algorithms or not sequence_paths:
                self.plot_error.emit("没有算法或序列数据")
                return

            total_algorithms = len(algorithms)
            current_algo = 0

            for algo_name, algo_path in algorithms.items():
                current_algo += 1
                output_dir = os.path.join(output_base_dir, algo_name)

                # 为每个序列绘制结果
                for seq_name, seq_path in sequence_paths.items():
                    self.plot_sequence(algo_path, seq_path, output_dir, seq_name, render_config)

            self.plot_completed.emit(output_base_dir)

        except Exception as e:
            self.plot_error.emit(str(e))


class PlotThread(QThread):
    """绘制线程"""

    def __init__(self, plotter: ResultPlotter, config: dict, output_dir: str):
        super().__init__()
        self.plotter = plotter
        self.config = config
        self.output_dir = output_dir

    def run(self):
        """运行绘制"""
        self.plotter.plot_all_algorithms(self.config, self.output_dir)
