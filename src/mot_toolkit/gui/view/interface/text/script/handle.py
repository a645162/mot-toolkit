import json
import os
import random
import base64
from typing import List, Dict, Any, Tuple, Optional
from tqdm import tqdm  # 导入进度条库

import cv2
import numpy as np

# 导入 OpenAIImageAnalyzer
try:
    from mot_toolkit.gui.view.interface.text.core.openai.openai_api import (
        OpenAIImageAnalyzer,
    )
except ImportError:
    from ..core.openai.openai_api import OpenAIImageAnalyzer

from mot_toolkit.datatype.xanylabeling import (
    XAnyLabelingAnnotation,
    XAnyLabelingAnnotationDirectory,
    XAnyLabelingRect,
)
from mot_toolkit.utils.logs import get_logger

logger = get_logger()

# 默认参数
DEFAULT_FRAME_SAMPLE_COUNT = 20  # 默认的外观采样帧数
DEFAULT_MOTION_LENGTH = 15  # 默认的运动分析帧长度
DEFAULT_GRID_ROWS = 4  # 图像网格默认行数
DEFAULT_GRID_COLS = 5  # 图像网格默认列数

# 整体工作流程:
# 1. 加载标注目录和标注文件
# 2. 为每个标注文件中的边界框生成描述:
#    a. 获取位置描述（基于边界框在画面中的位置）
#    b. 获取运动描述（基于多帧中目标的移动轨迹）
#    c. 获取外观描述（使用OpenAI视觉模型分析目标的外观）
# 3. 将描述保存回标注文件
# 4. 单线程处理以避免API并发问题


def encode_image_to_base64(image: np.ndarray) -> str:
    """
    将 OpenCV 图像编码为 Base64 字符串

    Args:
        image: OpenCV 格式的图像 (numpy.ndarray)

    Returns:
        base64编码后的图像字符串
    """
    _, buffer = cv2.imencode(".jpg", image)
    return base64.b64encode(buffer).decode("utf-8")


def get_image_crop(
    annotation_obj: XAnyLabelingAnnotation, rect_obj: XAnyLabelingRect
) -> Optional[np.ndarray]:
    """
    从标注对象中裁剪目标区域

    Args:
        annotation_obj: 标注对象，包含图像路径
        rect_obj: 矩形标注对象，包含边界框坐标

    Returns:
        裁剪后的图像区域，如果失败则返回 None

    处理流程:
    1. 读取原始图像
    2. 验证边界框坐标有效性
    3. 裁剪并返回目标区域
    """
    try:
        # 读取原始图像
        img = cv2.imread(annotation_obj.pic_path)
        if img is None:
            logger.error(f"无法读取图像: {annotation_obj.pic_path}")
            return None

        # 获取边界框坐标并转换为整数
        x1, y1, x2, y2 = (
            int(rect_obj.x1),
            int(rect_obj.y1),
            int(rect_obj.x2),
            int(rect_obj.y2),
        )

        # 确保坐标在图像范围内
        height, width = img.shape[:2]
        x1 = max(0, min(x1, width - 1))
        y1 = max(0, min(y1, height - 1))
        x2 = max(0, min(x2, width - 1))
        y2 = max(0, min(y2, height - 1))

        # 确保有效的边界框（宽度和高度都必须大于0）
        if x2 <= x1 or y2 <= y1:
            logger.error(f"无效的边界框: {x1},{y1},{x2},{y2}")
            return None

        # 裁剪并返回目标区域
        return img[y1:y2, x1:x2]
    except Exception as e:
        logger.error(f"裁剪图像时出错: {str(e)}")
        return None


def resize_to_target_size(images: List[np.ndarray]) -> List[np.ndarray]:
    """
    将所有图像调整为最大尺寸，确保统一大小

    Args:
        images: 图像列表

    Returns:
        调整大小后的图像列表

    注意:
        此函数将所有图像调整为列表中最大图像的尺寸，以便于后续排列成网格
    """
    if not images:
        return []

    # 找到最大宽度和高度
    max_height = max(img.shape[0] for img in images)
    max_width = max(img.shape[1] for img in images)

    # 调整所有图像尺寸
    resized_images = []
    for img in images:
        if img.shape[:2] == (max_height, max_width):
            resized_images.append(img)
        else:
            resized_img = cv2.resize(img, (max_width, max_height))
            resized_images.append(resized_img)

    return resized_images


