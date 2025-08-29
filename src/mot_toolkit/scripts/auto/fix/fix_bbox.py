import multiprocessing

import cv2

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list
from mot_toolkit.datatype.xanylabeling import (
    XAnyLabelingAnnotationDirectory,
)
from mot_toolkit.config.hardware import io_cpu_count
from mot_toolkit.utils.logs import get_logger

logger = get_logger()


def set_process_start_mode():
    # Only DL need to set start method to spawn.
    try:
        logger.info("Try to set start multiprocessing method to spawn.")
        multiprocessing.set_start_method("spawn")
        logger.info("Set start multiprocessing method to spawn.")
    except Exception as e:
        logger.error(e)


def handle_sequence(sequence_dir_path: str):
    annotation_directory = XAnyLabelingAnnotationDirectory()
    annotation_directory.dir_path = sequence_dir_path
    annotation_directory.walk_dir(recursive=False)
    annotation_directory.sort_path(group_directory=True)
    annotation_directory.load_json_files()

    if len(annotation_directory.annotation_file_list) == 0:
        logger.error(f"No annotation files found in {sequence_dir_path}")
        return

    pic_path = annotation_directory.annotation_file_list[0].pic_path
    try:
        img = cv2.imread(pic_path)
        if img is None:
            logger.error(f"Invalid image path: {pic_path}")
            return
        height, width = img.shape[:2]
    except Exception as e:
        logger.error(f"Error reading image {pic_path}: {str(e)}")
        return

    height -= 1
    width -= 1

    if height <= 0 or width <= 0:
        logger.error(f"Invalid image size: {pic_path}")
        return

    for annotation_file_obj in annotation_directory.annotation_file_list:
        modified = False
        for rect_obj in annotation_file_obj.rect_annotation_list:
            x1 = float(rect_obj.x1)
            y1 = float(rect_obj.y1)
            x2 = float(rect_obj.x2)
            y2 = float(rect_obj.y2)

            # Clamp coordinates to image boundaries
            x1_clamped = max(0, min(x1, width))
            y1_clamped = max(0, min(y1, height))
            x2_clamped = max(0, min(x2, width))
            y2_clamped = max(0, min(y2, height))

            # Ensure valid bounding box order
            x1_clamped, x2_clamped = sorted([x1_clamped, x2_clamped])
            y1_clamped, y2_clamped = sorted([y1_clamped, y2_clamped])

            if (x1_clamped, y1_clamped, x2_clamped, y2_clamped) != (x1, y1, x2, y2):
                rect_obj.x1 = x1_clamped
                rect_obj.y1 = y1_clamped
                rect_obj.x2 = x2_clamped
                rect_obj.y2 = y2_clamped
                modified = True

        if modified:
            print(f"Modified bounding box in {annotation_file_obj.file_path}")
            annotation_file_obj.modifying()

    # Save all changes at once after processing all files in directory
    annotation_directory.save_json_files()


def fix_bbox(dataset_dir_path: str | list[str], process_count: int = 1):
    # set_process_start_mode()

    if isinstance(dataset_dir_path, str):
        dataset_dir_path = [dataset_dir_path]

    with multiprocessing.Pool(processes=process_count) as pool:
        pool.map(handle_sequence, dataset_dir_path)


if __name__ == "__main__":
    base_dir = r"/mnt/h/Datasets/MaritimeTrackAllData/LabelMe"
    sequence_path_list = dir_list = get_dataset_dir_list(
        dataset_dir_path=base_dir, depth=1
    )
    print("Count", len(dir_list))
    input("Press Enter to continue...")

    print("Start fixing bounding box...")
    fix_bbox(dataset_dir_path=dir_list, process_count=io_cpu_count)
    print("Bounding box fixing completed!")
