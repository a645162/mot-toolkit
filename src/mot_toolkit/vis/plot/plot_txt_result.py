"""
BV14C4y13752-qtZR69rqL543PVoe_00000000-00000744.txt

Format:
frame_index,track_id,center_y,width,height,confidence,class,visibility,unused
1,0,247.25921630859375,574.379638671875,412.816162109375,52.2425537109375,1,-1,-1,-1
"""

import os
import cv2
import logging
import shutil
import time
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from multiprocessing import Pool
from tqdm import tqdm

# 新增导入
from mot_toolkit.config.hardware import cpu_count
from mot_toolkit.vis.scheme.genshin.sigewinne_colors import SIGEWINNEColorScheme

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class Config:
    """配置类"""

    txt_dir_path: str = (
        "/home/konghaomin/MOTIP/inference_outputs/MT_All_mt_anchor_v4_ffn_v2_c_20250624164142/submit/default/DanceTrack/val/checkpoint_8/tracker"
    )
    val_seq_dir_path: str = (
        "/dev/shm/konghaomin/Datasets/MaritimeTrack_20250322/DanceTrack/val"
    )
    output_dir_name: str = "plot_img"
    
    # 视频和图像设置
    max_width: int = 1920
    max_height: int = 1080
    save_frames: bool = True
    
    # 显示设置
    show_frame_text: bool = True
    show_frame_progress: bool = True
    show_frame_object_count: bool = True
    
    # 框和渲染设置
    show_box: bool = True
    different_color: bool = True
    with_text: bool = True
    center_point_trajectory: bool = True
    thickness: int = 3
    
    # 矩形填充设置
    fill_rectangle: bool = True
    fill_alpha: float = 0.25
    
    # 颜色设置 (BGR格式)
    box_color: Tuple[int, int, int] = (0, 255, 0)
    selected_color: Tuple[int, int, int] = (0, 255, 255)
    text_color: Tuple[int, int, int] = (0, 0, 255)
    
    # 缩放设置
    text_scale: float = 0.8
    
    # 多进程设置
    use_multiprocessing: bool = True
    max_workers: Optional[int] = max(4, cpu_count // 2)


class MOTResultVisualizer:
    """MOT结果可视化器"""

    def __init__(self, config: Config):
        self.config = config
        self.output_dir = os.path.join(config.txt_dir_path, config.output_dir_name)
        self.color_scheme = SIGEWINNEColorScheme()
        self.colors = self.color_scheme.bgr_colors()
        self._setup_output_dir()

    def _setup_output_dir(self) -> None:
        """设置输出目录"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"创建输出目录: {self.output_dir}")

    def _validate_paths(self) -> bool:
        """验证路径是否存在"""
        if not os.path.exists(self.config.txt_dir_path):
            logger.error(f"TXT目录不存在: {self.config.txt_dir_path}")
            return False

        if not os.path.exists(self.config.val_seq_dir_path):
            logger.error(f"验证序列目录不存在: {self.config.val_seq_dir_path}")
            return False

        return True

    def _get_txt_files(self) -> List[str]:
        """获取所有txt文件路径"""
        try:
            txt_list = os.listdir(self.config.txt_dir_path)
            txt_list = [
                f
                for f in txt_list
                if f.endswith(".txt") and "pedestrian_summary.txt" not in f
            ]
            txt_list = [os.path.join(self.config.txt_dir_path, f) for f in txt_list]
            logger.info(f"找到 {len(txt_list)} 个txt文件")
            return txt_list
        except OSError as e:
            logger.error(f"读取txt目录失败: {e}")
            return []

    def _parse_txt_content(self, txt_path: str) -> List[List[int]]:
        """解析txt文件内容"""
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            content = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    values = [float(x) for x in line.split(",")]
                    content.append([int(x) for x in values])
                except ValueError as e:
                    logger.warning(f"跳过无效行: {line}, 错误: {e}")
                    continue

            return content
        except (IOError, UnicodeDecodeError) as e:
            logger.error(f"读取文件失败 {txt_path}: {e}")
            return []

    def _get_sequence_images(self, seq_name: str) -> List[str]:
        """获取序列图像列表"""
        seq_dir_path = os.path.join(self.config.val_seq_dir_path, seq_name, "img1")

        if not os.path.exists(seq_dir_path):
            logger.warning(f"序列目录不存在: {seq_dir_path}")
            return []

        try:
            img_list = [f for f in os.listdir(seq_dir_path) if f.endswith(".jpg")]
            img_list.sort()
            return [os.path.join(seq_dir_path, img) for img in img_list]
        except OSError as e:
            logger.error(f"读取图像目录失败 {seq_dir_path}: {e}")
            return []

    def _generate_color_dict(self, txt_content: List[List[int]]) -> Dict[int, Tuple[int, int, int]]:
        """生成目标ID到颜色的映射字典"""
        if not self.config.different_color:
            return {}
            
        # 收集所有唯一的track_id
        all_ids = set()
        for annotation in txt_content:
            if len(annotation) >= 2:
                all_ids.add(annotation[1])  # track_id在索引1
        
        # 为每个ID分配颜色
        color_dict = {}
        for i, track_id in enumerate(sorted(all_ids)):
            color_dict[track_id] = self.colors[i % len(self.colors)]
        
        return color_dict

    def _draw_filled_rectangle(self, img, pt1: Tuple[int, int], pt2: Tuple[int, int], 
                             color: Tuple[int, int, int], alpha: float = 0.3):
        """绘制填充的半透明矩形"""
        if not self.config.fill_rectangle or alpha <= 0:
            return
            
        # 创建覆盖层
        overlay = img.copy()
        cv2.rectangle(overlay, pt1, pt2, color, -1)
        
        # 混合原图和覆盖层
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

    def _draw_annotations(self, img, annotations: List[List[int]], 
                         color_dict: Dict[int, Tuple[int, int, int]],
                         center_point_trajectory: Dict[int, List[Tuple[int, int]]]) -> None:
        """在图像上绘制标注（模仿GT绘制方式）"""
        for annotation in annotations:
            if len(annotation) < 6:
                continue

            track_id = annotation[1]
            x1, y1, w, h = annotation[2:6]
            x2, y2 = x1 + w, y1 + h
            
            # 计算中心点
            center_x = x1 + w // 2
            center_y = y1 + h // 2
            
            # 选择颜色
            if self.config.different_color and track_id in color_dict:
                color = color_dict[track_id]
            else:
                color = self.config.box_color

            # 绘制填充矩形
            if self.config.fill_rectangle:
                self._draw_filled_rectangle(img, (x1, y1), (x2, y2), color, self.config.fill_alpha)

            # 绘制边界框
            cv2.rectangle(img, (x1, y1), (x2, y2), color, self.config.thickness)

            # 绘制轨迹
            if self.config.center_point_trajectory:
                if track_id not in center_point_trajectory:
                    center_point_trajectory[track_id] = []
                
                center_point_trajectory[track_id].append((center_x, center_y))
                
                # 限制轨迹长度
                if len(center_point_trajectory[track_id]) > 30:
                    center_point_trajectory[track_id] = center_point_trajectory[track_id][-30:]
                
                # 绘制轨迹点
                trajectory_points = center_point_trajectory[track_id]
                for i in range(1, len(trajectory_points)):
                    cv2.line(img, trajectory_points[i-1], trajectory_points[i], color, 2)

            # 绘制ID文本
            if self.config.with_text:
                text = f"ID{track_id}"
                # 计算文本尺寸
                (text_width, text_height), baseline = cv2.getTextSize(
                    text, cv2.FONT_HERSHEY_SIMPLEX, self.config.text_scale, 2
                )
                
                # 绘制文本背景
                text_x, text_y = x1, y1 - 10
                if text_y - text_height < 0:
                    text_y = y1 + text_height + 10
                
                cv2.rectangle(
                    img, 
                    (text_x, text_y - text_height - baseline),
                    (text_x + text_width, text_y + baseline),
                    color,
                    -1
                )
                
                # 绘制文本
                cv2.putText(
                    img, text, (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, self.config.text_scale,
                    (255, 255, 255), 2
                )

    def _add_frame_info(self, img, frame_index: int, total_frames: int, 
                       object_count: int) -> None:
        """添加帧信息文本"""
        if not self.config.show_frame_text:
            return
            
        text_list = []
        if self.config.show_frame_progress:
            text_list.append(f"Frame: {frame_index}/{total_frames}")
        if self.config.show_frame_object_count:
            text_list.append(f"Objects: {object_count}")
        
        if text_list:
            text = " | ".join(text_list)
            cv2.putText(
                img, text, (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, 
                self.config.text_color, 2
            )

    def _process_single_txt(self, txt_path: str) -> None:
        """处理单个txt文件"""
        try:
            txt_name = os.path.basename(txt_path)
            txt_name_no_ext = os.path.splitext(txt_name)[0]

            logger.info(f"处理: {txt_name}")

            # 解析txt内容
            txt_content = self._parse_txt_content(txt_path)
            if not txt_content:
                logger.warning(f"文件为空或无法解析: {txt_path}")
                return

            # 生成颜色字典
            color_dict = self._generate_color_dict(txt_content)
            
            # 获取图像列表
            img_list = self._get_sequence_images(txt_name_no_ext)
            if not img_list:
                logger.warning(f"未找到图像序列: {txt_name_no_ext}")
                return

            # 创建保存目录
            save_dir = os.path.join(self.output_dir, txt_name_no_ext)
            if os.path.exists(save_dir):
                shutil.rmtree(save_dir)
            os.makedirs(save_dir, exist_ok=True)

            # 轨迹字典
            center_point_trajectory = {}
            total_frames = len(img_list)

            # 处理每一帧
            for frame_idx, img_path in enumerate(img_list):
                img_name = os.path.basename(img_path)
                img_name_no_ext = os.path.splitext(img_name)[0]
                save_path = os.path.join(save_dir, img_name)

                try:
                    frame_index = int(img_name_no_ext)
                except ValueError:
                    logger.warning(f"无法解析帧索引: {img_name_no_ext}")
                    continue

                # 筛选当前帧的标注
                frame_annotations = [
                    ann for ann in txt_content if ann[0] == frame_index
                ]

                # 读取图像
                img = cv2.imread(img_path)
                if img is None:
                    logger.warning(f"无法读取图像: {img_path}")
                    continue

                # 应用缩放
                original_height, original_width = img.shape[:2]
                scale_ratio = 1
                if self.config.max_width > 0 or self.config.max_height > 0:
                    width_ratio = self.config.max_width / original_width if self.config.max_width > 0 else 1
                    height_ratio = self.config.max_height / original_height if self.config.max_height > 0 else 1
                    scale_ratio = min(width_ratio, height_ratio)
                
                if scale_ratio != 1:
                    new_width = int(original_width * scale_ratio)
                    new_height = int(original_height * scale_ratio)
                    img = cv2.resize(img, (new_width, new_height))
                    
                    # 缩放标注坐标
                    scaled_annotations = []
                    for ann in frame_annotations:
                        if len(ann) >= 6:
                            scaled_ann = ann.copy()
                            scaled_ann[2] = int(ann[2] * scale_ratio)  # x
                            scaled_ann[3] = int(ann[3] * scale_ratio)  # y
                            scaled_ann[4] = int(ann[4] * scale_ratio)  # w
                            scaled_ann[5] = int(ann[5] * scale_ratio)  # h
                            scaled_annotations.append(scaled_ann)
                    frame_annotations = scaled_annotations

                # 绘制标注
                if self.config.show_box:
                    self._draw_annotations(img, frame_annotations, color_dict, center_point_trajectory)

                # 添加帧信息
                self._add_frame_info(img, frame_index, total_frames, len(frame_annotations))

                # 保存图像
                if not cv2.imwrite(save_path, img):
                    logger.warning(f"保存图像失败: {save_path}")

        except Exception as e:
            logger.error(f"处理txt文件失败 {txt_path}: {e}")

    def visualize(self) -> None:
        """执行可视化"""
        main_start_time = time.time()
        print(f"程序开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 验证路径
        if not self._validate_paths():
            return

        # 清理输出目录
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        self._setup_output_dir()

        # 获取txt文件列表
        txt_list = self._get_txt_files()
        if not txt_list:
            logger.error("未找到有效的txt文件")
            return

        print(f"找到 {len(txt_list)} 个txt文件")
        print("文件列表:")
        for txt_file in txt_list:
            print(f"  - {os.path.basename(txt_file)}")

        input("按回车键开始处理...")
        logger.info("开始处理...")

        processing_start_time = time.time()
        
        # 使用多进程或单进程处理
        if self.config.use_multiprocessing and len(txt_list) > 1:
            print(f"使用 {self.config.max_workers} 个进程并行处理")
            with Pool(processes=self.config.max_workers) as pool:
                list(
                    tqdm(
                        pool.imap(self._process_single_txt, txt_list),
                        total=len(txt_list),
                        desc="处理进度",
                    )
                )
        else:
            for txt_path in tqdm(txt_list, desc="处理进度"):
                self._process_single_txt(txt_path)

        processing_end_time = time.time()
        total_processing_time = processing_end_time - processing_start_time
        total_main_time = processing_end_time - main_start_time

        print(f"\n{'='*50}")
        print(f"处理完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"处理总用时: {timedelta(seconds=int(total_processing_time))}")
        print(f"程序总运行时间: {timedelta(seconds=int(total_main_time))}")
        if len(txt_list) > 0:
            avg_time_per_file = total_processing_time / len(txt_list)
            print(f"平均每个文件处理时间: {timedelta(seconds=int(avg_time_per_file))}")
        print(f"结果保存在: {self.output_dir}")
        print(f"{'='*50}")


def main():
    """主函数"""
    config = Config()
    visualizer = MOTResultVisualizer(config)
    visualizer.visualize()


if __name__ == "__main__":
    main()
