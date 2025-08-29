import os


def stats_file_count(dir_path: str, ext_name: str = "") -> int:
    count = 0
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if ext_name == "" or file.endswith(ext_name):
                count += 1
    return count
