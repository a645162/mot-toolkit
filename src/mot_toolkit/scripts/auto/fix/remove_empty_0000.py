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

    for annotation_file_obj in annotation_directory.annotation_file_list:
        original_length = len(annotation_file_obj.rect_annotation_list)
        # 过滤掉所有 x1=x2 且 y1=y2 的边界框（宽高为0）
        filtered_rects = [
            rect_obj
            for rect_obj in annotation_file_obj.rect_annotation_list
            if not (rect_obj.x1 == rect_obj.x2 and rect_obj.y1 == rect_obj.y2)
        ]

        removed_count = original_length - len(filtered_rects)
        if removed_count > 0:
            # annotation_file_obj.label
            annotation_file_obj.rect_annotation_list = filtered_rects
            print(
                f"Removed {removed_count} empty bounding boxes in {annotation_file_obj.file_path}"
            )
            annotation_file_obj.modifying()

        # 按label转换为整数后排序
        try:
            annotation_file_obj.rect_annotation_list.sort(
                key=lambda rect: (
                    int(rect.label) if rect.label.isdigit() else float("inf")
                )
            )
            if (
                len(annotation_file_obj.rect_annotation_list) != original_length
                or len(filtered_rects) != original_length
            ):
                print(
                    f"Sorted bounding boxes by label in {annotation_file_obj.file_path}"
                )
                annotation_file_obj.modifying()
        except Exception as e:
            logger.error(
                f"Error sorting bounding boxes in {annotation_file_obj.file_path}: {str(e)}"
            )

    # 保存所有在目录中处理过的文件
    annotation_directory.save_json_files()


def remove_empty_bbox(dataset_dir_path: str | list[str], process_count: int = 8):
    # set_process_start_mode()

    if isinstance(dataset_dir_path, str):
        dataset_dir_path = [dataset_dir_path]

    with multiprocessing.Pool(processes=process_count) as pool:
        pool.map(handle_sequence, dataset_dir_path)


if __name__ == "__main__":
    base_dir = r"H:\Datasets\SMD\SMD_LabelMe_Ori"
    base_dir = r"H:\Datasets\SMD\SMD_LabelMe_Fix_20250509"

    sequence_path_list = get_dataset_dir_list(dataset_dir_path=base_dir, depth=1)
    print("Count", len(sequence_path_list))
    input("Press Enter to continue...")

    print("Start removing empty bounding boxes...")
    remove_empty_bbox(dataset_dir_path=sequence_path_list, process_count=io_cpu_count)
    print("Empty bounding box removal completed!")
