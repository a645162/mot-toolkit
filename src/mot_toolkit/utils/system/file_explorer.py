import os
import subprocess
import sys
from pathlib import Path


def show_in_explorer(file_path: str):
    """
    在文件资源管理器中打开指定路径的文件或目录。

    :param file_path: 文件或目录的路径。
    """
    file_path = Path(file_path)  # 确保pathlib.Path对象

    if os.name == 'nt':  # Windows
        subprocess.run(['explorer', os.path.dirname(file_path)])
    elif os.name == 'posix':  # macOS and Linux
        if sys.platform == 'darwin':  # macOS
            subprocess.run(['open', os.path.dirname(file_path)])
        else:  # Linux
            subprocess.run(['xdg-open', os.path.dirname(file_path)])