def combine_images_grid(
    images: List[np.ndarray], rows: int, cols: int
) -> Optional[np.ndarray]:
    """
    将多个图像按网格拼接成一张图像

    Args:
        images: 要拼接的图像列表
        rows: 网格行数
        cols: 网格列数

    Returns:
        拼接后的网格图像，失败时返回None

    处理流程:
    1. 确保图像数量不超过网格容量
    2. 必要时通过随机挑选已有图像填补空缺
    3. 计算拼接后的图像尺寸
    4. 创建空白画布并填充图像
    """
    if not images:
        return None

    # 确保图像数量不超过网格容量
    n_images = min(len(images), rows * cols)
    images = images[:n_images]

    # 如果图像不够填满网格，随机挑选已有图像进行填充
    if n_images < rows * cols:
        # 计算需要填充的数量
        fill_count = rows * cols - n_images
        # 从已有图像中随机选择进行填充
        fill_images = [
            images[random.randint(0, n_images - 1)] for _ in range(fill_count)
        ]
        images.extend(fill_images)

    # 计算拼接后的图像大小
    img_height, img_width = images[0].shape[:2]
    grid_height = img_height * rows
    grid_width = img_width * cols

    # 创建空白画布
    grid_img = np.zeros((grid_height, grid_width, 3), dtype=np.uint8)

    # 填充图像
    for i, img in enumerate(images):
        row = i // cols
        col = i % cols
        y_start = row * img_height
        x_start = col * img_width
        grid_img[y_start : y_start + img_height, x_start : x_start + img_width] = img

    return grid_img


def analyze_frame_appearance(
    frame_image: np.ndarray,
    global_appearance: str,
    analyzer: OpenAIImageAnalyzer,
    class_name: str = "",
) -> str:
    """
    分析单帧图像中目标的外观，并与全局外观进行比较

    Args:
        frame_image: 单帧中目标的裁剪图像
        global_appearance: 预先获取的全局外观描述
        analyzer: OpenAIImageAnalyzer 实例
        class_name: 目标的类别名称

    Returns:
        当前帧外观的分析描述

    处理流程:
    1. 构建提示词，包含全局外观描述作为参考
    2. 要求分析当前帧中的目标外观，并与全局外观比较
    3. 调用 OpenAIImageAnalyzer 获取分析结果
    """
    try:
        class_info = f"这个目标的类别是: {class_name}。" if class_name else ""

        prompt = (
            f"这是之前我们分析的同一个目标的一个特定时刻的图像。以下是该目标的整体外观参考描述:\n\n"
            f"{global_appearance}\n\n"
            f"{class_info}"
            f"请分析这个具体时刻的图像中，目标的外观是否与参考描述一致，以及有哪些特殊或不同的地方。"
            f"如果看不清或有遮挡，请指出。如果完全符合参考描述，请确认并简要总结关键特征。"
        )

        response = analyzer.ask_question_about_image(frame_image, prompt)
        return response if response else "无法分析当前帧的外观"
    except Exception as e:
        logger.error(f"分析单帧外观时出错: {str(e)}")
        return "分析单帧外观失败"


def combine_appearance_descriptions(
    frame_descriptions: List[str], global_appearance: str, analyzer: OpenAIImageAnalyzer
) -> str:
    """
    综合多个帧的外观描述和全局外观，生成最终的目标外观描述

    Args:
        frame_descriptions: 各帧的外观描述列表
        global_appearance: 全局外观描述
        analyzer: OpenAIImageAnalyzer 实例

    Returns:
        综合后的外观描述

    处理流程:
    1. 构建提示词，包含全局外观和所有单帧分析
    2. 要求综合分析，提取关键特征和变化情况
    3. 调用 OpenAIImageAnalyzer 获取综合描述
    """
    if not frame_descriptions:
        return global_appearance

    try:
        # 构建包含所有信息的提示词
        prompt = (
            f"我有一个目标的全局外观描述和多个具体时刻的外观分析。请综合这些信息，"
            f"生成一个完整、准确的外观描述，既包含稳定特征，也反映外观可能的变化。\n\n"
            f"全局外观描述:\n{global_appearance}\n\n"
            f"具体时刻的分析 ({len(frame_descriptions)} 个):\n"
        )

        # 添加各帧的分析结果
        for i, desc in enumerate(frame_descriptions, 1):
            prompt += f"时刻 {i}:\n{desc}\n\n"

        prompt += "请综合以上信息，提供最终的外观描述，只要精炼的表述，不要额外的内容:"

        # 使用文本模式调用API
        response = analyzer.ask_question_about_image(None, prompt)
        logger.info("已综合多帧分析，生成最终外观描述")

        return response if response else "无法生成综合外观描述"
    except Exception as e:
        logger.error(f"综合外观描述时出错: {str(e)}")
        return global_appearance  # 如果失败，返回全局描述


