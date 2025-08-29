import multiprocessing
import os
import shutil
from enum import Enum

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


class SpiltDanceTrack:
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

    def handle_dance_track_sequence(
            self,
            sequence_dir: str,
            target_dir: str
    ):
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

        annotation_directory = XAnyLabelingAnnotationDirectory()
        annotation_directory.dir_path = sequence_dir
        annotation_directory.walk_dir(recursive=False)
        annotation_directory.sort_path(group_directory=True)

        annotation_directory.load_json_files()

        path_img1 = os.path.join(target_dir, "img1")
        path_gt = os.path.join(target_dir, "gt")
        if not os.path.exists(path_img1):
            os.makedirs(path_img1, exist_ok=True)
        if not os.path.exists(path_gt):
            os.makedirs(path_gt, exist_ok=True)
        path_gt_txt = os.path.join(path_gt, "gt.txt")
        path_seq_info_ini = os.path.join(target_dir, "seqinfo.ini")

        for i, file_obj in enumerate(annotation_directory.annotation_file_list):
            current_index = i + self.file_name_start

            source_path_jpeg = file_obj.file_path.replace(".json", ".jpg")
            target_path_jpeg = os.path.join(
                path_img1,
                format(current_index, f"0{self.file_name_length}") + ".jpg"
            )

            if os.path.exists(target_path_jpeg):
                # Remove if already exists
                os.remove(target_path_jpeg)

            shutil.copyfile(source_path_jpeg, target_path_jpeg)

            yolo_text_list = []
            for rect_obj in file_obj.rect_annotation_list:
                group_id = str(rect_obj.group_id).strip()

                if group_id == "":
                    logger.error(f"Object({rect_obj.label}) Group ID is Empty! {file_obj.file_path}")
                    continue

                x_ratio = rect_obj.center_x_ratio
                y_ratio = rect_obj.center_y_ratio
                w_ratio = rect_obj.width_ratio
                h_ratio = rect_obj.height_ratio

                round_count = 6
                x_ratio = round(x_ratio, round_count)
                y_ratio = round(y_ratio, round_count)
                w_ratio = round(w_ratio, round_count)
                h_ratio = round(h_ratio, round_count)

                line = (f"{group_id} "
                        f"{x_ratio} "
                        f"{y_ratio} "
                        f"{w_ratio} "
                        f"{h_ratio}")
                yolo_text_list.append(line)

            yolo_text = "\n".join(yolo_text_list)
            target_path_txt = target_path_jpeg.replace(".jpg", ".txt")
            with open(target_path_txt, "w") as f:
                f.write(yolo_text)

        # gt.txt
        with open(path_gt_txt, "w") as f:
            f.write(annotation_directory.to_mot_gt_txt(
                start_index=self.file_name_start
            ))

        # seqinfo.ini
        with open(path_seq_info_ini, "w") as f:
            f.write(annotation_directory.to_mot_seq_info_ini())

    def handle_dance_track_sequence_param(
            self,
            sequence_dir: str,
            target_dir: str
    ):
        return (
            sequence_dir,
            target_dir
        )

    def handle_dance_track_dir(
            self,
            dataset_dir_obj: DatasetSpilt,
            output_dir: str
    ):
        # print(str(dataset_dir_obj))
        source_dir = dataset_dir_obj.abs_path

        if not os.path.exists(source_dir):
            logger.error("Source Dir Not Found: " + source_dir)
            return

        # logger.debug("Source Dir: " + source_dir)
        # logger.debug("Target Dir: " + target_dir)

        sequence_path_list = get_dataset_dir_list(
            dataset_dir_path=source_dir,
            depth=1
        )
        for sequence_path in sequence_path_list:
            target_dir = os.path.join(
                output_dir,
                dataset_dir_obj.generate_new_name(sequence_path)
            )
            # self.handle_dance_track_sequence(
            #     sequence_dir=sequence_path,
            #     target_dir=target_dir
            # )
            self.multiprocess_task_params.append(
                self.handle_dance_track_sequence_param(
                    sequence_dir=sequence_path,
                    target_dir=target_dir
                )
            )

    def output_dance_track_spilt(
            self,
            dataset_list: List[DatasetSpilt],
            output_dir: str
    ):
        logger.info("Output DanceTrack")
        logger.info("Dataset List Count: " + str(len(dataset_list)))
        logger.info("Output Dir: " + output_dir)

        for dataset_obj in dataset_list:
            self.handle_dance_track_dir(
                dataset_dir_obj=dataset_obj,
                output_dir=output_dir
            )

    @staticmethod
    def generate_seq_map(
            dir_path: str,
            save_path: str
    ):
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
    def generate_yolo_list_txt(
            dir_path: str,
            profile_name: str = "train"
    ):
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
        with open(os.path.join(dir_path, f"yolo_{profile_name}.txt"), "w", encoding="utf-8") as f:
            f.write(text)

    def output_dance_track(
            self,
            output_dance_track_dir: str,
            dataset_train_list: List[DatasetSpilt],
            dataset_val_list: List[DatasetSpilt],
            dataset_test_list: List[DatasetSpilt],
    ):
        ## Train
        dance_track_train_dir = os.path.join(output_dance_track_dir, "train")
        os.makedirs(dance_track_train_dir, exist_ok=True)
        self.output_dance_track_spilt(
            dataset_list=dataset_train_list,
            output_dir=dance_track_train_dir
        )

        ## Val
        dance_track_val_dir = os.path.join(output_dance_track_dir, "val")
        os.makedirs(dance_track_val_dir, exist_ok=True)
        self.output_dance_track_spilt(
            dataset_list=dataset_val_list,
            output_dir=dance_track_val_dir
        )

        ## Test
        dance_track_test_dir = os.path.join(output_dance_track_dir, "test")
        os.makedirs(dance_track_test_dir, exist_ok=True)
        self.output_dance_track_spilt(
            dataset_list=dataset_test_list,
            output_dir=dance_track_test_dir
        )

        task_count = len(self.multiprocess_task_params)

        logger.info("Output DanceTrack Task Generate Done!")
        logger.info("Output DanceTrack Task Count: " + str(task_count))

        logger.info("Start task on " + str(self.process_count) + " CPU Cores")
        if self.multiprocess_mode and self.process_count > 1:
            with multiprocessing.Pool(processes=self.process_count) as pool:
                pool.starmap(
                    self.handle_dance_track_sequence,
                    self.multiprocess_task_params
                )
        else:
            for param in self.multiprocess_task_params:
                self.handle_dance_track_sequence(*param)
        logger.info("Output DanceTrack format finished!")

        logger.info("Generate SeqMap")
        train_seq_map_path = os.path.join(output_dance_track_dir, "train_seqmap.txt")
        self.generate_seq_map(
            dir_path=os.path.join(output_dance_track_dir, "train"),
            save_path=train_seq_map_path
        )
        logger.info("Generate Train Done! " + train_seq_map_path)

        val_seq_map_path = os.path.join(output_dance_track_dir, "val_seqmap.txt")
        self.generate_seq_map(
            dir_path=os.path.join(output_dance_track_dir, "val"),
            save_path=val_seq_map_path
        )
        logger.info("Generate Val Done! " + val_seq_map_path)

        test_seq_map_path = os.path.join(output_dance_track_dir, "test_seqmap.txt")
        self.generate_seq_map(
            dir_path=os.path.join(output_dance_track_dir, "test"),
            save_path=test_seq_map_path
        )
        logger.info("Generate Test Done! " + test_seq_map_path)
        logger.info("Generate SeqMap Done!")

        logger.info("Generate YOLO List")
        self.generate_yolo_list_txt(
            dir_path=output_dance_track_dir,
            profile_name="train"
        )
        logger.info("Generate YOLO Train Done!")

        self.generate_yolo_list_txt(
            dir_path=output_dance_track_dir,
            profile_name="val"
        )
        logger.info("Generate YOLO Val Done!")

        self.generate_yolo_list_txt(
            dir_path=output_dance_track_dir,
            profile_name="test"
        )
        logger.info("Generate YOLO Test Done!")

        logger.info("Output DanceTrack Task Done!")
