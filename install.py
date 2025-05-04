import os
import argparse
from typing import Union, List


def setup_mirrors():
    os.system(
        "pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple"
    )


def install_conda_packages(
    packages: Union[str, List[str]] = "numpy",
):
    if isinstance(packages, str):
        packages = [packages]

    package_str = " ".join(packages)
    ret = os.system(f"conda install {package_str} -y")
    return ret == 0


def install_pip_packages(
    packages: Union[str, List[str]],
):
    if isinstance(packages, str):
        packages = [packages]

    package_str = " ".join(packages)
    ret = os.system(f"pip install {package_str}")
    return ret == 0


def install_pip_requirements_txt(
    file_paths: Union[str, List[str]] = "requirements.txt",
) -> bool:
    if isinstance(file_paths, str):
        file_paths = [file_paths]

    is_success = True
    for file_path in file_paths:
        ret = os.system(f"pip install -r {file_path}")
        if ret != 0:
            print(f"Install {file_path} Failed!")
            is_success = False
            break

    return is_success


def install_package(
    package_name: Union[str, List[str]] = "pip", update: bool = False
) -> bool:
    if isinstance(package_name, str):
        package_name = [package_name]

    update_flag = ""
    if update:
        update_flag = " -U "

    package_str = " ".join(package_name)

    ret = os.system(f"pip install {update_flag} {package_str}")

    return ret == 0


def install_dep():
    ret = install_pip_requirements_txt()

    if not ret:
        print("Install necessary dependencies Failed!")
        exit(1)


def install_gui():
    ret = install_pip_requirements_txt("r-gui-requirements.txt")

    if not ret:
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

    print("Install GUI Done!")


def install_dep_dev():
    install_pip_requirements_txt("r-dev-requirements.txt")

    print("Install Dev Done!")


def install_crawler():
    install_pip_requirements_txt("r-crawler-requirements.txt")

    os.system("playwright install")

    print("Install Crawler Done!")


def install_dl():
    install_pip_requirements_txt("r-dl-requirements.txt")

    print("Install Torch Done!")


def install_dataset():
    install_pip_requirements_txt("r-dataset-requirements.txt")

    print("Install Dataset Done!")


def install_eval():
    install_pip_requirements_txt("r-eval-requirements.txt")

    print("Install Eval Done!")


def install_llms():
    install_pip_requirements_txt("r-llms-requirements.txt")

    print("Install LLMs Done!")


def install_labelme():
    os.system("pip install labelme")


def check_is_intel_cpu_platform() -> bool:
    import cpuinfo
    import re

    info = cpuinfo.get_cpu_info()
    cpu_name = info["brand_raw"]

    if re.search(r"Intel", cpu_name):
        return True

    return False


def update():
    pass


def upgrade():
    install_package("pip", update=True)
    install_package("setuptools", update=True)

    install_package("pyside6", update=True)

    install_package(
        [
            "ultralytics",
            "opencv-python",
        ],
        update=True,
    )

    print("Upgrade Done!")


def get_options():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dev", "-d", action="store_true", help="Install Dev Dependencies"
    )
    parser.add_argument("--gui", action="store_true", help="Install GUI Dependencies")
    parser.add_argument("--dl", action="store_true", help="Install Torch Dependencies")
    parser.add_argument("--llms", action="store_true", help="Install LLMs Dependencies")

    parser.add_argument(
        "--crawler", action="store_true", help="Install Crawler Dependencies"
    )
    parser.add_argument(
        "--dataset", action="store_true", help="Install Dataset Dependencies"
    )

    parser.add_argument("--eval", action="store_true", help="Install Eval Dependencies")
    parser.add_argument("--labelme", action="store_true", help="Install LabelMe")

    parser.add_argument(
        "--all", "-a", action="store_true", help="Install All Dependencies"
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = get_options()

    # For debug
    # args.all = True

    if args.all:
        args.dev = True
        args.gui = True
        args.dl = True
        args.llms = True
        args.crawler = True
        args.dataset = True
        args.eval = True

    print("=" * 20)
    print("mot-toolkit Installer")
    print("=" * 20)
    print("Install Options:")
    print("-" * 20)
    print(f"Dev: {args.dev}")
    print(f"GUI: {args.gui}")
    print(f"Deep Learning: {args.dl}")
    print(f"LLMs: {args.llms}")
    print(f"Crawler: {args.crawler}")
    print(f"Dataset: {args.dataset}")
    print(f"Eval: {args.eval}")
    print("-" * 20)
    print(f"LabelMe: {args.labelme}")
    print("=" * 20)

    install_dep()

    if args.dev:
        install_dep_dev()
    if args.gui:
        install_gui()
    if args.dl:
        install_dl()
    if args.llms:
        install_llms()
    if args.crawler:
        install_crawler()
    if args.dataset:
        install_dataset()
    if args.eval:
        install_eval()

    if args.labelme:
        install_labelme()

    if check_is_intel_cpu_platform():
        print("Intel CPU Platform Detected!")
        print("Installing numpy with conda(with MKL Support)...")
        install_conda_packages("numpy")
