import os
import json
from typing import List

from mot_toolkit.config.hardware import io_cpu_count
from mot_toolkit.datatype.dataset.dataset_spilt import (
    DatasetSpilt, SpiltType
)
from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotationDirectory
from mot_toolkit.utils.logs import get_logger

logger = get_logger()

json_dict_example: dict = {
    "all": {
        "dataset_list": [],
        "path_str_list": []
    },
    "train": {
        "dataset_list": [],
        "path_str_list": []
    },
    "val": {
        "dataset_list": [],
        "path_str_list": []
    },
    "test": {
        "dataset_list": [],
        "path_str_list": []
    },
}

# DanceTrack is 8
# MOT Challenge is 6
file_name_length = 8


def handle_dance_track_dir(
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

    annotation_directory = XAnyLabelingAnnotationDirectory()
    annotation_directory.dir_path = source_dir
    annotation_directory.walk_dir(recursive=False)
    annotation_directory.sort_path(group_directory=True)

    annotation_directory.load_json_files()

    for file_obj in annotation_directory.annotation_file:
        print(file_obj.file_name_no_extension)


def output_dance_track(
        dataset_list: List[DatasetSpilt],
        output_dir: str
):
    logger.info("Output DanceTrack")
    logger.info("Dataset List Count: " + str(len(dataset_list)))
    logger.info("Output Dir: " + output_dir)

    process_count = io_cpu_count

    for dataset_obj in dataset_list:
        handle_dance_track_dir(
            dataset_dir_obj=dataset_obj,
            output_dir=output_dir
        )


def spilt_dataset(
        dataset_base_dir: str,
        output_base_dir: str,
        spilt_config: str = "spilt_settings.json"
):
    if not (os.path.exists(dataset_base_dir) and os.path.isdir(dataset_base_dir)):
        logger.error("Dataset base dir not found: " + dataset_base_dir)
        return

    spilt_config_path = os.path.join(dataset_base_dir, spilt_config)
    if not os.path.exists(spilt_config_path):
        logger.error("Spilt config file not found: " + spilt_config_path)
        return

    with open(spilt_config_path, "r", encoding="utf-8") as f:
        config_dict = json.load(f)

    # Check Dict key is contain train, val, test
    for key in ["train", "val", "test"]:
        if key not in config_dict:
            logger.error("Key not found: " + key)
            return

        spilt_dict: dict = config_dict[key]

        if "path_str_list" not in spilt_dict.keys():
            logger.error(f'Key not found: config_dict[{key}]["path_str_list"]')
            return

        if not isinstance(spilt_dict["path_str_list"], list):
            logger.error(f'TypeError: config_dict[{key}]["path_str_list"]')
            return

    dataset_train_str_list = config_dict["train"]["path_str_list"]
    dataset_val_str_list = config_dict["val"]["path_str_list"]
    dataset_test_str_list = config_dict["test"]["path_str_list"]

    dataset_train_list: List[DatasetSpilt] = []
    dataset_val_list: List[DatasetSpilt] = []
    dataset_test_list: List[DatasetSpilt] = []

    depth = config_dict["depth"]

    for path_str in dataset_train_str_list:
        obj = DatasetSpilt(
            path=path_str,
            base_dir_path=dataset_base_dir,
            spilt_type=SpiltType.TRAIN,
            depth=depth
        )
        dataset_train_list.append(obj)
    for path_str in dataset_val_str_list:
        obj = DatasetSpilt(
            path=path_str,
            base_dir_path=dataset_base_dir,
            spilt_type=SpiltType.VAL,
            depth=depth
        )
        dataset_val_list.append(obj)
    for path_str in dataset_test_str_list:
        obj = DatasetSpilt(
            path=path_str,
            base_dir_path=dataset_base_dir,
            spilt_type=SpiltType.TEST,
            depth=depth
        )
        dataset_test_list.append(obj)

    output_dance_track_dir = os.path.join(output_base_dir, "DanceTrack")
    output_yolo_dir = os.path.join(output_base_dir, "YOLO")

    os.makedirs(output_dance_track_dir, exist_ok=True)
    os.makedirs(output_yolo_dir, exist_ok=True)

    # DanceTrack

    ## Train
    dance_track_train_dir = os.path.join(output_dance_track_dir, "train")
    os.makedirs(dance_track_train_dir, exist_ok=True)
    output_dance_track(
        dataset_list=dataset_train_list,
        output_dir=dance_track_train_dir
    )

    ## Val
    dance_track_val_dir = os.path.join(output_dance_track_dir, "val")
    os.makedirs(dance_track_val_dir, exist_ok=True)
    output_dance_track(
        dataset_list=dataset_val_list,
        output_dir=dance_track_val_dir
    )

    ## Test
    dance_track_test_dir = os.path.join(output_dance_track_dir, "test")
    os.makedirs(dance_track_test_dir, exist_ok=True)
    output_dance_track(
        dataset_list=dataset_test_list,
        output_dir=dance_track_test_dir
    )

    # YOLO


if __name__ == '__main__':
    dataset_base_dir = r"/mnt/h/Datasets/TrackShipOnlineVideo/LabelMe"
    output_base_dir = r"/mnt/h/Datasets/TrackShipOnlineVideo/Spilt"

    spilt_dataset(
        dataset_base_dir=dataset_base_dir,
        output_base_dir=output_base_dir
    )
