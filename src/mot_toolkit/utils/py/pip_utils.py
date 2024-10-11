import importlib.util


def check_package_is_installed(package_name: str) -> bool:
    try:
        # 尝试查找包的spec
        if importlib.util.find_spec(package_name):
            return True
        else:
            return False
    except ImportError:
        return False


if __name__ == "__main__":
    package = "cv2"
    is_installed = check_package_is_installed(package)
    print(f"Package '{package}' is installed: {is_installed}")
