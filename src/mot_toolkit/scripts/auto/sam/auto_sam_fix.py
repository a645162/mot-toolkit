import os
import multiprocessing

from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotationDirectory
from mot_toolkit.dl.model.sam2 import sam_predict_xyxy

process_count = 4


# sam_predict_xyxy()

def handle_sequence(sequence_dir_path):
    annotation_directory = XAnyLabelingAnnotationDirectory()
    annotation_directory.dir_path = sequence_dir_path
    annotation_directory.walk_dir(recursive=False)
    annotation_directory.sort_path(group_directory=True)

    annotation_directory.load_json_files()

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
            result = sam_predict_xyxy(image_path, bbox_xyxy)
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

    dataset_dir_path = "/mnt/d/Datasets/MOT-Datasets/FVessel/FVessel_LabelMe_GT"
    handle_dataset(dataset_dir_path)
