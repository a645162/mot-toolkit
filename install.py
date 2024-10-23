import os


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


if __name__ == "__main__":
    install_dep()
