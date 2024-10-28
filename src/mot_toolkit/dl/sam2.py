from ultralytics import SAM

from mot_toolkit.dl.utils.value_calc import calculate_iou
from mot_toolkit.utils.logs import get_logger

model_sam: SAM | None = None

logger = get_logger()


def sam_is_loaded() -> bool:
    global model_sam

    return model_sam is not None


def sam_load():
    global model_sam

    if model_sam is None:
        model_sam = SAM("sam2.1_b.pt")


def sam_predict_xyxy(
        image_path,
        bbox_xyxy: list[float],
) -> list[list[float]]:
    result_list: list[list[float]] = []

    prompt_bbox_tuple = (bbox_xyxy[0], bbox_xyxy[1], bbox_xyxy[2], bbox_xyxy[3])

    if not sam_is_loaded():
        sam_load()

    global model_sam

    results = model_sam.predict(
        source=image_path,
        bboxes=bbox_xyxy,
    )

    for result in results:
        logger.info(f"Detected {len(result.masks)} masks(boxes).")

        xy_xy_list = result.boxes.cpu().xyxy.numpy().tolist()

        for i, xy_xy in enumerate(xy_xy_list):
            box: list[float] = [xy_xy[0], xy_xy[1], xy_xy[2], xy_xy[3]]

            iou = calculate_iou(prompt_bbox_tuple, box)
            logger.info(f"[{i}] IOU: {iou}")

            if iou > 0.5:
                result_list.append(box)

    return result_list
