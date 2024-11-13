import os
import multiprocessing
import json

from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotationDirectory, XAnyLabelingAnnotation
from mot_toolkit.dl.common.torch_devices import wait_gpu_memory
from mot_toolkit.dl.model import sam2

from mot_toolkit.utils.logs import get_logger

logger = get_logger()


def handle_sequence(
        sequence_dir_path: str,
        iou_threshold: float = 0.9,
        model_name: str = '',
        first_file_name: str = "",
        label_list: list[str] = None,
        copy_previous: bool = False
):
    first_file_name = first_file_name.strip()
    if label_list is None:
        label_list = []

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
        global_mode=False,
        model_name=model_name
    )

    previous_file_obj: XAnyLabelingAnnotation | None = None
    for annotation_file_obj in annotation_directory.annotation_file:
        if first_file_name:
            first_file_index = os.path.split(first_file_name)[0]
            current_file_name = annotation_file_obj.file_name_no_extension

            first_file_index = int(first_file_index)
            current_file_index = int(current_file_name)

            if current_file_index < first_file_index:
                continue

        for rect_obj in annotation_file_obj.rect_annotation_list:
            if len(label_list) > 0:
                if rect_obj.label not in label_list:
                    continue

            if copy_previous and previous_file_obj is not None:
                for previous_rect_obj in previous_file_obj.rect_annotation_list:
                    if rect_obj.label == previous_rect_obj.label:
                        rect_obj.x1 = previous_rect_obj.x1
                        rect_obj.y1 = previous_rect_obj.y1
                        rect_obj.x2 = previous_rect_obj.x2
                        rect_obj.y2 = previous_rect_obj.y2

                        break

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
                iou_threshold=iou_threshold,
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
        previous_file_obj = annotation_file_obj

    annotation_directory.save_json_files()


def generate_param_tuple(
        sequence_dir_path: str,
        iou_threshold: float = 0.9,
        model_name: str = '',
        first_file_name: str = "",
        label_list: list[str] = None,
        copy_previous: bool = False
):
    return (
        sequence_dir_path,
        iou_threshold,
        model_name,
        first_file_name,
        label_list,
        copy_previous
    )


def handle_dataset(
        dataset_dir_path: str,
        process_count: int = 1,
        iou_threshold: float = 0.9,
        model_name: str = ''
):
    video_list = os.listdir(dataset_dir_path)

    params_list = []
    for video_name in video_list:
        video_dir_path = os.path.join(dataset_dir_path, video_name)
        if not os.path.isdir(video_dir_path):
            continue

        params_list.append(
            generate_param_tuple(
                sequence_dir_path=video_dir_path,
                iou_threshold=iou_threshold,
                model_name=model_name,
                first_file_name="",
                label_list=[],
                copy_previous=False
            )
        )

    # For debug only
    # video_dir_path_list = video_dir_path_list[:1]

    with multiprocessing.Pool(processes=process_count) as pool:
        pool.map(handle_sequence, params_list)


def sam_fix(
        dataset_dir_path: str | list[str],
        process_count: int = 1,
        iou_threshold: float = 0.9,
        model_name: str = ''
):
    multiprocessing.set_start_method('spawn')

    if isinstance(dataset_dir_path, str):
        dataset_dir_path = [dataset_dir_path]

    for dataset_dir in dataset_dir_path:

        if not os.path.isdir(dataset_dir):
            logger.error(f"Dataset directory {dataset_dir} does not exist.")
            return

        handle_dataset(
            dataset_dir_path=dataset_dir,
            process_count=process_count,
            iou_threshold=iou_threshold,
            model_name=model_name
        )


def sam_fix_with_config(
        dataset_dir_path: str,
        iou_threshold: float = 0.9,
        config_path: str = "",
        model_name: str = ''
) -> tuple | None:
    if not os.path.isfile(config_path):
        return None
    model_name = model_name.strip()

    with open(config_path, 'r') as f:
        json_text = f.read()

    json_dict = json.loads(json_text)

    dataset_name: str = json_dict["dataset_name"]
    sequence_name: str = json_dict["sequence_name"]
    json_name: str = json_dict["json_name"]
    target_label: str = json_dict["target_label"]
    sam_model: str = json_dict["sam_model"]
    copy_previous: bool = json_dict["copy_previous"]

    if model_name:
        sam_model = model_name

    sequence_dir_path = os.path.join(dataset_dir_path, dataset_name, sequence_name)
    if not os.path.isdir(sequence_dir_path):
        logger.error(f"Sequence directory {sequence_dir_path} does not exist.")
        return None

    return generate_param_tuple(
        sequence_dir_path=sequence_dir_path,
        iou_threshold=iou_threshold,
        model_name=sam_model,
        first_file_name=json_name,
        label_list=[target_label],
        copy_previous=copy_previous
    )


def sam_fix_with_config_dir(
        dataset_dir_path: str | list[str],
        process_count: int = 1,
        iou_threshold: float = 0.9,
        config_path_list: list[str] = None,
        model_name: str = ''
):
    if config_path_list is None:
        logger.error("No valid config directory path.")
        return

    params_list = []
    for config_path in config_path_list:
        if not os.path.exists(config_path):
            logger.error(f"Config file {config_path} does not exist.")
            return

        param = sam_fix_with_config(
            dataset_dir_path=dataset_dir_path,
            iou_threshold=iou_threshold,
            config_path=config_path,
            model_name=model_name
        )

        if param is not None:
            params_list.append(param)

    with multiprocessing.Pool(processes=process_count) as pool:
        pool.map(handle_sequence, params_list)


if __name__ == '__main__':
    sam_fix("/mnt/d/Datasets/MOT-Datasets/FVessel/FVessel_LabelMe_GT")