def get_visual_description_batch(
    images: List[np.ndarray], analyzer: OpenAIImageAnalyzer
) -> str:
    """
    使用 OpenAIImageAnalyzer 对一批图像生成目标外观描述

    Args:
        images: 要分析的图像列表
        analyzer: OpenAIImageAnalyzer 实例用于图像分析

    Returns:
        生成的外观描述文本

    处理流程:
    1. 将图像组合为网格
    2. 构建提示词，询问目标外观特征
    3. 调用 OpenAIImageAnalyzer 进行分析
    4. 返回分析结果
    """
    if not images:
        return "没有提供图像"
    try:
        # 将图像作为网格组合在一起
        grid_image = combine_images_grid(images, DEFAULT_GRID_ROWS, DEFAULT_GRID_COLS)
        if grid_image is None:
            return "无法组合图像"

        # 使用 OpenAIImageAnalyzer 分析图像
        prompt = f"这些是同一个目标的 {len(images)} 个不同时刻的图像。请详细描述这个目标的外观特征，例如颜色、形状、外观特征等。"
        response = analyzer.ask_question_about_image(grid_image, prompt)

        logger.info("已生成批量视觉描述")
        return response if response else "模型未能生成有效描述"
    except Exception as e:
        logger.error(f"生成批量视觉描述时出错: {str(e)}")
        return "无法生成外观描述"


def summarize_descriptions(
    descriptions: List[str], analyzer: OpenAIImageAnalyzer
) -> str:
    """
    使用 OpenAIImageAnalyzer 总结多个描述中出现频率最高的特征

    Args:
        descriptions: 多个描述文本的列表
        analyzer: OpenAIImageAnalyzer 实例用于文本分析

    Returns:
        总结后的描述文本

    处理流程:
    1. 构建综合提示词，包含所有描述
    2. 要求模型总结共同特征
    3. 返回总结结果

    注意:
        此函数使用 OpenAIImageAnalyzer 的纯文本查询能力（没有图像输入）
    """
    try:
        if not descriptions:
            return ""

        # 构建提示词，包含所有描述
        prompt = "以下是关于同一个目标的多个外观描述，请你仔细阅读这些描述，并总结出其中反复提及、出现频率最高的共同视觉特征。\n\n"
        for i, desc in enumerate(descriptions, 1):
            prompt += f'描述{i}: "{desc}"\n\n'
        prompt += "要求：\n"
        prompt += " 请直接输出目标的特征，不要提及如“所有描述”，“可以总结出以下共同特征”等指令回答。\n"
        prompt += " 如果目标外观上有什么文本，必须大部分都有这个描述，也就是只能有1个没有提到文本，否则就认为他没有文本"
        prompt += " 不需要总结意义（如“这些颜色特征有助于船只的识别和导航”）\n"
        prompt += " “规则排列的窗户和舱口：这些描述中提到船只的窗户和舱口排列整齐，是其设计的显著特征”你只需要回答“船只的窗户和舱口排列整齐”即可!\n"
        prompt += " “稳定和坚固的结构：船体的设计和结构表明其具有稳定的航行能力，适合在水面上行驶”这种废话就别说了，人家都航行在水上了，不用你介绍！"
        prompt += " 也就是你只需要回答，这个船，比如有多层甲板，然后颜色是什么，有没有开灯，不需要分点，一句话直接简练概括所有特征！尽可能简练，不要有多余描述与分析！"
        prompt += "\n\n你的输出必须是一句话，简体中文，只描述他的就行了！不要带任何回答问题样式的其他内容！\n"
        prompt += "\n请总结共同特征（只输出特征）："

        # 使用 OpenAIImageAnalyzer 的纯文本查询能力（传入None作为图像）
        response = analyzer.ask_question_about_image(None, prompt)

        logger.info("已总结多个描述的共同特征")
        return response if response else "模型未能生成有效总结"
    except Exception as e:
        logger.error(f"总结描述时出错: {str(e)}")
        return "无法总结特征"


