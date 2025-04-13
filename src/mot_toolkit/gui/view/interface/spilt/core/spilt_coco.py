import multiprocessing
import os
import shutil
import json
from enum import Enum
import numpy as np
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


class SpiltCoco:
    # COCO格式转换类
    file_name_length = 8
    file_name_start = 1

    process_count: int = 1
    multiprocess_mode: bool = True
    multiprocess_task_params: List[Tuple] = []

    def __init__(self):
        self.process_count = io_cpu_count
        # COCO数据结构初始化
        self.reset_coco_data()

    def reset_coco_data(self):
        self.images = []
        self.annotations = []
        self.categories = []
        self.img_id = 0
        self.ann_id = 0
        # 设置类别，这里只有person类，可根据需要修改
        self._init_categories({"person": 1})

    def _init_categories(self, classname_to_id: Dict[str, int]):
        """初始化COCO的类别"""
        self.categories = []
        for k, v in classname_to_id.items():
            category = {}
            category["id"] = v
            category["name"] = k
            self.categories.append(category)

    def save_coco_json(self, instance: Dict[str, Any], save_path: str):
        """保存COCO格式的JSON文件"""
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        json.dump(
            instance,
            open(save_path, "w", encoding="utf-8"),
            ensure_ascii=False,
            indent=1,
        )

    def handle_coco_sequence(
        self,
        sequence_dir: str,
        target_dir: str,
        profile_name: str = "train",
    ):
        """处理单个序列转换为COCO格式"""
        if not os.path.exists(sequence_dir):
            logger.error("Source Sequence Dir Not Found: " + sequence_dir)
            return

        # 创建COCO目录结构
        coco_imgs = os.path.join(target_dir, "images", f"{profile_name}2017")
        coco_anno_dir = os.path.join(target_dir, "annotations")

        os.makedirs(coco_imgs, exist_ok=True)
        os.makedirs(coco_anno_dir, exist_ok=True)

        # 加载注释文件
        annotation_directory = XAnyLabelingAnnotationDirectory()
        annotation_directory.dir_path = sequence_dir
        annotation_directory.walk_dir(recursive=False)
        annotation_directory.sort_path(group_directory=True)
        annotation_directory.load_json_files()

        # 生成序列前缀名称
        prefix_name = os.path.basename(sequence_dir)
        current_dir = os.path.dirname(sequence_dir)
        level = 2
        level -= 1
        while level > 0:
            prefix_name = os.path.basename(current_dir) + "_" + prefix_name
            current_dir = os.path.dirname(current_dir)
            level -= 1

        # 临时存储此序列的COCO数据
        images = []
        annotations = []
        img_id_start = self.img_id
        ann_id_start = self.ann_id

        for i, file_obj in enumerate(annotation_directory.annotation_file_list):
            current_index = i + self.file_name_start

            # 处理图像文件
            source_path_jpeg = file_obj.file_path.replace(".json", ".jpg")
            file_name = format(current_index, f"0{self.file_name_length}") + ".jpg"
            if prefix_name:
                file_name = prefix_name + "_" + file_name
            target_path_jpeg = os.path.join(coco_imgs, file_name)

            if os.path.exists(target_path_jpeg):
                # 删除已存在的文件
                os.remove(target_path_jpeg)

            # 复制图像到目标目录
            shutil.copyfile(source_path_jpeg, target_path_jpeg)

            # 创建COCO图像条目
            img_width = file_obj.image_width
            img_height = file_obj.image_height
            image_item = {
                "id": self.img_id,
                "width": img_width,
                "height": img_height,
                "file_name": file_name,
            }
            images.append(image_item)

            # 为每个矩形框创建COCO标注
            for rect_obj in file_obj.rect_annotation_list:
                # 计算COCO格式的bbox [x, y, width, height]
                x_center_ratio = rect_obj.center_x_ratio
                y_center_ratio = rect_obj.center_y_ratio
                width_ratio = rect_obj.width_ratio
                height_ratio = rect_obj.height_ratio

                # 转换为像素坐标
                x_center = x_center_ratio * img_width
                y_center = y_center_ratio * img_height
                width = width_ratio * img_width
                height = height_ratio * img_height

                # COCO格式需要左上角坐标
                x = x_center - (width / 2)
                y = y_center - (height / 2)

                # 创建分割点（简单矩形的四个角点）
                x1, y1 = x, y
                x2, y2 = x + width, y
                x3, y3 = x + width, y + height
                x4, y4 = x, y + height
                segmentation = [[x1, y1, x2, y2, x3, y3, x4, y4]]

                annotation_item = {
                    "id": self.ann_id,
                    "image_id": self.img_id,
                    "category_id": 1,  # 假设所有目标都是人
                    "segmentation": segmentation,
                    "bbox": [x, y, width, height],
                    "area": width * height,
                    "iscrowd": 0,
                }
                annotations.append(annotation_item)
                self.ann_id += 1

            self.img_id += 1

        return images, annotations, img_id_start, ann_id_start

    def handle_coco_sequence_param(
        self, sequence_dir: str, target_dir: str, profile_name: str = "train"
    ):
        return (sequence_dir, target_dir, profile_name)

    def handle_coco_dir(
        self,
        dataset_dir_obj: DatasetSpilt,
        output_dir: str,
        profile_name: str = "train",
    ):
        source_dir = dataset_dir_obj.abs_path

        if not os.path.exists(source_dir):
            logger.error("Source Dir Not Found: " + source_dir)
            return

        sequence_path_list = get_dataset_dir_list(dataset_dir_path=source_dir, depth=1)
        for sequence_path in sequence_path_list:
            self.multiprocess_task_params.append(
                self.handle_coco_sequence_param(
                    sequence_dir=sequence_path,
                    target_dir=output_dir,
                    profile_name=profile_name,
                )
            )

    def output_coco_spilt(
        self,
        dataset_list: List[DatasetSpilt],
        output_dir: str,
        profile_name: str = "train",
    ):
        logger.info(f"Output COCO {profile_name}")
        logger.info("Dataset List Count: " + str(len(dataset_list)))
        logger.info("Output Dir: " + output_dir)

        for dataset_obj in dataset_list:
            self.handle_coco_dir(
                dataset_dir_obj=dataset_obj,
                output_dir=output_dir,
                profile_name=profile_name,
            )

    def output_coco(
        self,
        output_coco_dir: str,
        dataset_train_list: List[DatasetSpilt],
        dataset_val_list: List[DatasetSpilt],
        dataset_test_list: List[DatasetSpilt],
    ):
        # 重置COCO数据
        self.reset_coco_data()

        # 生成训练集任务
        self.output_coco_spilt(
            dataset_list=dataset_train_list,
            output_dir=output_coco_dir,
            profile_name="train",
        )

        # 生成验证集任务
        self.output_coco_spilt(
            dataset_list=dataset_val_list,
            output_dir=output_coco_dir,
            profile_name="val",
        )

        # 生成测试集任务
        self.output_coco_spilt(
            dataset_list=dataset_test_list,
            output_dir=output_coco_dir,
            profile_name="test",
        )

        task_count = len(self.multiprocess_task_params)

        logger.info("Output COCO Task Generate Done!")
        logger.info("Output COCO Task Count: " + str(task_count))

        logger.info("Start task on " + str(self.process_count) + " CPU Cores")

        # 存储每个分割的数据
        train_images = []
        train_annotations = []
        val_images = []
        val_annotations = []
        test_images = []
        test_annotations = []

        # 多进程执行任务
        results = []
        if self.multiprocess_mode and self.process_count > 1:
            with multiprocessing.Pool(processes=self.process_count) as pool:
                results = pool.starmap(
                    self.handle_coco_sequence, self.multiprocess_task_params
                )
        else:
            for param in self.multiprocess_task_params:
                results.append(self.handle_coco_sequence(*param))

        # 处理结果，分类到不同集合
        for i, param in enumerate(self.multiprocess_task_params):
            profile_name = param[2]
            images, annotations, _, _ = results[i]

            if profile_name == "train":
                train_images.extend(images)
                train_annotations.extend(annotations)
            elif profile_name == "val":
                val_images.extend(images)
                val_annotations.extend(annotations)
            elif profile_name == "test":
                test_images.extend(images)
                test_annotations.extend(annotations)

        # 创建并保存COCO格式的JSON文件
        if train_images:
            train_instance = {
                "info": "MOT Toolkit created",
                "license": ["license"],
                "images": train_images,
                "annotations": train_annotations,
                "categories": self.categories,
            }
            self.save_coco_json(
                train_instance,
                os.path.join(
                    output_coco_dir, "annotations", "instances_train2017.json"
                ),
            )

        if val_images:
            val_instance = {
                "info": "MOT Toolkit created",
                "license": ["license"],
                "images": val_images,
                "annotations": val_annotations,
                "categories": self.categories,
            }
            self.save_coco_json(
                val_instance,
                os.path.join(output_coco_dir, "annotations", "instances_val2017.json"),
            )

        if test_images:
            test_instance = {
                "info": "MOT Toolkit created",
                "license": ["license"],
                "images": test_images,
                "annotations": test_annotations,
                "categories": self.categories,
            }
            self.save_coco_json(
                test_instance,
                os.path.join(output_coco_dir, "annotations", "instances_test2017.json"),
            )

        logger.info("Output COCO format finished!")
        logger.info("Output COCO Task Done!")
