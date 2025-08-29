from typing import Tuple

from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotationDirectory
from mot_toolkit.gui.view.interface.spilt.common.datasets_spilt_type import DatasetSpiltType


def get_annotation_directory_by_ratio(
        sequence_dir: str,
        train_ratio: float,
        val_ratio: float,
        test_ratio: float = 0,
        auto_load: bool = True
) -> Tuple[
    XAnyLabelingAnnotationDirectory,
    XAnyLabelingAnnotationDirectory,
    XAnyLabelingAnnotationDirectory,
]:
    total_ratio = train_ratio + val_ratio + test_ratio
    train_ratio = train_ratio / total_ratio
    val_ratio = val_ratio / total_ratio
    test_ratio = test_ratio / total_ratio

    total_dir_obj = XAnyLabelingAnnotationDirectory()
    total_dir_obj.dir_path = sequence_dir
    total_dir_obj.walk_dir(recursive=False)
    total_dir_obj.sort_path(group_directory=True)

    train_dir_obj = XAnyLabelingAnnotationDirectory()
    val_dir_obj = XAnyLabelingAnnotationDirectory()
    test_dir_obj = XAnyLabelingAnnotationDirectory()

    total_file_list = total_dir_obj.file_list

    total_file_count = len(total_file_list)
    train_file_count = int(total_file_count * train_ratio)
    if test_ratio == 0:
        val_file_count = total_file_count - train_file_count
    else:
        val_file_count = int(total_file_count * val_ratio)

    train_dir_obj.dir_path = sequence_dir
    val_dir_obj.dir_path = sequence_dir
    test_dir_obj.dir_path = sequence_dir

    train_dir_obj.file_list = total_file_list[:train_file_count]
    val_dir_obj.file_list = total_file_list[train_file_count:train_file_count + val_file_count]
    test_dir_obj.file_list = total_file_list[train_file_count + val_file_count:]

    train_dir_obj.set_file_list(train_dir_obj.file_list)
    val_dir_obj.set_file_list(val_dir_obj.file_list)
    test_dir_obj.set_file_list(test_dir_obj.file_list)

    train_dir_obj.spilt_type = DatasetSpiltType.Train
    val_dir_obj.spilt_type = DatasetSpiltType.Val
    test_dir_obj.spilt_type = DatasetSpiltType.Test

    if auto_load:
        train_dir_obj.load_json_files()
        val_dir_obj.load_json_files()
        test_dir_obj.load_json_files()

    return train_dir_obj, val_dir_obj, test_dir_obj
