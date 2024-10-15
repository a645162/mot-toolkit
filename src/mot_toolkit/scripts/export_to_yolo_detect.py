import os
import shutil

from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotationDirectory


def handle_sequence(sequence_dir_path, video_name, image_dir, label_dir):
    annotation_directory = XAnyLabelingAnnotationDirectory()
    annotation_directory.dir_path = sequence_dir_path
    annotation_directory.walk_dir(recursive=False)
    annotation_directory.sort_path(group_directory=True)

    annotation_directory.load_json_files()

    image_path_list = [
        annotation_json_path.replace(".json", ".jpg")
        for annotation_json_path in annotation_directory.file_list
    ]

    for image_file_path in image_path_list:
        old_name = os.path.basename(image_file_path)
        new_name = f"{video_name}_{old_name}"
        new_path = os.path.join(image_dir, new_name)

        if os.path.exists(new_path):
            # Remove if already exists
            os.remove(new_path)

        shutil.copyfile(image_file_path, new_path)

    annotation_directory.export_yolo_annotation(
        label_dir,
        f"{video_name}_",
        {
            "*": "0"
        }
    )


task_list = []


def __convert_mot_to_yolo_task(video_dir, save_dir):
    os.makedirs(save_dir, exist_ok=True)

    image_dir = os.path.join(save_dir, "images")
    label_dir = os.path.join(save_dir, "labels")

    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(label_dir, exist_ok=True)

    video_list = os.listdir(video_dir)
    for video_name in video_list:
        video_dir_path = os.path.join(video_dir, video_name)

        sequence_list = os.listdir(video_dir_path)
        for sequence in sequence_list:
            sequence_dir_path = os.path.join(video_dir_path, sequence)

            task_list.append((sequence_dir_path, video_name, image_dir, label_dir))

            return


def __handle_task_multiprocess():
    from multiprocessing import Pool
    pool = Pool()
    pool.starmap(handle_sequence, task_list)


if __name__ == "__main__":
    source_dir = [
        "/mnt/h/Datasets/TrackShipOnlineVideo/sea_video_20240313_part2/OnboardTL",
        "/mnt/h/Datasets/TrackShipOnlineVideo/sea_video_20240313_part4/OnshoreTL"
    ]

    yolo_save_dir = "/mnt/h/Datasets/TrackShipOnlineVideo/TrackShipOnlineVideoYOLO"

    if os.path.exists(yolo_save_dir):
        shutil.rmtree(yolo_save_dir)

    for source in source_dir:
        __convert_mot_to_yolo_task(source, yolo_save_dir)

    __handle_task_multiprocess()
