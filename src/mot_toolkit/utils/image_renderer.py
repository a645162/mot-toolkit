from typing import Union, Optional, List, Tuple
import cv2
import numpy as np
from PySide6.QtGui import QColor


class RenderConfig:
    """渲染配置类，封装所有渲染参数"""

    def __init__(
        self,
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
        # 新增矩形填充参数
        fill_rectangle: bool = False,
        fill_alpha: float = 0.1,  # 填充透明度，0.0-1.0
    ):
        self.with_text = with_text
        self.color = color
        self.text_color = text_color
        self.thickness = thickness
        # 修复：确保传递正确的字典引用，而不是创建新的空字典
        self.center_point_trajectory = (
            center_point_trajectory if center_point_trajectory is not None else {}
        )
        self.draw_trajectory = draw_trajectory
        self.trajectory_line_mode = trajectory_line_mode
        self.selection_label = selection_label
        self.selection_color = selection_color
        self.not_found_return_none = not_found_return_none
        self.only_selection_box = only_selection_box
        self.crop_selection = crop_selection
        self.crop_xyxy = crop_xyxy
        self.crop_padding = crop_padding
        self.crop_min_size = crop_min_size
        self.color_dict = color_dict if color_dict is not None else {}
        # 新增属性
        self.fill_rectangle = fill_rectangle
        self.fill_alpha = max(0.0, min(1.0, fill_alpha))  # 确保在有效范围内


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


def _draw_filled_rectangle(
    image: np.ndarray, x1: int, y1: int, x2: int, y2: int, color: tuple, alpha: float
) -> np.ndarray:
    """绘制填充的半透明矩形"""
    if alpha <= 0:
        return image

    # 创建填充层
    overlay = image.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)

    # 混合原图和填充层
    return cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)


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
    # 修复：与原版本保持一致的条件判断
    if (
        len(center_point_trajectory.keys()) > 0
        and label
        and label in center_point_trajectory.keys()
    ):
        trajectory_points = center_point_trajectory[label]
        if trajectory_line_mode:
            image = _draw_trajectory_line(image, trajectory_points, color, thickness)
        else:
            image = _draw_trajectory_points(image, trajectory_points, color)
    return image


def _draw_text_label(
    image: np.ndarray, label: str, x1: int, y1: int, x2: int, y2: int, text_color: tuple
) -> np.ndarray:
    """绘制文字标签（居中显示，无背景）"""
    if label:
        # 计算文本尺寸
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.8
        thickness = 2
        (text_width, text_height), baseline = cv2.getTextSize(
            label, font, font_scale, thickness
        )

        # 计算矩形框中心位置
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        # 计算文本绘制位置（使文本居中）
        text_x = center_x - text_width // 2
        text_y = center_y + text_height // 2

        # 直接绘制文本，不添加背景
        cv2.putText(
            image, label, (text_x, text_y), font, font_scale, text_color, thickness
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
    fill_rectangle: bool,
    fill_alpha: float,
) -> Tuple[np.ndarray, Optional[Tuple[int, int, int, int]], tuple, str]:
    """处理单个标注，返回绘制信息用于后续文本绘制"""
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
            return image, selection_rect, current_color, label

    # 绘制填充矩形（如果启用）
    if fill_rectangle:
        image = _draw_filled_rectangle(image, x1, y1, x2, y2, current_color, fill_alpha)

    # 绘制矩形框
    image = _draw_rectangle(image, x1, y1, x2, y2, current_color, thickness)

    # 绘制轨迹
    if draw_trajectory:
        # Debug Info
        # print("center_point_trajectory", center_point_trajectory)

        image = _draw_trajectory(
            image,
            center_point_trajectory,
            label,
            current_color,
            thickness,
            trajectory_line_mode,
        )

    return image, selection_rect, current_color, label


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


def render_image_with_config(
    img_np: np.ndarray,
    rect_annotation_list: List,
    config: RenderConfig,
) -> Optional[np.ndarray]:
    """使用配置类渲染带有标注框的图像（新接口）"""
    if img_np is None:
        return None

    new_image = img_np.copy()

    # 转换颜色格式
    color = _convert_color_to_bgr(config.color)
    text_color = _convert_color_to_bgr(config.text_color)
    selection_color = _convert_color_to_bgr(config.selection_color)

    # 处理所有标注，收集文本绘制信息
    found_selection = False
    selection_rect = None
    text_draw_info = []  # 存储文本绘制信息

    for rect_item in rect_annotation_list:
        new_image, current_selection, current_color, label = _process_single_annotation(
            new_image,
            rect_item,
            config.center_point_trajectory,
            color,
            text_color,
            config.thickness,
            config.selection_label,
            selection_color,
            config.color_dict,
            config.draw_trajectory,
            config.trajectory_line_mode,
            config.with_text,
            config.only_selection_box,
            config.fill_rectangle,
            config.fill_alpha,
        )

        if current_selection is not None:
            selection_rect = current_selection
            found_selection = True

        # 收集文本绘制信息，留到最后绘制
        if config.with_text and label:
            x1, y1, x2, y2 = rect_item.get_rect_two_point_tuple_int()
            text_draw_info.append((label, x1, y1, x2, y2, text_color))

    # 最后绘制所有文本（确保在最顶层）
    for label, x1, y1, x2, y2, t_color in text_draw_info:
        new_image = _draw_text_label(new_image, label, x1, y1, x2, y2, t_color)

    # 检查选择结果
    if (
        config.not_found_return_none
        and len(config.selection_label) > 0
        and not found_selection
    ):
        return None

    # 处理裁剪
    crop_selection = config.crop_selection and found_selection

    if not crop_selection and config.crop_xyxy == (0, 0, 0, 0):
        return new_image

    # 确定裁剪区域
    crop_xyxy = config.crop_xyxy
    if crop_selection and selection_rect:
        crop_xyxy = selection_rect

    # 执行裁剪
    return _crop_image(new_image, crop_xyxy, config.crop_padding, config.crop_min_size)


# # 旧接口，已重命名为 render_image_with_config
# 未来不再添加任何新的参数
def render_image_with_annotations_legacy(
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
    """渲染带有标注框的图像（旧接口，已重命名，调用新接口）"""
    # 旧接口直接使用默认值！这个函数不再进行修改！
    config = RenderConfig(
        with_text=with_text,
        color=color,
        text_color=text_color,
        thickness=thickness,
        center_point_trajectory=center_point_trajectory,
        draw_trajectory=draw_trajectory,
        trajectory_line_mode=trajectory_line_mode,
        selection_label=selection_label,
        selection_color=selection_color,
        not_found_return_none=not_found_return_none,
        only_selection_box=only_selection_box,
        crop_selection=crop_selection,
        crop_xyxy=crop_xyxy,
        crop_padding=crop_padding,
        crop_min_size=crop_min_size,
        color_dict=color_dict,
    )
    return render_image_with_config(img_np, rect_annotation_list, config)


# 为了向后兼容，保留原函数名作为别名
# render_image_with_annotations = render_image_with_annotations_legacy
