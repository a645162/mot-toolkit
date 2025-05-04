import multiprocessing
import os
import profile
import shutil
from enum import Enum
from sys import prefix

from typing import List, Tuple

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


class SpiltYolo:
    # DanceTrack is 8
    # MOT Challenge is 6
    file_name_length = 8
    file_name_start = 1

    process_count: int = 1
    multiprocess_mode: bool = True
    multiprocess_task_params: List[Tuple] = []

    def __init__(self):
        self.process_count = io_cpu_count

    def handle_yolo_sequence(
        self,
        sequence_dir: str,
        target_dir: str,
        profile_name: str = "train",
    ):
        if not os.path.exists(sequence_dir):
            logger.error("Source Sequence Dir Not Found: " + sequence_dir)
            return

        yolo_img = os.path.join(target_dir, "images", profile_name)
        yolo_label = os.path.join(target_dir, "labels", profile_name)

        os.makedirs(yolo_img, exist_ok=True)
        os.makedirs(yolo_label, exist_ok=True)

        annotation_directory = XAnyLabelingAnnotationDirectory()
        annotation_directory.dir_path = sequence_dir
        annotation_directory.walk_dir(recursive=False)
        annotation_directory.sort_path(group_directory=True)

        annotation_directory.load_json_files()

        level = 2

        prefix_name = os.path.basename(sequence_dir)
        current_dir = os.path.dirname(sequence_dir)
        level -= 1
        while level > 0:
            prefix_name = os.path.basename(current_dir) + "_" + prefix_name
            current_dir = os.path.dirname(current_dir)
            level -= 1

        for i, file_obj in enumerate(annotation_directory.annotation_file_list):
            current_index = i + self.file_name_start

            source_path_jpeg = file_obj.file_path.replace(".json", ".jpg")
            file_name = format(current_index, f"0{self.file_name_length}") + ".jpg"
            if prefix_name:
                file_name = prefix_name + "_" + file_name
            target_path_jpeg = os.path.join(yolo_img, file_name)

            if os.path.exists(target_path_jpeg):
                # Remove if already exists
                os.remove(target_path_jpeg)

            shutil.copyfile(source_path_jpeg, target_path_jpeg)

            yolo_text_list = []
            for rect_obj in file_obj.rect_annotation_list:
                x_ratio = rect_obj.center_x_ratio
                y_ratio = rect_obj.center_y_ratio
                w_ratio = rect_obj.width_ratio
                h_ratio = rect_obj.height_ratio

                round_count = 6
                x_ratio = round(x_ratio, round_count)
                y_ratio = round(y_ratio, round_count)
                w_ratio = round(w_ratio, round_count)
                h_ratio = round(h_ratio, round_count)

                line = (
                    f"{rect_obj.group_id} "
                    f"{x_ratio} "
                    f"{y_ratio} "
                    f"{w_ratio} "
                    f"{h_ratio}"
                )
                yolo_text_list.append(line)

            yolo_text = "\n".join(yolo_text_list)
            # 修改此处，使用相同的文件名但保存到labels目录
            label_file_name = file_name.replace(".jpg", ".txt")
            target_path_txt = os.path.join(yolo_label, label_file_name)
            with open(target_path_txt, "w") as f:
                f.write(yolo_text)

    def handle_yolo_sequence_param(
        self, sequence_dir: str, target_dir: str, profile_name: str = "train"
    ):
        return (sequence_dir, target_dir, profile_name)

    def handle_yolo_dir(
        self,
        dataset_dir_obj: DatasetSpilt,
        output_dir: str,
        profile_name: str = "train",
    ):
        # print(str(dataset_dir_obj))
        source_dir = dataset_dir_obj.abs_path

        if not os.path.exists(source_dir):
            logger.error("Source Dir Not Found: " + source_dir)
            return

        # logger.debug("Source Dir: " + source_dir)
        # logger.debug("Target Dir: " + target_dir)

        sequence_path_list = get_dataset_dir_list(dataset_dir_path=source_dir, depth=1)
        for sequence_path in sequence_path_list:
            # self.handle_dance_track_sequence(
            #     sequence_dir=sequence_path,
            #     target_dir=output_dir,
            #     profile_name=profile_name
            # )
            self.multiprocess_task_params.append(
                self.handle_yolo_sequence_param(
                    sequence_dir=sequence_path,
                    target_dir=output_dir,
                    profile_name=profile_name,
                )
            )

    def output_yolo_spilt(
        self,
        dataset_list: List[DatasetSpilt],
        output_dir: str,
        profile_name: str = "train",
    ):
        logger.info("Output DanceTrack")
        logger.info("Dataset List Count: " + str(len(dataset_list)))
        logger.info("Output Dir: " + output_dir)

        for dataset_obj in dataset_list:
            self.handle_yolo_dir(
                dataset_dir_obj=dataset_obj,
                output_dir=output_dir,
                profile_name=profile_name,
            )

    def output_yolo(
        self,
        output_yolo_dir: str,
        dataset_train_list: List[DatasetSpilt],
        dataset_val_list: List[DatasetSpilt],
        dataset_test_list: List[DatasetSpilt],
    ):
        ## Train
        self.output_yolo_spilt(
            dataset_list=dataset_train_list,
            output_dir=output_yolo_dir,
            profile_name="train",
        )

        ## Val
        self.output_yolo_spilt(
            dataset_list=dataset_val_list,
            output_dir=output_yolo_dir,
            profile_name="val",
        )

        ## Test
        self.output_yolo_spilt(
            dataset_list=dataset_test_list,
            output_dir=output_yolo_dir,
            profile_name="test",
        )

        task_count = len(self.multiprocess_task_params)

        logger.info("Output DanceTrack Task Generate Done!")
        logger.info("Output DanceTrack Task Count: " + str(task_count))

        logger.info("Start task on " + str(self.process_count) + " CPU Cores")
        if self.multiprocess_mode and self.process_count > 1:
            with multiprocessing.Pool(processes=self.process_count) as pool:
                pool.starmap(self.handle_yolo_sequence, self.multiprocess_task_params)
        else:
            for param in self.multiprocess_task_params:
                self.handle_yolo_sequence(*param)
        logger.info("Output YOLO format finished!")

        logger.info("Output YOLO Task Done!")
