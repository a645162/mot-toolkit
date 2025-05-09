import sys
from mot_toolkit.scripts.auto.sam.auto_sam_fix import (
    handle_sequence,
    set_process_start_mode,
)


def main():
    """处理单个序列的主函数"""
    if len(sys.argv) < 2:
        print("Usage: python -m mot_toolkit.scripts.auto.sam.sam_seq <sequence_path>")
        return

    set_process_start_mode()
    sequence_path = sys.argv[1]

    print(f"Processing sequence: {sequence_path} on GPU")
    handle_sequence(
        sequence_dir_path=sequence_path, iou_threshold=0.6, model_name="sam2.1_l.pt"
    )
    print(f"Finished processing: {sequence_path}")


if __name__ == "__main__":
    main()
