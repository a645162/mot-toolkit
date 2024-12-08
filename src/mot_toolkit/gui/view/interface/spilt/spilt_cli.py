import os
import argparse

from mot_toolkit.gui.view.interface.spilt \
    .core.spilt_datasets_core import spilt_dataset
from mot_toolkit.utils.logs import get_logger

logger = get_logger()


def get_opts():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dir", "-d", type=str, default="",
        help="Path to dataset directory"
    )
    parser.add_argument(
        "--output", "-o", type=str, default="",
        help="Path to output directory"
    )
    parser.add_argument(
        "--config", "--cfg", "-c", type=str, default="",
        help="Path to output directory"
    )

    return parser.parse_args()


def main():
    opts = get_opts()

    dataset_base_dir = str(opts.dir).strip()
    output_base_dir = str(opts.output).strip()
    config = str(opts.config).strip()

    if not os.path.exists(dataset_base_dir):
        logger.error("Directory does not exist!!!")
        return
    if not os.path.exists(config):
        logger.error("Config file does not exist!!!")
        return

    config_name = os.path.basename(config)
    if not config_name.endswith(".spilt.json"):
        logger.error("Invalid config file!!!")
        return

    config_name = config_name.replace(".spilt.json", "").strip()

    if output_base_dir == "":
        output_base_dir = dataset_base_dir
        while output_base_dir.endswith("/"):
            output_base_dir = output_base_dir[:-1]
        output_base_dir += "_" + config_name

    spilt_dataset(
        dataset_base_dir=dataset_base_dir,
        output_base_dir=output_base_dir,
        spilt_config=config
    )


if __name__ == "__main__":
    main()
