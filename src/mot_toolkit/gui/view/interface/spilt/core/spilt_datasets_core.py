import os
import json
from typing import List

from mot_toolkit.datatype.dataset.dataset_spilt import (
    DatasetSpilt, SpiltType
)
from mot_toolkit.gui.view.interface.spilt.core.spilt_dancetrack import SpiltDanceTrack
from mot_toolkit.gui.view.interface.spilt.core.spilt_yolo import SpiltYolo
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


def spilt_dataset(
        dataset_base_dir: str,
        output_base_dir: str,
        spilt_config: str = "default.spilt.json"
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
    # file_name_depth = config_dict["file_name_depth"]

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
    spilt_dance_track = SpiltDanceTrack()
    spilt_dance_track.output_dance_track(
        output_dance_track_dir=output_dance_track_dir,
        dataset_train_list=dataset_train_list,
        dataset_val_list=dataset_val_list,
        dataset_test_list=dataset_test_list,
    )

    # YOLO
    # spilt_yolo = SpiltYolo()
    # spilt_yolo.output_yolo(
    #     output_yolo_dir=output_yolo_dir,
    #     dataset_train_list=dataset_train_list,
    #     dataset_val_list=dataset_val_list,
    #     dataset_test_list=dataset_test_list,
    # )


if __name__ == '__main__':
    # dataset_base_dir = r"/mnt/h/Datasets/TrackShipOnlineVideo/LabelMe"
    # output_base_dir = r"/mnt/h/Datasets/TrackShipOnlineVideo/ShipTrackSpilt"
    dataset_base_dir = r"H:\Datasets\MaritimeTrackAllData\LabelMe"
    output_base_dir = r"H:\Datasets\MaritimeTrackAllData\Spilt\MaritimeTrack_Full"

    # config = "test.spilt.json"
    config = "20241208.spilt.json"

    spilt_dataset(
        dataset_base_dir=dataset_base_dir,
        output_base_dir=output_base_dir,
        spilt_config=config
    )
