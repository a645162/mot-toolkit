import sys


def is_linux() -> bool:
    return sys.platform == "linux"


if __name__ == "__main__":
    print(is_linux())  # Expected: True if running on a linux machine, False otherwise
