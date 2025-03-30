import multiprocessing

from mot_toolkit.scripts.auto.sam.auto_sam_fix import (
    handle_sequence,
    set_process_start_mode,
)
from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list


def handle_sequence_current(sequence_path):
    handle_sequence(
        sequence_dir_path=sequence_path, iou_threshold=0.7, model_name="sam2.1_l.pt"
    )


def main():
    set_process_start_mode()

    base_dir = r"H:\Datasets\SMD\SMD_LabelMe"
    sequence_path_list = get_dataset_dir_list(dataset_dir_path=base_dir, depth=1)

    with multiprocessing.Pool(8) as pool:
        pool.map(handle_sequence_current, sequence_path_list)


if __name__ == "__main__":
    main()
