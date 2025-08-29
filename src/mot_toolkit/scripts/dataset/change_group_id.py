import multiprocessing
from typing import List

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list
from mot_toolkit.datatype.utils.list_data import sort_int_str_list
from mot_toolkit.datatype.xanylabeling import (
    XAnyLabelingAnnotationDirectory,
    XAnyLabelingAnnotation,
)

replace_rule = {
    "1": "0",  # Ship
    "2": "12",  # Other
    "3": "1",  # Cargo ship
    "4": "2",  # Fishing Boat
    "5": "3",  # Container Ship
    "6": "4",  # Passenger Ship
    "7": "13",  # Raft
    "8": "5",  # Island
    "9": "6",  # Buoy
    "10": "7",  # Obstacle
    "11": "8",  # Tugboat
}


def handle_sequence(sequence_dir):
    annotation_directory = XAnyLabelingAnnotationDirectory()
    annotation_directory.dir_path = sequence_dir
    annotation_directory.walk_dir(recursive=False)
    annotation_directory.sort_path(group_directory=True)

    annotation_directory.load_json_files()

    def replace_group_id(file_obj: XAnyLabelingAnnotation, index: int):
        task_id_list: List[str] = list(replace_rule.keys())
        task_id_list = sort_int_str_list(task_id_list)

        annotation_obj_list_task_list = [
            file_obj.get_list_by_group_id(group_id) for group_id in task_id_list
        ]

        for annotation_obj_list in annotation_obj_list_task_list:
            for annotation_obj in annotation_obj_list:
                current_group_id = annotation_obj.group_id

                if current_group_id in replace_rule:
                    new_group_id = replace_rule[current_group_id]
                    annotation_obj.group_id = new_group_id
                    file_obj.modifying()

        file_obj.save()

    annotation_directory.do_for_each_file(func=replace_group_id)


base_dir = r"H:\Datasets\MaritimeTrackAllData\LabelMe1"
sequence_path_list = get_dataset_dir_list(dataset_dir_path=base_dir, depth=1)

# with multiprocessing.Pool(26) as pool:
#     pool.map(handle_sequence, sequence_path_list)

for sequence_path in sequence_path_list:
    print(sequence_path)
    handle_sequence(sequence_path)
