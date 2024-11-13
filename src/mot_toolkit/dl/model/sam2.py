from enum import Enum
import os

import cv2

from ultralytics import SAM
from ultralytics import FastSAM

from mot_toolkit.dl.common import torch_devices
from mot_toolkit.dl.utils.value_calc import calculate_iou
from mot_toolkit.utils.logs import get_logger

model_sam: SAM | FastSAM | None = None

logger = get_logger()

device = torch_devices.get_device()

# Try to fix AMD Gpu error
if torch_devices.is_amd_rocm_device(device=device):
    logger.info("AMD ROCm device detected.")
    # https://github.com/pytorch/pytorch/issues/138067
    os.environ["TORCH_BLAS_PREFER_HIPBLASLT"] = "0"
    os.environ["DISABLE_ADDMM_CUDA_LT"] = "1"


# https://docs.ultralytics.com/zh/models/sam-2/#segment-everything
class SamModelType(Enum):
    SAM_2_1_Tiny = "sam2.1_t.pt"
    SAM_2_1_Small = "sam2.1_s.pt"
    SAM_2_1_Base = "sam2.1_b.pt"
    SAM_2_1_Large = "sam2.1_l.pt"
    FAST_SAM_S = "FastSAM-s.pt"
    FAST_SAM_X = "FastSAM-x.pt"


def get_sam_model_list() -> list[str]:
    return [model.value for model in SamModelType]


def get_sam_model_by_name(
        model_name: str = ""
) -> SamModelType:
    for model in SamModelType:
        if model.value == model_name:
            return model

    return SamModelType.SAM_2_1_Large


def sam_is_loaded() -> bool:
    global model_sam

    if model_sam is not None:
        return True

    if (
            isinstance(model_sam, SAM) or
            isinstance(model_sam, FastSAM)
    ):
        return True

    return False


def sam_load(
        target_device=None,
        global_mode=True,
        model_name: str = ""
) -> SAM | FastSAM | None:
    model: SAM | FastSAM | None = None

    if global_mode:
        global model_sam
        model = model_sam

    model_type: SamModelType = get_sam_model_by_name(model_name)

    if model is None:
        if (
                model_type == SamModelType.FAST_SAM_S or
                model_type == SamModelType.FAST_SAM_X
        ):
            model = FastSAM(model_type.value)
        else:
            model = SAM(model_type.value)

        if target_device is not None:
            model.to(target_device)
        else:
            model.to(device)

    if global_mode:
        model_sam = model

    return model


def sam_predict_xyxy(
        source,
        bbox_xyxy: list[float],
        iou_threshold: float = 0.4,
        model: SAM | FastSAM = None
) -> list[list[float]]:
    result_list: list[list[float]] = []

    prompt_bbox_tuple = (bbox_xyxy[0], bbox_xyxy[1], bbox_xyxy[2], bbox_xyxy[3])

    if model is None:
        if not sam_is_loaded():
            sam_load()

        global model_sam
        model = model_sam

    results = model.predict(
        source=source,
        bboxes=bbox_xyxy,
    )

    for result in results:
        logger.info(f"Detected {len(result.masks)} masks(boxes).")

        xy_xy_list = result.boxes.cpu().xyxy.numpy().tolist()

        for i, xy_xy in enumerate(xy_xy_list):
            box: list[float] = [xy_xy[0], xy_xy[1], xy_xy[2], xy_xy[3]]

            iou = calculate_iou(prompt_bbox_tuple, box)
            logger.info(f"[{i}] IOU: {iou}")

            if iou > iou_threshold:
                result_list.append(box)
            else:
                logger.info(f"[{i}] IOU({iou}) is too low(<{iou_threshold}), skip.")

    return result_list


def sam_predict_xyxy_near(
        image_path,
        bbox_xyxy: list[float],
        padding: int = -1,
        iou_threshold: float = 0.4,
        model: SAM | FastSAM = None
) -> list[list[float]]:
    result_list: list[list[float]] = []

    new_image = cv2.imread(image_path)

    image_width = new_image.shape[1]
    image_height = new_image.shape[0]

    x1, y1, x2, y2 = bbox_xyxy
    x, y, w, h = x1, y1, x2, y2

    if padding == -1:
        padding = max(w, h) // 2

    prompt_bbox_tuple = (x1, y1, x2, y2)

    new_x1 = int(bbox_xyxy[0] - padding)
    new_y1 = int(bbox_xyxy[1] - padding)
    new_x2 = int(bbox_xyxy[2] + padding)
    new_y2 = int(bbox_xyxy[3] + padding)

    padding_left = x - new_x1
    padding_top = y - new_y1

    new_x1 = max(0, new_x1)
    new_y1 = max(0, new_y1)
    new_x2 = min(image_width, new_x2)
    new_y2 = min(image_height, new_y2)

    new_image = new_image[new_y1:new_y2, new_x1:new_x2]

    new_prompt_bbox_list: list[float] = [
        padding_left,
        padding_top,
        padding_left + w,
        padding_top + h
    ]

    if model is None:
        if not sam_is_loaded():
            sam_load()

        global model_sam

        model = model_sam

    results = model.predict(
        source=new_image,
        bboxes=new_prompt_bbox_list,
    )

    for result in results:
        logger.info(f"Detected {len(result.masks)} masks(boxes).")

        xy_xy_list = result.boxes.cpu().xyxy.numpy().tolist()

        for i, xy_xy in enumerate(xy_xy_list):
            predict_x1, predict_y1, predict_x2, predict_y2 = xy_xy
            predict_x, predict_y, predict_w, predict_h = (
                predict_x1, predict_y1,
                predict_x2 - predict_x1,
                predict_y2 - predict_y1
            )

            original_x1 = predict_x + new_x1
            original_y1 = predict_y + new_y1
            original_x2 = original_x1 + predict_w
            original_y2 = original_y1 + predict_h

            box: list[float] = [
                original_x1, original_y1,
                original_x2, original_y2
            ]

            iou = calculate_iou(prompt_bbox_tuple, box)
            logger.info(f"[{i}] IOU: {iou}")

            if iou > iou_threshold:
                result_list.append(box)
            else:
                logger.info(f"[{i}] IOU({iou}) is too low(<{iou_threshold}), skip.")

    return result_list


if __name__ == "__main__":
    # Print Model List
    model_list = get_sam_model_list()
    for model_name in model_list:
        model_type = get_sam_model_by_name(model_name)
        print(model_type.value)
