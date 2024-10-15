import os
import shutil

from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotationDirectory


def handle_sequence(sequence_dir_path, target_path):
    img_dir_path = os.path.join(target_path, "img1")
    gt_dir_path = os.path.join(target_path, "gt")
    seq_info_path = os.path.join(target_path, "seqinfo.ini")

    os.makedirs(target_path, exist_ok=True)
    os.makedirs(img_dir_path, exist_ok=True)
    os.makedirs(gt_dir_path, exist_ok=True)

    annotation_directory = XAnyLabelingAnnotationDirectory()
    annotation_directory.dir_path = sequence_dir_path
    annotation_directory.walk_dir(recursive=False)
    annotation_directory.sort_path(group_directory=True)

    annotation_directory.load_json_files()

    image_path_list = [
        annotation_json_path.replace(".json", ".jpg")
        for annotation_json_path in annotation_directory.file_list
    ]

    # Copy Image
    for image_file_path in image_path_list:
        old_name = os.path.basename(image_file_path)
        new_path = os.path.join(img_dir_path, old_name)

        if os.path.exists(new_path):
            # Remove if already exists
            os.remove(new_path)

        shutil.copyfile(image_file_path, new_path)

    # Generate gt.txt
    gt_path = os.path.join(gt_dir_path, "gt.txt")
    gt_content = annotation_directory.to_mot_gt_txt()
    with open(gt_path, "w") as f:
        f.write(gt_content)

    # Generate seqinfo.ini
    seq_info_content = annotation_directory.to_mot_seq_info_ini()
    with open(seq_info_path, "w") as f:
        f.write(seq_info_content)


task_list = []


def __convert_mot_to_dt(video_dir, save_dir):
    os.makedirs(save_dir, exist_ok=True)

    video_list = os.listdir(video_dir)
    video_list = [
        video_name
        for video_name in video_list
        if os.path.isdir(os.path.join(video_dir, video_name))
    ]
    for video_name in video_list:
        video_dir_path = os.path.join(video_dir, video_name)

        sequence_list = os.listdir(video_dir_path)
        sequence_list = [
            sequence
            for sequence in sequence_list
            if os.path.isdir(os.path.join(video_dir_path, sequence))
        ]

        for sequence in sequence_list:
            sequence_dir_path = os.path.join(video_dir_path, sequence)

            target_dir = os.path.join(save_dir, f"{video_name}-{sequence}")

            task_list.append((sequence_dir_path, target_dir))
            # handle_sequence(sequence_dir_path, target_dir)

            # return


def __handle_task_multiprocess():
    from multiprocessing import Pool
    pool = Pool()
    pool.starmap(handle_sequence, task_list)


if __name__ == "__main__":
    source_dir = [
        "/mnt/h/Datasets/TrackShipOnlineVideo/sea_video_20240313_part2/OnboardTL",
        "/mnt/h/Datasets/TrackShipOnlineVideo/sea_video_20240313_part4/OnshoreTL"
    ]

    dt_save_dir = "/mnt/h/Datasets/TrackShipOnlineVideo/TrackShipOnlineVideoDT"

    if os.path.exists(dt_save_dir):
        shutil.rmtree(dt_save_dir)

    for source in source_dir:
        __convert_mot_to_dt(source, dt_save_dir)

    __handle_task_multiprocess()