def get_position_description(
    rect_obj: XAnyLabelingRect, img_width: int, img_height: int
) -> str:
    """
    生成目标在画面中的位置描述

    Args:
        rect_obj: 矩形标注对象
        img_width: 图像宽度
        img_height: 图像高度

    Returns:
        描述目标位置的字符串，例如 "画面左上区域"

    工作原理:
    1. 计算边界框的中心点
    2. 将图像划分为3×3=9个区域
    3. 判断中心点位于哪个区域并生成描述
    """
    # 计算中心点
    center_x = (rect_obj.x1 + rect_obj.x2) / 2
    center_y = (rect_obj.x1 + rect_obj.x2) / 2

    # 将图像划分为9个区域
    width_third = img_width / 3
    height_third = img_height / 3

    # 确定水平位置
    if center_x < width_third:
        h_pos = "左"
    elif center_x < 2 * width_third:
        h_pos = "中"
    else:
        h_pos = "右"

    # 确定垂直位置
    if center_y < height_third:
        v_pos = "上"
    elif center_y < 2 * height_third:
        v_pos = "中"
    else:
        v_pos = "下"

    # 如果是中心则特殊处理
    if h_pos == "中" and v_pos == "中":
        return "画面中心区域"

    # 返回位置描述
    return f"画面{v_pos}{h_pos}区域"


