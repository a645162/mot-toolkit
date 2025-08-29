"""
Script to check if bounding boxes exceed image boundaries
Detects invalid annotations in the dataset, including:
1. Negative coordinates
2. Boxes extending beyond image boundaries
3. Zero or negative dimensions
"""

import os
from multiprocessing import pool
from typing import List, Tuple
from pathlib import Path

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list
from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotationDirectory


def check_bbox_boundary(
    rect_obj, image_width: int, image_height: int
) -> Tuple[bool, str]:
    """
    Check if a single bounding box is valid within image boundaries

    Args:
        rect_obj: Bounding box object containing coordinates and dimensions
        image_width: Width of the image
        image_height: Height of the image

    Returns:
        is_valid: Whether the bounding box is valid
        reason: Description of why the box is invalid (if applicable)
    """
    # Get bounding box coordinates and dimensions
    x, y = rect_obj.x, rect_obj.y
    w, h = rect_obj.width, rect_obj.height

    # Check if dimensions are negative or zero
    if w <= 0 or h <= 0:
        return False, "Bounding box width or height is less than or equal to 0"

    # Check for negative coordinates
    if x < 0 or y < 0:
        return False, "Bounding box has negative coordinates"

    # Check if box extends beyond image boundaries
    if x + w > image_width or y + h > image_height:
        return False, "Bounding box extends beyond image boundaries"

    return True, ""


def handle_seq(sequence_dir: str):
    """
    Process all annotation files in a single sequence directory

    Args:
        sequence_dir: Path to the sequence directory
    """
    # Initialize annotation directory object
    annotation_directory = XAnyLabelingAnnotationDirectory()
    annotation_directory.dir_path = sequence_dir
    annotation_directory.walk_dir(recursive=False)
    annotation_directory.sort_path(group_directory=True)

    # Load all JSON annotation files
    annotation_directory.load_json_files()

    # Process each annotation file
    for file_obj in annotation_directory.annotation_file_list:
        # Get image dimensions
        image_width = file_obj.image_width
        image_height = file_obj.image_height

        # Validate image dimensions
        if image_width is None or image_height is None:
            print(f"Warning: Cannot get image dimensions for {file_obj.file_path}")
            continue

        # Check each bounding box in the file
        for rect_obj in file_obj.rect_annotation_list:
            is_valid, reason = check_bbox_boundary(
                rect_obj, image_width=image_width, image_height=image_height
            )

            # Output information for invalid boxes
            if not is_valid:
                print(f"Invalid bbox found in {file_obj.file_path}")
                print(f"Label: {rect_obj.label}")
                print(f"Reason: {reason}")
                print(f"Box info: {rect_obj}")
                print()


def main():
    """Main function: Set up dataset path and start processing"""
    # Set dataset root directory
    base_dir = r"H:\Datasets\MaritimeTrackAllData\LabelMe"  # Change to your actual dataset path

    # Get list of sequence directories to process
    seq_list = get_dataset_dir_list(
        dataset_dir_path=base_dir, depth=1, check_disable=True
    )

    # Single process mode (commented out by default)
    # for seq_dir_path in seq_list:
    #     handle_seq(seq_dir_path)

    # Multi-process mode (enabled by default)
    with pool.Pool(processes=8) as p:
        p.map(handle_seq, seq_list)

    print("Processing completed")


if __name__ == "__main__":
    main()
