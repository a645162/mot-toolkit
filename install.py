import os
import argparse


def setup_mirrors():
    os.system("pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple")


def install_dep():
    ret = os.system("pip install -r requirements.txt")

    if ret != 0:
        print("Install necessary dependencies Failed!")
        exit(1)

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


def install_dep_dev():
    os.system("pip install -r r-dev-requirements.txt")

    print("Install Dev Done!")


def install_crawler():
    os.system("pip install -r r-crawler-requirements.txt")

    os.system("playwright install")

    print("Install Crawler Done!")


def install_torch():
    os.system("pip install -r r-torch-requirements.txt")

    print("Install Torch Done!")


def install_dataset():
    os.system("pip install -r r-dataset-requirements.txt")

    print("Install Dataset Done!")


def install_eval():
    os.system("pip install -r r-eval-requirements.txt")

    print("Install Eval Done!")


def install_labelme():
    os.system("pip install labelme")


def get_options():
    parser = argparse.ArgumentParser()

    parser.add_argument("--dev", "-d", action="store_true", help="Install Dev Dependencies")
    parser.add_argument("--torch", "-t", action="store_true", help="Install Torch Dependencies")

    parser.add_argument("--crawler", action="store_true", help="Install Crawler Dependencies")
    parser.add_argument("--dataset", action="store_true", help="Install Dataset Dependencies")

    parser.add_argument("--eval", action="store_true", help="Install Eval Dependencies")
    parser.add_argument("--labelme", action="store_true", help="Install LabelMe")

    parser.add_argument("--all", "-a", action="store_true", help="Install All Dependencies")

    return parser.parse_args()


if __name__ == "__main__":
    args = get_options()

    if args.all:
        args.dev = True
        args.torch = True
        args.crawler = True
        args.dataset = True
        args.eval = True

    print("=" * 20)
    print("mot-toolkit Installer")
    print("=" * 20)
    print("Install Options:")
    print("-" * 20)
    print(f"Dev: {args.dev}")
    print(f"Torch: {args.torch}")
    print(f"Crawler: {args.crawler}")
    print(f"Dataset: {args.dataset}")
    print(f"Eval: {args.eval}")
    print("-" * 20)
    print(f"LabelMe: {args.labelme}")
    print("=" * 20)

    install_dep()

    if args.dev:
        install_dep_dev()
    if args.torch:
        install_torch()
    if args.crawler:
        install_crawler()
    if args.dataset:
        install_dataset()
    if args.eval:
        install_eval()

    if args.labelme:
        install_labelme()
