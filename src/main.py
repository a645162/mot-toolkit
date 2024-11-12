import argparse

from mot_toolkit.main_gui import main as main_gui_main
from mot_toolkit.main_gui import test as main_gui_test


def get_opts():
    parser = argparse.ArgumentParser(description='MOT ToolKit')

    parser.add_argument('--test', action='store_true', help='Start Test')

    return parser.parse_args()


def main():
    opts = get_opts()

    if opts.__contains__('test') and opts.test:
        print('Start Test')
        main_gui_test()
        return

    main_gui_main()


if __name__ == "__main__":
    main()
