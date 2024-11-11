import argparse
import os

from mot_toolkit.scripts.auto.sam.auto_sam_fix import sam_fix
from mot_toolkit.utils.cli.print_info import print_info
from mot_toolkit.utils.logs import get_logger

logger = get_logger()


def get_opts():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', type=str, default='.', help='Directory')
    parser.add_argument('--process', type=int, default=1, help='Work Process Count')

    parser.add_argument('--sam', action='store_true', help='Segment Anything Model')
    parser.add_argument('--sam_model', type=str, default='sam', help='Segment Anything Model')

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

    sam_fix(
        dataset_dir_path=dir_path,
        process_count=process_count
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
