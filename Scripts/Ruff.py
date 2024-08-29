import os


def check_by_ruff():
    if os.path.exists(".ruff.toml"):
        os.system("ruff check .")
    else:
        os.system("ruff check ../")


if __name__ == "__main__":
    check_by_ruff()
