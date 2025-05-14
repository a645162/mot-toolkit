import os
import json
from typing import List

from mot_toolkit.datatype.dataset.dataset_spilt import DatasetSpilt, SpiltType
from mot_toolkit.gui.view.interface.spilt.core.spilt_dancetrack import SpiltDanceTrack
from mot_toolkit.gui.view.interface.spilt.core.spilt_yolo import SpiltYolo
from mot_toolkit.gui.view.interface.spilt.core.spilt_coco import SpiltCoco
from mot_toolkit.utils.logs import get_logger

logger = get_logger()

json_dict_example: dict = {
    "all": {"dataset_list": [], "path_str_list": []},
    "train": {"dataset_list": [], "path_str_list": []},
    "val": {"dataset_list": [], "path_str_list": []},
    "test": {"dataset_list": [], "path_str_list": []},
}


def spilt_dataset(
    dataset_base_dir: str,
    output_base_dir: str,
    spilt_config: str = "default.spilt.json",
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
            depth=depth,
        )
        dataset_train_list.append(obj)
    for path_str in dataset_val_str_list:
        obj = DatasetSpilt(
            path=path_str,
            base_dir_path=dataset_base_dir,
            spilt_type=SpiltType.VAL,
            depth=depth,
        )
        dataset_val_list.append(obj)
    for path_str in dataset_test_str_list:
        obj = DatasetSpilt(
            path=path_str,
            base_dir_path=dataset_base_dir,
            spilt_type=SpiltType.TEST,
            depth=depth,
        )
        dataset_test_list.append(obj)

    output_dance_track_dir = os.path.join(output_base_dir, "DanceTrack")
    output_yolo_dir = os.path.join(output_base_dir, "YOLO")
    output_coco_dir = os.path.join(output_base_dir, "COCO")  # 新增COCO输出目录

    os.makedirs(output_dance_track_dir, exist_ok=True)
    os.makedirs(output_yolo_dir, exist_ok=True)
    os.makedirs(output_coco_dir, exist_ok=True)  # 创建COCO输出目录

    # # DanceTrack
    spilt_dance_track = SpiltDanceTrack()
    spilt_dance_track.output_dance_track(
        output_dance_track_dir=output_dance_track_dir,
        dataset_train_list=dataset_train_list,
        dataset_val_list=dataset_val_list,
        dataset_test_list=dataset_test_list,
    )

    # # YOLO
    # spilt_yolo = SpiltYolo()
    # spilt_yolo.output_yolo(
    #     output_yolo_dir=output_yolo_dir,
    #     dataset_train_list=dataset_train_list,
    #     dataset_val_list=dataset_val_list,
    #     dataset_test_list=dataset_test_list,
    # )

    # # COCO
    # spilt_coco = SpiltCoco()
    # spilt_coco.output_coco(
    #     output_coco_dir=output_coco_dir,
    #     dataset_train_list=dataset_train_list,
    #     dataset_val_list=dataset_val_list,
    #     dataset_test_list=dataset_test_list,
    # )


def spilt_datasets_list(dataset_configs: List[dict]):
    """
    对多个数据集进行划分
    
    Args:
        dataset_configs: 列表，每个元素是一个字典，包含以下键：
            - dataset_base_dir: 数据集基础目录
            - output_base_dir: 输出基础目录
            - spilt_config: 划分配置文件名，默认为"default.spilt.json"
    """
    for config in dataset_configs:
        if not config.get("enable", True):
            continue
        
        dataset_base_dir = config.get("dataset_base_dir")
        output_base_dir = config.get("output_base_dir")
        spilt_config = config.get("spilt_config", "default.spilt.json")
        
        logger.info(f"Processing dataset: {dataset_base_dir}")
        spilt_dataset(
            dataset_base_dir=dataset_base_dir,
            output_base_dir=output_base_dir,
            spilt_config=spilt_config
        )


if __name__ == "__main__":
    # spilt_dataset(
    #     dataset_base_dir=dataset_base_dir,
    #     output_base_dir=output_base_dir,
    #     spilt_config=config,
    # )

    # 使用列表方式调用多个数据集划分
    datasets_config = [
        {
            "enable": True,
            "dataset_base_dir": r"/home/konghaomin/Datasets/SMD_LabelMe_Fix_20250509",
            "output_base_dir": r"/home/konghaomin/Datasets/SMD_Fix_20250509",
            "spilt_config": "20250509.spilt.json",
        },
        {
            "enable": False,
            "dataset_base_dir": r"/home/konghaomin/datasets/SMD_LabelMe",
            "output_base_dir": r"/home/konghaomin/Datasets/SMD_New_20250509",
            "spilt_config": "20250509.spilt.json",
        },
        {
            "enable": False,
            "dataset_base_dir": r"/home/konghaomin/Datasets/MaritimeTrackAllData/MT20250319/LabelMe",
            "output_base_dir": r"/home/konghaomin/Datasets/MaritimeTrack_Full_20250322",
            "spilt_config": "20250322.spilt.json",
        },
        # 可以添加更多数据集配置
    ]

    # 注释掉以下行以避免在导入时执行
    spilt_datasets_list(datasets_config)