def get_motion_description(
    annotation_directory: XAnyLabelingAnnotationDirectory,
    current_index: int,
    object_label: str,
    length: int,
) -> str:
    """
    分析目标的运动描述

    Args:
        annotation_directory: 标注目录对象
        current_index: 当前帧索引
        object_label: 目标标签
        length: 分析的帧数范围

    Returns:
        描述目标运动的字符串，例如 "向左移动" 或 "基本静止"

    处理流程:
    1. 获取前后一定范围内的帧
    2. 收集目标在这些帧中的中心点位置
    3. 分析中心点位置变化，判断运动方向
    4. 生成运动描述
    """
    try:
        # 获取当前帧前后的帧
        start_idx = max(0, current_index - length // 2)
        end_idx = min(
            len(annotation_directory.annotation_file_list) - 1,
            current_index + length // 2,
        )

        # 收集目标轨迹点
        trajectory = []
        for i in range(start_idx, end_idx + 1):
            anno_obj = annotation_directory.annotation_file_list[i]
            for rect in anno_obj.rect_annotation_list:
                if rect.label == object_label:
                    center_x = (rect.x1 + rect.x2) / 2
                    center_y = (rect.x1 + rect.x2) / 2
                    trajectory.append((i, center_x, center_y))
                    break

        # 如果轨迹点少于2个，无法判断运动
        if len(trajectory) < 2:
            return "静止或无法确定运动状态"

        # 计算总体运动趋势
        first_point = trajectory[0]
        last_point = trajectory[-1]
        dx = last_point[1] - first_point[1]  # x方向位移
        dy = last_point[2] - first_point[2]  # y方向位移

        # 判断主要运动方向（水平或垂直）
        directions = []
        if abs(dx) > abs(dy):  # 水平运动为主
            if dx > 0:
                directions.append("向右")
            else:
                directions.append("向左")
        else:  # 垂直运动为主
            if dy > 0:
                directions.append("向下")
            else:
                directions.append("向上")

        # 判断是否有次要运动方向
        # 当位移超过阈值时，即便不是主方向，也认为有显著移动
        if abs(dx) > 10 and abs(dy) > 10:  # 阈值可调整
            if dx > 0 and "向右" not in directions:
                directions.append("向右")
            elif dx < 0 and "向左" not in directions:
                directions.append("向左")

            if dy > 0 and "向下" not in directions:
                directions.append("向下")
            elif dy < 0 and "向上" not in directions:
                directions.append("向上")

        # 如果没有检测到明显方向，认为是静止
        if not directions:
            return "基本静止"

        # 组合多个方向
        return "、".join(directions) + "移动"

    except Exception as e:
        logger.error(f"分析运动描述时出错: {str(e)}")
        return "无法分析运动"


def generate_object_description(
    annotation_directory: XAnyLabelingAnnotationDirectory,
    current_index: int,
    rect_obj: XAnyLabelingRect,
    analyzer: OpenAIImageAnalyzer,
    sample_count: int = DEFAULT_FRAME_SAMPLE_COUNT,
    motion_length: int = DEFAULT_MOTION_LENGTH,
    grid_rows: int = DEFAULT_GRID_ROWS,
    grid_cols: int = DEFAULT_GRID_COLS,
    class_map: dict = None,
    appearance_repeat: int = 1,  # 新增参数，表示采样n次
) -> Dict[str, Any]:
    """
    为目标生成完整描述信息，使用提供的 OpenAIImageAnalyzer 实例

    Args:
        annotation_directory: 标注目录对象
        current_index: 当前帧索引
        rect_obj: 矩形标注对象
        analyzer: OpenAIImageAnalyzer 实例
        sample_count: 外观采样帧数
        motion_length: 运动分析帧长度
        grid_rows: 图像网格行数
        grid_cols: 图像网格列数
        class_map: 类别ID到类别名称的映射字典
        appearance_repeat: 连续采样appearance_repeat次，每次sample_count帧

    Returns:
        包含 appearance、position 和 motion 三个字段的描述信息字典

    处理流程:
    1. 生成位置描述 -> position
    2. 生成运动描述 -> motion
    3. 生成外观描述
       a. 连续采样appearance_repeat次，每次sample_count帧，分别生成appearance描述
       b. 综合所有appearance描述，生成最终appearance
    """
    description_data = {
        "appearance": "",  # 外观描述
        "position": "",  # 位置描述
        "motion": "",  # 运动描述
        "class_id": str(rect_obj.label),  # 原始类别ID
        "class_name": "",  # 类别名称
    }

    # 获取类别名称（如果有类别映射）
    class_id = rect_obj.group_id
    class_name = ""
    if class_map and class_id in class_map:
        class_name = class_map[class_id]
        # Only for debug
        print(f"目标类别ID {class_id} 映射到类别名称: {class_name}")
        description_data["class_name"] = class_name
        logger.info(f"目标类别ID {class_id} 映射到类别名称: {class_name}")

    try:
        # 当前标注对象
        current_annotation = annotation_directory.annotation_file_list[current_index]
        img_width, img_height = (
            current_annotation.image_width,
            current_annotation.image_height,
        )

        # 1. 生成位置描述
        description_data["position"] = get_position_description(
            rect_obj, img_width, img_height
        )

        # 2. 生成运动描述
        description_data["motion"] = get_motion_description(
            annotation_directory, current_index, rect_obj.label, motion_length
        )

        # 3. 生成外观描述（连续采样appearance_repeat次，每次sample_count帧）
        # 从所有帧中获取该目标的所有可用帧
        available_frames = []
        for idx, anno_obj in enumerate(annotation_directory.annotation_file_list):
            for rect in anno_obj.rect_annotation_list:
                if rect.label == rect_obj.label:
                    crop = get_image_crop(anno_obj, rect)
                    if crop is not None:
                        available_frames.append((idx, crop))
                    break

        if not available_frames:
            logger.warning(f"未找到目标 {rect_obj.label} 的有效帧")
            return description_data

        # 调整所有帧的大小使其一致
        all_crops = [crop for _, crop in available_frames]
        resized_crops = resize_to_target_size(all_crops)

        if not resized_crops:
            logger.warning("无法调整图像大小")
            return description_data

        frame_count = len(resized_crops)
        appearance_descriptions = []

        # 连续采样appearance_repeat次，每次sample_count帧
        for repeat_idx in range(appearance_repeat):
            if frame_count <= sample_count:
                selected_frames = resized_crops
            else:
                # 均匀采样
                step = frame_count // sample_count
                selected_indices = [i * step + repeat_idx for i in range(sample_count)]
                # 保证索引不越界
                selected_indices = [
                    min(idx, frame_count - 1) for idx in selected_indices
                ]
                # 去重
                selected_indices = list(dict.fromkeys(selected_indices))
                # 如果采样数不足，补齐
                while len(selected_indices) < sample_count:
                    selected_indices.append(frame_count - 1)
                selected_frames = [resized_crops[i] for i in selected_indices]

            # 组合为网格
            grid_image = combine_images_grid(selected_frames, grid_rows, grid_cols)
            if grid_image is None:
                appearance_descriptions.append("无法组合图像")
                continue

            # 构建提示词
            target_type_info = ""
            if class_name:
                target_type_info = (
                    f"\n这个目标的类别是: {class_name}。请考虑这个类别的典型特征。"
                )
            elif class_id:
                target_type_info = f"\n这个目标的类别ID是: {class_id}。"

            prompt = (
                f"这些是同一个目标的 {len(selected_frames)} 个不同时刻的图像。"
                f"请详细描述这个目标的整体外观特征，包括但不限于："
                f"1. 外形特征（主要都是水上目标）\n"
                f"2. 主要颜色和颜色分布\n"
                f"3. 特征细节（如标志、独特形状、是否有窗户、有没有人）\n"
                f"4. 环境细节（如是否存在水波、水面反射）"
                f"{target_type_info}\n"
                f"请提供详尽准确的描述，这将用作参考标准。\n"
                f"只需要输出对目标的外观的描述，不要输出其他的乱七八糟的。"
            )

            response = analyzer.ask_question_about_image(grid_image, prompt)
            logger.info(f"第{repeat_idx+1}次appearance采样完成")
            appearance_descriptions.append(
                response if response else "模型未能生成有效的外观描述"
            )

        # 3.4 综合所有appearance描述
        if appearance_descriptions:
            logger.info("正在综合多次appearance采样的描述...")
            final_appearance = summarize_descriptions(appearance_descriptions, analyzer)
        else:
            final_appearance = ""

        # 添加类别信息到描述中
        if class_name:
            final_appearance = f"【{class_name}】 {final_appearance}"

        description_data["appearance"] = final_appearance

        return description_data

    except Exception as e:
        logger.error(f"生成描述信息时出错: {str(e)}")
        description_data["appearance"] = ""
        return description_data


def process_annotation_task(task_args):
    """
    处理单个任务：为特定的标注文件中的边界框生成描述

    这是传递给单线程的worker函数，处理单个标注文件的所有边界框

    Args:
        task_args: 包含以下元素的元组:
            - annotation_obj: 标注对象
            - annotation_directory: 标注目录
            - idx: 文件索引
            - sample_count: 外观采样帧数
            - motion_length: 运动分析帧长度
            - analyzer: OpenAIImageAnalyzer实例
            - class_map: 类别ID到类别名称的映射字典

    Returns:
        包含修改后标注对象和是否已修改的元组: (annotation_obj, modified)

    处理流程:
    1. 遍历标注文件中的所有边界框
    2. 为每个边界框生成描述信息
    3. 将描述信息保存到边界框的描述字段
    """
    (
        annotation_obj,
        annotation_directory,
        idx,
        sample_count,
        motion_length,
        analyzer,
        class_map,
        appearance_repeat,
    ) = task_args
    modified = False

    for rect_obj in annotation_obj.rect_annotation_list:
        # 生成描述信息
        description_data = generate_object_description(
            annotation_directory,
            idx,
            rect_obj,
            analyzer,
            sample_count,
            motion_length,
            class_map=class_map,
            appearance_repeat=appearance_repeat,
        )

        # 将描述信息序列化为JSON字符串
        description_json = json.dumps(description_data, ensure_ascii=False)

        # 更新边界框的描述字段
        if rect_obj.description != description_json:
            rect_obj.description = description_json
            modified = True

    # 如果有修改，标记待保存
    if modified:
        logger.info(f"更新了文件描述信息: {annotation_obj.file_path}")
        annotation_obj.modifying()

    # For debug
    annotation_obj.save()

    return annotation_obj, modified


def update_bbox_descriptions(
    dataset_dir_path: str,
    sample_count: int = DEFAULT_FRAME_SAMPLE_COUNT,
    motion_length: int = DEFAULT_MOTION_LENGTH,
    analyzers: List[OpenAIImageAnalyzer] = None,
    class_map: dict = None,
    appearance_repeat=1,
) -> bool:
    """
    更新数据集中所有边界框的描述信息，使用单线程处理每个标注文件

    OpenAI API 不支持多并发调用，因此使用单线程处理

    主函数，协调整个描述生成过程

    Args:
        dataset_dir_path: 数据集目录路径
        sample_count: 外观采样帧数
        motion_length: 运动分析帧长度
        analyzers: OpenAIImageAnalyzer 实例列表，一般只提供一个实例
        class_map: 类别ID到类别名称的映射字典

    Returns:
        操作成功返回 True，否则返回 False

    工作流程:
    1. 初始化标注目录并加载标注文件
    2. 检查并准备 OpenAIImageAnalyzer 实例
    3. 顺序处理每个标注文件
    4. 保存修改后的标注文件
    """
    try:
        # 初始化标注目录
        annotation_directory = XAnyLabelingAnnotationDirectory()
        annotation_directory.dir_path = dataset_dir_path
        annotation_directory.walk_dir(recursive=False)
        annotation_directory.sort_path(group_directory=True)
        annotation_directory.load_json_files()

        if len(annotation_directory.annotation_file_list) == 0:
            logger.error(f"目录中没有找到标注文件: {dataset_dir_path}")
            return False

        # 更新标签列表
        annotation_directory.update_label_list()

        # 如果没有提供 analyzers，创建一个默认的 analyzer
        if not analyzers or len(analyzers) == 0:
            # 检查环境变量中是否有 OpenAI API 密钥
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                logger.error(
                    "没有提供 OpenAIImageAnalyzer 实例，且环境变量中没有 OPENAI_API_KEY"
                )
                return False

            analyzers = [OpenAIImageAnalyzer(api_key=api_key, model="gpt-4o")]
            logger.info("使用环境变量中的API密钥创建了一个默认的OpenAIImageAnalyzer")

        # 记录类别ID到名称的映射
        if class_map:
            logger.info(f"使用类别映射: {class_map}")
        else:
            logger.info(f"未提供类别映射字典")
            class_map = {}

        # 将注释文件分成大致相等的几份，每个 analyzer 处理一份
        n_analyzers = len(analyzers)
        n_files = len(annotation_directory.annotation_file_list)
        logger.info(f"使用 {n_analyzers} 个分析器处理 {n_files} 个标注文件")

        # 准备任务列表
        tasks = []
        for idx, annotation_obj in enumerate(annotation_directory.annotation_file_list):
            # 计算使用哪个 analyzer（简单轮询分配）
            analyzer_idx = idx % n_analyzers
            tasks.append(
                (
                    annotation_obj,
                    annotation_directory,
                    idx,
                    sample_count,
                    motion_length,
                    analyzers[analyzer_idx],
                    class_map,
                    appearance_repeat,
                )
            )

        # 存储修改过的标注对象
        modified_annotations = []

        # 顺序处理每个任务，使用tqdm显示进度条
        sequence_name = os.path.basename(dataset_dir_path)
        logger.info(f"开始处理序列: {sequence_name}, 共 {len(tasks)} 个标注文件")

        # 使用tqdm创建进度条
        with tqdm(
            total=len(tasks),
            desc=f"处理序列 '{sequence_name}'",
            unit="帧",
            ncols=100,
            leave=True,
        ) as pbar:
            for task in tasks:
                try:
                    annotation_obj, modified = process_annotation_task(task)
                    if modified:
                        modified_annotations.append(annotation_obj)
                    pbar.update(1)  # 更新进度条
                except Exception as e:
                    logger.error(f"处理标注文件时出错: {e}")
                    pbar.update(1)  # 即使出错也要更新进度条

        # 保存所有被修改过的标注文件
        logger.info(f"开始保存 {len(modified_annotations)} 个已修改的标注文件")
        for annotation_obj in modified_annotations:
            annotation_obj.save_json()

        logger.info(
            f"成功处理了 {len(annotation_directory.annotation_file_list)} 个标注文件，其中 {len(modified_annotations)} 个被修改"
        )
        return True

    except Exception as e:
        logger.error(f"更新边界框描述时出错: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 测试用例
    test_dir = "/path/to/test/dataset"

    # 创建多个 analyzer 实例
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        # 创建两个相同配置的analyzer实例用于测试
        analyzers = [
            OpenAIImageAnalyzer(api_key=api_key, model="gpt-4o"),
            OpenAIImageAnalyzer(api_key=api_key, model="gpt-4o"),
        ]
        print(f"创建了 {len(analyzers)} 个 OpenAIImageAnalyzer 实例")
        print(f"开始处理测试目录: {test_dir}")
        update_bbox_descriptions(test_dir, analyzers=analyzers)
    else:
        print("请设置 OPENAI_API_KEY 环境变量")
