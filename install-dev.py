import os

from install import install_dep


# os.system("pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple")
def install_dep_dev():
    os.system("pip install -r r-dev-requirements.txt")

    print("Install Dev Done!")


if __name__ == "__main__":
    install_dep()
    install_dep_dev()
