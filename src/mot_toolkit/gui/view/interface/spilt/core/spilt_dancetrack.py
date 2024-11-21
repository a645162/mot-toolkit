import multiprocessing
import os
import shutil

from typing import List, Tuple

from mot_toolkit.config.hardware import io_cpu_count
from mot_toolkit.dataset.dataset_dir import get_dataset_dir_list
from mot_toolkit.datatype.dataset.dataset_spilt import DatasetSpilt
from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotationDirectory
from mot_toolkit.utils.logs import get_logger

logger = get_logger()


class SpiltDanceTrack:
    # DanceTrack is 8
    # MOT Challenge is 6
    file_name_length = 8
    file_name_start = 1

    process_count: int = 1
    multiprocess_mode: bool = True
    multiprocess_task_params: List[Tuple] = []

    def __init__(self):
        self.process_count = io_cpu_count

    def handle_dance_track_sequence(
            self,
            sequence_dir: str,
            target_dir: str
    ):
        if not os.path.exists(sequence_dir):
            os.makedirs(sequence_dir, exist_ok=True)

        annotation_directory = XAnyLabelingAnnotationDirectory()
        annotation_directory.dir_path = sequence_dir
        annotation_directory.walk_dir(recursive=False)
        annotation_directory.sort_path(group_directory=True)

        annotation_directory.load_json_files()

        for i, file_obj in enumerate(annotation_directory.annotation_file):
            current_index = i + self.file_name_start

            source_path_json = file_obj.file_path
            source_path_jpeg = source_path_json.replace(".json", ".jpg")

            target_path_json = os.path.join(
                target_dir, target_dir,
                format(current_index, f"0{self.file_name_length}") + ".json"
            )
            target_path_jpeg = target_path_json.replace(".json", ".jpg")

            shutil.copyfile(source_path_json, target_path_json)
            shutil.copyfile(source_path_jpeg, target_path_jpeg)

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
        print(str(dataset_dir_obj))
        source_dir = dataset_dir_obj.abs_path
        target_dir = os.path.join(output_dir, dataset_dir_obj.generate_new_name())

        if not os.path.exists(source_dir):
            logger.error("Source Dir Not Found: " + source_dir)
            return
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        # logger.debug("Source Dir: " + source_dir)
        # logger.debug("Target Dir: " + target_dir)

        sequence_path_list = get_dataset_dir_list(
            dataset_dir_path=source_dir,
            depth=1
        )
        for sequence_path in sequence_path_list:
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
        logger.info("Output DanceTrack Task Done!")
