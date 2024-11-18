import argparse
import os

from mot_toolkit.scripts.auto.sam.auto_sam_fix import (
    sam_fix, sam_fix_with_config_dir
)
from mot_toolkit.utils.cli.print_info import print_info
from mot_toolkit.utils.logs import get_logger

logger = get_logger()


def get_opts():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', type=str, default='.', help='Directory')
    parser.add_argument('--process', type=int, default=1, help='Work Process Count')
    parser.add_argument('--iou', type=float, default=0.9, help='IOU Threshold')

    parser.add_argument(
        '--task', type=str, default='',
        help='Task configure file or directory path'
    )

    parser.add_argument('--sam', action='store_true', help='Segment Anything Model')
    parser.add_argument(
        '--sam_model', type=str, default='',
        help='Segment Anything Model pt file name'
    )

    parser.add_argument('-y', action='store_true', help='Auto Confirm')

    return parser.parse_args()


def sam(opts):
    if not (opts.__contains__('dir') and opts.dir):
        logger.error('Please input dir')

    dir_path = opts.dir
    if not (os.path.exists(dir_path) and os.path.isdir(dir_path)):
        logger.error(f'Please input a valid dir: {dir_path}')
        return

    process_count = 1
    try:
        process_count = opts.process
    except Exception:
        pass

    iou = 0.9
    model_name = ""

    try:
        iou = opts.iou
    except Exception as e:
        logger.error(e)

    try:
        model_name = opts.sam_model
    except Exception as e:
        logger.error(e)

    task_config_path = ""
    try:
        task_config_path = opts.task
    except Exception as e:
        logger.error(e)

    if task_config_path and os.path.exists(task_config_path):
        logger.info(f"Task Config Path: {task_config_path}")

        json_path_list = []

        if os.path.isfile(task_config_path) and task_config_path.endswith('.json'):
            json_path_list.append(task_config_path)

        if os.path.isdir(task_config_path):
            for root, dirs, files in os.walk(task_config_path):
                for file in files:
                    if file.endswith('.json'):
                        json_path = os.path.join(root, file)
                        json_path_list.append(json_path)

        if len(json_path_list) == 0:
            logger.error(f"No valid json file found in {task_config_path}")
            return

        logger.info(f"Dir: {dir_path}")
        logger.info(f"Process: {process_count}")
        logger.info(f"IOU: {iou}")
        logger.info(f"Model: {model_name}")

        logger.info(f"Task Config List({len(json_path_list)}):")
        for json_path in json_path_list:
            logger.info(f"  {json_path}")

        if not opts.y:
            input("Press Enter to continue...")

        sam_fix_with_config_dir(
            dataset_dir_path=dir_path,
            process_count=process_count,
            iou_threshold=iou,
            config_path_list=json_path_list,
            model_name=model_name
        )

    else:
        logger.info(f"Dir: {dir_path}")
        logger.info(f"Process: {process_count}")
        logger.info(f"IOU: {iou}")
        logger.info(f"Model: {model_name}")

        if not opts.y:
            input("Press Enter to continue...")

        sam_fix(
            dataset_dir_path=dir_path,
            process_count=process_count,
            iou_threshold=iou,
            model_name=model_name
        )


def main():
    print_info()

    opts = get_opts()

    if opts.__contains__('sam') and opts.sam:
        print('Segment Anything Model')
        sam(opts)
        return


if __name__ == '__main__':
    main()
