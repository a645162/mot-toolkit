import platform


def is_macos():
    return platform.system().lower() == "darwin"
