import re
import sys


def is_windows():
    return 'win' in sys.platform.lower()


def is_windows_path(path):
    # 修改后的Windows路径正则表达式
    windows_path_regex = r'^(?:[a-zA-Z]:\\{1,2})?(?:\\[^\\/:*?"<>|]+\\)*[^\\/:*?"<>|]+\\?$'
    return bool(re.match(windows_path_regex, path))


def is_unix_path(path):
    unix_path_regex = r'^(/)?([^/\0]+(/)?)*[^/\0]+$'
    return bool(re.match(unix_path_regex, path))


def check_path(path) -> bool:
    if not path:
        return False
    if is_windows():
        return is_windows_path(path)
    else:
        return is_unix_path(path)


if __name__ == "__main__":
    print(f"Is Windows: {is_windows()}")

    # 测试路径
    paths = [
        "C:\\\\Program Files\\MyApp",
        "C:\\\\Program Files\\MyApp\\",
        "C:\\Program Files\\MyApp",
        "C:\\Program Files\\MyApp\\",
        "/home/user/Documents",
        "invalid\\path/with/mix\\slashes",
        "relative/path",
        "C:/invalid/mix/slash/path",
        ""
    ]

    for path in paths:
        print(f"{path}: {check_path(path)}")
