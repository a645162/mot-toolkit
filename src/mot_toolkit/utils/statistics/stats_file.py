import os


def stats_file_count(
        directory_path: str,
        file_extension: str,
        recursive: bool = False
) -> int:
    """
    Count the number of files with the specified extension in the specified directory.

    Args:
        directory_path (str): The directory path to search for files.
        file_extension (str): The file extension to search for.
        recursive (bool, optional): Whether to search recursively in the specified directory. Defaults to False.

    Returns:
        int: The number of files with the specified extension in the specified directory.
    """

    if not directory_path or not file_extension:
        return 0

    directory_path = directory_path.strip()
    file_extension = file_extension.strip()

    if not os.path.isdir(directory_path):
        return 0

    if not file_extension.startswith("."):
        file_extension = "." + file_extension

    count = 0

    if recursive:
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith(file_extension):
                    count += 1
    else:
        for file in os.listdir(directory_path):
            if file.endswith(file_extension):
                count += 1

    return count
