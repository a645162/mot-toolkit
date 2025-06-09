"""
BV14C4y13752-qtZR69rqL543PVoe_00000000-00000744.txt

Format:
frame_index,track_id,center_y,width,height,confidence,class,visibility,unused
1,0,247.25921630859375,574.379638671875,412.816162109375,52.2425537109375,1,-1,-1,-1
"""

import os
import cv2
import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass
from multiprocessing import Pool
from tqdm import tqdm

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class Config:
    """配置类"""

    txt_dir_path: str = (
        "/home/konghaomin/me-motr-modify/outputs/MeMOTR_MaritimeTrack_Full_Same_523/val/checkpoint_19_tracker"
    )
    val_seq_dir_path: str = (
        "/home/konghaomin/Datasets/MaritimeTrackAllData/Spilt/523/MaritimeTrack/val"
    )
    output_dir_name: str = "plot_img"
    box_color: Tuple[int, int, int] = (0, 255, 0)
    box_thickness: int = 2
    text_scale: float = 1.0
    use_multiprocessing: bool = True
    max_workers: Optional[int] = None


class MOTResultVisualizer:
    """MOT结果可视化器"""

    def __init__(self, config: Config):
        self.config = config
        self.output_dir = os.path.join(config.txt_dir_path, config.output_dir_name)
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

    def _draw_annotations(self, img, annotations: List[List[int]]) -> None:
        """在图像上绘制标注"""
        for annotation in annotations:
            if len(annotation) < 6:
                continue

            track_id = annotation[1]
            x1, y1, w, h = annotation[2:6]
            x2, y2 = x1 + w, y1 + h

            # 绘制边界框
            cv2.rectangle(
                img,
                (x1, y1),
                (x2, y2),
                self.config.box_color,
                self.config.box_thickness,
            )

            # 绘制ID文本
            text = f"ID{track_id}"
            cv2.putText(
                img,
                text,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                self.config.text_scale,
                self.config.box_color,
                self.config.box_thickness,
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

            # 获取图像列表
            img_list = self._get_sequence_images(txt_name_no_ext)
            if not img_list:
                logger.warning(f"未找到图像序列: {txt_name_no_ext}")
                return

            # 创建保存目录
            save_dir = os.path.join(self.output_dir, txt_name_no_ext)
            os.makedirs(save_dir, exist_ok=True)

            # 处理每一帧
            for img_path in img_list:
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

                # 读取并处理图像
                img = cv2.imread(img_path)
                if img is None:
                    logger.warning(f"无法读取图像: {img_path}")
                    continue

                # 绘制标注
                self._draw_annotations(img, frame_annotations)

                # 保存图像
                if not cv2.imwrite(save_path, img):
                    logger.warning(f"保存图像失败: {save_path}")

        except Exception as e:
            logger.error(f"处理txt文件失败 {txt_path}: {e}")

    def visualize(self) -> None:
        """执行可视化"""
        # 验证路径
        if not self._validate_paths():
            return

        # 获取txt文件列表
        txt_list = self._get_txt_files()
        if not txt_list:
            logger.error("未找到有效的txt文件")
            return

        print(f"找到 {len(txt_list)} 个txt文件")
        print("文件列表:")
        for txt_file in txt_list:
            print(f"  - {txt_file}")

        input("按回车键开始处理...")
        logger.info("开始处理...")

        # 使用多进程或单进程处理
        if self.config.use_multiprocessing and len(txt_list) > 1:
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

        logger.info("处理完成!")
        print(f"结果保存在: {self.output_dir}")


def main():
    """主函数"""
    config = Config()
    visualizer = MOTResultVisualizer(config)
    visualizer.visualize()


if __name__ == "__main__":
    main()
