import os
import multiprocessing

from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotationDirectory
from mot_toolkit.dl.common.torch_devices import wait_gpu_memory
from mot_toolkit.dl.model import sam2

process_count = 12

memory_per_process = 2.5
total_memory = 24
process_count = min(
    process_count,
    int(total_memory / memory_per_process)
)


def handle_sequence(sequence_dir_path):
    annotation_directory = XAnyLabelingAnnotationDirectory()
    annotation_directory.dir_path = sequence_dir_path
    annotation_directory.walk_dir(recursive=False)
    annotation_directory.sort_path(group_directory=True)

    annotation_directory.load_json_files()

    device = wait_gpu_memory(
        memory_size='3GiB',
        time_interval=2
    )

    model = sam2.sam_load(
        target_device=device,
        global_mode=False
    )

    for annotation_file_obj in annotation_directory.annotation_file:
        for rect_obj in annotation_file_obj.rect_annotation_list:
            x1 = float(rect_obj.x1)
            y1 = float(rect_obj.y1)
            x2 = float(rect_obj.x2)
            y2 = float(rect_obj.y2)
            bbox_xyxy: list[float] = [
                x1, y1, x2, y2
            ]
            image_path = annotation_file_obj.pic_path
            result = sam2.sam_predict_xyxy(
                source=image_path,
                bbox_xyxy=bbox_xyxy,
                model=model
            )
            if len(result) > 0:
                result = result[0]

                rect_obj.x1 = result[0]
                rect_obj.y1 = result[1]
                rect_obj.x2 = result[2]
                rect_obj.y2 = result[3]
            else:
                print("No result for", f"Object:{rect_obj.label}", image_path)

        annotation_file_obj.modifying()

    annotation_directory.save_json_files()


def handle_dataset(dataset_dir_path):
    video_list = os.listdir(dataset_dir_path)
    video_dir_path_list = []
    for video_name in video_list:
        video_dir_path = os.path.join(dataset_dir_path, video_name)
        if not os.path.isdir(video_dir_path):
            continue

        video_dir_path_list.append(video_dir_path)

    # For debug only
    # video_dir_path_list = video_dir_path_list[:1]

    with multiprocessing.Pool(processes=process_count) as pool:
        pool.map(handle_sequence, video_dir_path_list)


if __name__ == '__main__':
    multiprocessing.set_start_method('spawn')

    handle_dataset("/mnt/d/Datasets/MOT-Datasets/FVessel/FVessel_LabelMe_GT")
