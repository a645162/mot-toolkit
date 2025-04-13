import multiprocessing
import os
import shutil
import json
from enum import Enum

from typing import List, Tuple, Dict, Any

from mot_toolkit.config.hardware import io_cpu_count
from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list
from mot_toolkit.datatype.dataset.dataset_spilt import DatasetSpilt
from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotationDirectory
from mot_toolkit.utils.logs import get_logger

logger = get_logger()


class ReplaceMode(Enum):
    DELETE_AND_CREATE = 1  # 存在时删除后重新创建
    SKIP_IF_EXISTS = 2  # 存在就跳过
    IGNORE = 3  # 无视

    def __str__(self):
        return self.name


class SpiltBDD100K:
    # DanceTrack is 8
    # MOT Challenge is 6
    file_name_length = 8
    file_name_start = 1

    process_count: int = 1
    multiprocess_mode: bool = True
    multiprocess_task_params: List[Tuple] = []

    replace_mode: ReplaceMode = ReplaceMode.DELETE_AND_CREATE

    def __init__(self):
        self.process_count = io_cpu_count

    def handle_bdd100k_sequence(self, sequence_dir: str, target_dir: str):
        if not os.path.exists(sequence_dir):
            logger.error("Source Sequence Dir Not Found: " + sequence_dir)
            return

        if self.replace_mode == ReplaceMode.DELETE_AND_CREATE:
            # Remove if Exist
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)

            os.makedirs(target_dir, exist_ok=True)
        elif self.replace_mode == ReplaceMode.SKIP_IF_EXISTS:
            if os.path.exists(target_dir):
                logger.info("(SKIP) Target Dir Already Exist: " + target_dir)
                return

        # BDD100K 格式处理
        # 查找对应的图片和标注文件
        image_files = []
        for root, _, files in os.walk(sequence_dir):
            for file in files:
                if file.lower().endswith((".jpg", ".jpeg", ".png")):
                    image_files.append(os.path.join(root, file))

        image_files.sort()

        path_img1 = os.path.join(target_dir, "img1")
        path_gt = os.path.join(target_dir, "gt")
        if not os.path.exists(path_img1):
            os.makedirs(path_img1, exist_ok=True)
        if not os.path.exists(path_gt):
            os.makedirs(path_gt, exist_ok=True)
        path_gt_txt = os.path.join(path_gt, "gt.txt")
        path_seq_info_ini = os.path.join(target_dir, "seqinfo.ini")

        # 处理每个图像及其标注
        gt_lines = []
        frame_width = 0
        frame_height = 0

        for i, img_path in enumerate(image_files):
            current_index = i + self.file_name_start

            # 获取对应的标注文件
            json_path = os.path.splitext(img_path)[0] + ".json"
            if not os.path.exists(json_path):
                logger.warning(f"Annotation file not found for: {img_path}")
                continue

            # 复制图像文件
            target_path_jpeg = os.path.join(
                path_img1, format(current_index, f"0{self.file_name_length}") + ".jpg"
            )

            if os.path.exists(target_path_jpeg):
                # Remove if already exists
                os.remove(target_path_jpeg)

            shutil.copyfile(img_path, target_path_jpeg)

            # 获取图像尺寸（用于生成seqinfo.ini）
            if i == 0:
                from PIL import Image

                with Image.open(img_path) as img:
                    frame_width, frame_height = img.size

            # 解析标注文件
            with open(json_path, "r", encoding="utf-8") as f:
                annotation_data = json.load(f)

            # 处理标注数据 - 生成YOLO格式的txt文件
            yolo_text_list = []
            for obj in annotation_data.get("frames", [{}])[0].get("objects", []):
                if "id" not in obj or "box2d" not in obj:
                    continue

                obj_id = obj.get("id", "")
                category = obj.get("category", "unknown")

                # 获取边界框坐标
                box = obj.get("box2d", {})
                x1 = float(box.get("x1", 0))
                y1 = float(box.get("y1", 0))
                x2 = float(box.get("x2", 0))
                y2 = float(box.get("y2", 0))

                # 计算YOLO格式（中心点坐标和宽高）
                width = x2 - x1
                height = y2 - y1
                center_x = x1 + width / 2
                center_y = y1 + height / 2

                # 转换为相对坐标
                x_ratio = center_x / frame_width if frame_width > 0 else 0
                y_ratio = center_y / frame_height if frame_height > 0 else 0
                w_ratio = width / frame_width if frame_width > 0 else 0
                h_ratio = height / frame_height if frame_height > 0 else 0

                round_count = 6
                x_ratio = round(x_ratio, round_count)
                y_ratio = round(y_ratio, round_count)
                w_ratio = round(w_ratio, round_count)
                h_ratio = round(h_ratio, round_count)

                # 生成YOLO格式的行
                line = (
                    f"{obj_id} " f"{x_ratio} " f"{y_ratio} " f"{w_ratio} " f"{h_ratio}"
                )
                yolo_text_list.append(line)

                # 生成MOT格式的行 (frame,id,x,y,w,h,conf,class,vis)
                gt_line = f"{current_index},{obj_id},{x1},{y1},{width},{height},1,{category},1,0"
                gt_lines.append(gt_line)

            # 保存YOLO格式的txt文件
            yolo_text = "\n".join(yolo_text_list)
            target_path_txt = target_path_jpeg.replace(".jpg", ".txt")
            with open(target_path_txt, "w") as f:
                f.write(yolo_text)

        # 保存gt.txt
        with open(path_gt_txt, "w") as f:
            f.write("\n".join(gt_lines))

        # 生成seqinfo.ini
        seq_name = os.path.basename(target_dir)
        seqinfo_content = f"""[Sequence]
name={seq_name}
imDir=img1
frameRate=30
seqLength={len(image_files)}
imWidth={frame_width}
imHeight={frame_height}
imExt=.jpg"""

        with open(path_seq_info_ini, "w") as f:
            f.write(seqinfo_content)

    def handle_bdd100k_sequence_param(self, sequence_dir: str, target_dir: str):
        return (sequence_dir, target_dir)

    def handle_bdd100k_dir(self, dataset_dir_obj: DatasetSpilt, output_dir: str):
        source_dir = dataset_dir_obj.abs_path

        if not os.path.exists(source_dir):
            logger.error("Source Dir Not Found: " + source_dir)
            return

        sequence_path_list = get_dataset_dir_list(dataset_dir_path=source_dir, depth=1)
        for sequence_path in sequence_path_list:
            target_dir = os.path.join(
                output_dir, dataset_dir_obj.generate_new_name(sequence_path)
            )
            self.multiprocess_task_params.append(
                self.handle_bdd100k_sequence_param(
                    sequence_dir=sequence_path, target_dir=target_dir
                )
            )

    def output_bdd100k_spilt(self, dataset_list: List[DatasetSpilt], output_dir: str):
        logger.info("Output BDD100K")
        logger.info("Dataset List Count: " + str(len(dataset_list)))
        logger.info("Output Dir: " + output_dir)

        for dataset_obj in dataset_list:
            self.handle_bdd100k_dir(dataset_dir_obj=dataset_obj, output_dir=output_dir)

    @staticmethod
    def generate_seq_map(dir_path: str, save_path: str):
        text_lines: List[str] = ["name"]

        # List Dir
        dir_list = os.listdir(dir_path)
        for dir_name in dir_list:
            if os.path.isdir(os.path.join(dir_path, dir_name)):
                text_lines.append(dir_name)

        text = "\n".join(text_lines).strip()

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(text)

    @staticmethod
    def generate_yolo_list_txt(dir_path: str, profile_name: str = "train"):
        image_dir_base = os.path.join(dir_path, profile_name)
        image_list: List[str] = []
        for root, dirs, files in os.walk(image_dir_base):
            for file in files:
                if file.endswith(".jpg"):
                    img_path = os.path.join(root, file)
                    txt_path = img_path.replace(".jpg", ".txt")
                    if os.path.exists(txt_path):
                        rel_path = os.path.relpath(img_path, dir_path)
                        while rel_path.find("\\") != -1:
                            rel_path = rel_path.replace("\\", "/")
                        image_list.append(rel_path)

        text = "\n".join(image_list).strip()
        with open(
            os.path.join(dir_path, f"yolo_{profile_name}.txt"), "w", encoding="utf-8"
        ) as f:
            f.write(text)

    def output_bdd100k(
        self,
        output_bdd100k_dir: str,
        dataset_train_list: List[DatasetSpilt],
        dataset_val_list: List[DatasetSpilt],
        dataset_test_list: List[DatasetSpilt],
    ):
        ## Train
        bdd100k_train_dir = os.path.join(output_bdd100k_dir, "train")
        os.makedirs(bdd100k_train_dir, exist_ok=True)
        self.output_bdd100k_spilt(
            dataset_list=dataset_train_list, output_dir=bdd100k_train_dir
        )

        ## Val
        bdd100k_val_dir = os.path.join(output_bdd100k_dir, "val")
        os.makedirs(bdd100k_val_dir, exist_ok=True)
        self.output_bdd100k_spilt(
            dataset_list=dataset_val_list, output_dir=bdd100k_val_dir
        )

        ## Test
        bdd100k_test_dir = os.path.join(output_bdd100k_dir, "test")
        os.makedirs(bdd100k_test_dir, exist_ok=True)
        self.output_bdd100k_spilt(
            dataset_list=dataset_test_list, output_dir=bdd100k_test_dir
        )

        task_count = len(self.multiprocess_task_params)

        logger.info("Output BDD100K Task Generate Done!")
        logger.info("Output BDD100K Task Count: " + str(task_count))

        logger.info("Start task on " + str(self.process_count) + " CPU Cores")
        if self.multiprocess_mode and self.process_count > 1:
            with multiprocessing.Pool(processes=self.process_count) as pool:
                pool.starmap(
                    self.handle_bdd100k_sequence, self.multiprocess_task_params
                )
        else:
            for param in self.multiprocess_task_params:
                self.handle_bdd100k_sequence(*param)
        logger.info("Output BDD100K format finished!")

        logger.info("Generate SeqMap")
        train_seq_map_path = os.path.join(output_bdd100k_dir, "train_seqmap.txt")
        self.generate_seq_map(
            dir_path=os.path.join(output_bdd100k_dir, "train"),
            save_path=train_seq_map_path,
        )
        logger.info("Generate Train Done! " + train_seq_map_path)

        val_seq_map_path = os.path.join(output_bdd100k_dir, "val_seqmap.txt")
        self.generate_seq_map(
            dir_path=os.path.join(output_bdd100k_dir, "val"), save_path=val_seq_map_path
        )
        logger.info("Generate Val Done! " + val_seq_map_path)

        test_seq_map_path = os.path.join(output_bdd100k_dir, "test_seqmap.txt")
        self.generate_seq_map(
            dir_path=os.path.join(output_bdd100k_dir, "test"),
            save_path=test_seq_map_path,
        )
        logger.info("Generate Test Done! " + test_seq_map_path)
        logger.info("Generate SeqMap Done!")

        logger.info("Generate YOLO List")
        self.generate_yolo_list_txt(dir_path=output_bdd100k_dir, profile_name="train")
        logger.info("Generate YOLO Train Done!")

        self.generate_yolo_list_txt(dir_path=output_bdd100k_dir, profile_name="val")
        logger.info("Generate YOLO Val Done!")

        self.generate_yolo_list_txt(dir_path=output_bdd100k_dir, profile_name="test")
        logger.info("Generate YOLO Test Done!")

        logger.info("Output BDD100K Task Done!")
