from typing import Union, Optional, List, Tuple
import cv2
import numpy as np
from PySide6.QtGui import QColor


def _convert_color_to_bgr(color: Union[tuple, QColor]) -> tuple:
    """将颜色转换为BGR格式"""
    if isinstance(color, QColor):
        rgb = color.getRgb()
        return rgb[2], rgb[1], rgb[0]
    return color


def _update_trajectory(
    center_point_trajectory: dict, label: str, center_x: int, center_y: int
) -> None:
    """更新轨迹点"""
    if label != "":
        if label not in center_point_trajectory:
            center_point_trajectory[label] = []
        center_point_trajectory[label].append((center_x, center_y))


def _get_annotation_color(
    label: str,
    default_color: tuple,
    selection_label: str,
    selection_color: tuple,
    color_dict: dict,
) -> Tuple[tuple, bool]:
    """获取标注框颜色"""
    current_color = default_color
    found_color = False

    # 检查是否有自定义颜色
    if label in color_dict:
        found_color_obj: QColor = color_dict[label]
        current_color = _convert_color_to_bgr(found_color_obj)
        found_color = True

    # 检查是否是选中的标签
    if len(selection_label) > 0 and label == selection_label:
        if not found_color:
            current_color = selection_color

    return current_color, found_color


def _draw_rectangle(
    image: np.ndarray, x1: int, y1: int, x2: int, y2: int, color: tuple, thickness: int
) -> np.ndarray:
    """绘制矩形框"""
    return cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)


def _draw_trajectory_line(
    image: np.ndarray,
    trajectory_points: List[Tuple[int, int]],
    color: tuple,
    thickness: int,
) -> np.ndarray:
    """绘制轨迹线"""
    last_point = None
    for point in trajectory_points:
        center_x, center_y = point
        if last_point is not None:
            image = cv2.line(
                image, last_point, (int(center_x), int(center_y)), color, thickness
            )
        last_point = (int(center_x), int(center_y))
    return image


def _draw_trajectory_points(
    image: np.ndarray, trajectory_points: List[Tuple[int, int]], color: tuple
) -> np.ndarray:
    """绘制轨迹点"""
    for point in trajectory_points:
        center_x, center_y = point
        image = cv2.circle(image, (int(center_x), int(center_y)), 3, color, -1)
    return image


def _draw_trajectory(
    image: np.ndarray,
    center_point_trajectory: dict,
    label: str,
    color: tuple,
    thickness: int,
    trajectory_line_mode: bool,
) -> np.ndarray:
    """绘制轨迹"""
    if label and label in center_point_trajectory and len(center_point_trajectory) > 0:
        trajectory_points = center_point_trajectory[label]
        if trajectory_line_mode:
            image = _draw_trajectory_line(image, trajectory_points, color, thickness)
        else:
            image = _draw_trajectory_points(image, trajectory_points, color)
    return image


