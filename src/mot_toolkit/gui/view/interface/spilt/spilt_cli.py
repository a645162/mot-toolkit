import os
import argparse

from mot_toolkit.utils.logs import get_logger

logger = get_logger()


def get_opts():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dir", "-d", type=str, default="",
        help="Path to dataset directory"
    )

    return parser.parse_args()


def main():
    opts = get_opts()

    if not os.path.exists(opts.dir):
        logger.error("Directory does not exist")
        return


if __name__ == "__main__":
    main()
