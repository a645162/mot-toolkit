import os
import argparse


def install_dep():
    os.system("pip install -r requirements.txt")

    command = """
    pyside6-rcc \
        ./Resources/PySide6/resources.qrc \
        -o ./src/mot_toolkit/gui/resources/resources.py
    """

    ret = os.system(command.strip())

    if ret != 0:
        print("Qt Resource Compile Failed!")
        exit(1)

    print("Qt Resource Compile Done!")

    print("Install Done!")


# os.system("pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple")
def install_dep_dev():
    os.system("pip install -r r-dev-requirements.txt")

    print("Install Dev Done!")


def install_torch():
    os.system("pip install -r r-torch-requirements.txt")

    print("Install Torch Done!")


def get_options():
    parser = argparse.ArgumentParser()

    parser.add_argument("--dev", "-d", action="store_true", help="Install Dev Dependencies")
    parser.add_argument("--torch", "-t", action="store_true", help="Install Torch Dependencies")
    parser.add_argument("--all", "-a", action="store_true", help="Install All Dependencies")

    return parser.parse_args()


if __name__ == "__main__":
    args = get_options()

    if args.dev:
        install_dep_dev()
    elif args.torch:
        install_torch()
    elif args.all:
        install_dep()
        install_dep_dev()
        install_torch()
    else:
        install_dep()
