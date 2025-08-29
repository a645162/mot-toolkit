import os

from multiprocessing import pool
from typing import List, Tuple

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list

from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotationDirectory


def handle_seq(sequence_dir):
    annotation_directory = XAnyLabelingAnnotationDirectory()
    annotation_directory.dir_path = sequence_dir
    annotation_directory.walk_dir(recursive=False)
    annotation_directory.sort_path(group_directory=True)

    annotation_directory.load_json_files()

    for file_obj in annotation_directory.annotation_file_list:
        duplicate_label_pair_list: List[Tuple] = []

        for rect_obj in file_obj.rect_annotation_list:
            for other_rect_obj in file_obj.rect_annotation_list:
                if rect_obj.label == other_rect_obj.label:
                    continue

                iou = rect_obj.get_iou(other_rect_obj)
                if iou > 0.95:
                    found = False
                    for label_pair in duplicate_label_pair_list:
                        if (
                                rect_obj.label in label_pair and
                                other_rect_obj.label in label_pair
                        ):
                            found = True
                            break

                    if found:
                        continue

                    duplicate_label_pair_list.append((rect_obj.label, other_rect_obj.label))

                    print(f"Duplicate bbox ({round(iou, 2)}) found in {file_obj.file_path}")
                    print(f"rect_obj: {rect_obj}")
                    print(f"other_rect_obj: {other_rect_obj}")
                    print()


def main():
    base_dir = r"H:\Datasets\MaritimeTrackAllData\LabelMe"

    seq_list = get_dataset_dir_list(
        dataset_dir_path=base_dir,
        depth=1,
        check_disable=True
    )

    # # Single process
    # for seq_dir_path in seq_list:
    #     handle_seq(seq_dir_path)

    # Multi process
    with pool.Pool(processes=8) as p:
        p.map(handle_seq, seq_list)

    print("Done")


if __name__ == '__main__':
    main()