def _draw_text_label(
    image: np.ndarray, label: str, x1: int, y1: int, text_color: tuple
) -> np.ndarray:
    """绘制文字标签"""
    if label:
        cv2.putText(
            image, label, (x1, y1 + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2
        )
    return image


def _process_single_annotation(
    image: np.ndarray,
    rect_item,
    center_point_trajectory: dict,
    default_color: tuple,
    text_color: tuple,
    thickness: int,
    selection_label: str,
    selection_color: tuple,
    color_dict: dict,
    draw_trajectory: bool,
    trajectory_line_mode: bool,
    with_text: bool,
    only_selection_box: bool,
) -> Tuple[np.ndarray, Optional[Tuple[int, int, int, int]]]:
    """处理单个标注"""
    x1, y1, x2, y2 = rect_item.get_rect_two_point_tuple_int()
    center_x, center_y = rect_item.center_x, rect_item.center_y
    label = rect_item.label.strip()

    # 更新轨迹
    _update_trajectory(center_point_trajectory, label, center_x, center_y)

    # 获取颜色
    current_color, found_color = _get_annotation_color(
        label, default_color, selection_label, selection_color, color_dict
    )

    # 检查选择逻辑
    selection_rect = None
    if len(selection_label) > 0:
        if rect_item.label == selection_label:
            selection_rect = (x1, y1, x2, y2)
        elif only_selection_box:
            return image, selection_rect

    # 绘制矩形框
    image = _draw_rectangle(image, x1, y1, x2, y2, current_color, thickness)

    # 绘制轨迹
    if draw_trajectory:
        image = _draw_trajectory(
            image,
            center_point_trajectory,
            label,
            current_color,
            thickness,
            trajectory_line_mode,
        )

    # 绘制文字
    if with_text:
        image = _draw_text_label(image, label, x1, y1, text_color)

    return image, selection_rect


def _crop_image(
    image: np.ndarray,
    crop_xyxy: Tuple[int, int, int, int],
    crop_padding: int,
    crop_min_size: int,
) -> np.ndarray:
    """裁剪图像"""
    image_width, image_height = image.shape[1], image.shape[0]
    crop_x1, crop_y1, crop_x2, crop_y2 = crop_xyxy

    # 添加填充
    crop_x1 -= crop_padding
    crop_y1 -= crop_padding
    crop_x2 += crop_padding
    crop_y2 += crop_padding

    # 修正裁剪尺寸
    crop_x1 = max(0, crop_x1)
    crop_y1 = max(0, crop_y1)
    crop_x2 = min(image_width, crop_x2)
    crop_y2 = min(image_height, crop_y2)

    crop_image = image[crop_y1:crop_y2, crop_x1:crop_x2]

    # 调整最小尺寸
    if crop_min_size > 0:
        crop_height, crop_width = crop_image.shape[:2]
        if crop_width < crop_min_size or crop_height < crop_min_size:
            scale_factor = crop_min_size / max(crop_width, crop_height)
            crop_image = cv2.resize(
                crop_image, (0, 0), fx=scale_factor, fy=scale_factor
            )

    return crop_image


def render_image_with_annotations(
    img_np: np.ndarray,
    rect_annotation_list: List,
    with_text: bool = True,
    color: Union[tuple, QColor] = (0, 255, 0),
    text_color: Union[tuple, QColor] = (0, 0, 255),
    thickness: int = 2,
    center_point_trajectory: dict = None,
    draw_trajectory: bool = False,
    trajectory_line_mode: bool = True,
    selection_label: str = "",
    selection_color: Union[tuple, QColor] = (0, 255, 255),
    not_found_return_none: bool = False,
    only_selection_box: bool = False,
    crop_selection: bool = False,
    crop_xyxy: Tuple[int, int, int, int] = (0, 0, 0, 0),
    crop_padding: int = 50,
    crop_min_size: int = 1000,
    color_dict: dict = None,
) -> Optional[np.ndarray]:
    """渲染带有标注框的图像"""
    # 初始化参数
    if center_point_trajectory is None:
        center_point_trajectory = {}
    if color_dict is None:
        color_dict = {}

    if img_np is None:
        return None

    new_image = img_np.copy()

    # 转换颜色格式
    color = _convert_color_to_bgr(color)
    text_color = _convert_color_to_bgr(text_color)
    selection_color = _convert_color_to_bgr(selection_color)

    # 处理所有标注
    found_selection = False
    selection_rect = None

    for rect_item in rect_annotation_list:
        new_image, current_selection = _process_single_annotation(
            new_image,
            rect_item,
            center_point_trajectory,
            color,
            text_color,
            thickness,
            selection_label,
            selection_color,
            color_dict,
            draw_trajectory,
            trajectory_line_mode,
            with_text,
            only_selection_box,
        )

        if current_selection is not None:
            selection_rect = current_selection
            found_selection = True

    # 检查选择结果
    if not_found_return_none and len(selection_label) > 0 and not found_selection:
        return None

    # 处理裁剪
    crop_selection = crop_selection and found_selection

    if not crop_selection and crop_xyxy == (0, 0, 0, 0):
        return new_image

    # 确定裁剪区域
    if crop_selection and selection_rect:
        crop_xyxy = selection_rect

    # 执行裁剪
    return _crop_image(new_image, crop_xyxy, crop_padding, crop_min_size)
