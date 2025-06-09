import os
from typing import List

import cv2
import tqdm

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list
from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotationDirectory
from mot_toolkit.vis.scheme.genshin.sigewinne_colors import SIGEWINNEColorScheme
from mot_toolkit.utils.image_renderer import RenderConfig


def bgr2rgb(color: tuple) -> tuple:
    return color[2], color[1], color[0]


def generate_color_dict(annotation_directory: XAnyLabelingAnnotationDirectory) -> dict:
    """生成目标ID到颜色的映射字典"""
    color_scheme = SIGEWINNEColorScheme()
    colors = color_scheme.bgr_colors()

    # 收集所有唯一的目标ID
    all_ids = set()
    for annotation_file in annotation_directory.annotation_file_list:
        for rect_annotation in annotation_file.rect_annotation_list:
            all_ids.add(rect_annotation.label)

    # 为每个ID分配颜色
    color_dict = {}
    for i, obj_id in enumerate(sorted(all_ids)):
        color_dict[obj_id] = colors[i % len(colors)]

    return color_dict


def process_sequence(
    sequence_dir_path: str,
    output_video_path: str,
    # 视频设置
    fps: float = 30.0,
    max_width: int = 1920,
    max_height: int = 1080,
    # 显示设置
    show_frame_text: bool = True,
    show_frame_progress: bool = True,
    show_frame_object_count: bool = True,
    # 框设置
    show_box: bool = True,
    different_color: bool = True,
    with_text: bool = False,
    center_point_trajectory: bool = True,
    thickness: int = 2,
    # 颜色设置
    selected_color: tuple = (0, 255, 255),  # BGR格式
    unselected_color: tuple = (0, 255, 0),  # BGR格式
    text_color: tuple = (0, 0, 255),  # BGR格式
    # 过滤设置
    selection_label: str = "",
    only_selection_box: bool = False,
    only_near_selection: bool = False,
    crop_padding: int = 50,
):
    """处理单个序列，生成带GT框的视频"""

    if not os.path.isdir(sequence_dir_path):
        print(f"序列目录不存在: {sequence_dir_path}")
        return False

    # 加载标注文件
    annotation_directory = XAnyLabelingAnnotationDirectory()
    annotation_directory.dir_path = sequence_dir_path
    annotation_directory.walk_dir(recursive=False)
    annotation_directory.sort_path(group_directory=True)

    if len(annotation_directory.file_list) == 0:
        print(f"序列 {sequence_dir_path} 没有标注文件!")
        return False

    annotation_directory.load_json_files()

    # 获取图像尺寸
    first_file_obj = annotation_directory.annotation_file_list[0]
    image_width, image_height = first_file_obj.image_width, first_file_obj.image_height

    # 计算缩放比例
    scale_ratio = 1
    if max_width > 0 or max_height > 0:
        width_ratio = max_width / image_width if max_width > 0 else 1
        height_ratio = max_height / image_height if max_height > 0 else 1
        scale_ratio = min(width_ratio, height_ratio)

    # 生成颜色字典
    color_dict = generate_color_dict(annotation_directory) if different_color else None

    # 创建视频写入器
    output_dir = os.path.dirname(output_video_path)
    os.makedirs(output_dir, exist_ok=True)

    if output_video_path.endswith(".mp4"):
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    else:
        fourcc = cv2.VideoWriter_fourcc(*"XVID")

    final_width = int(image_width * scale_ratio)
    final_height = int(image_height * scale_ratio)
    video_out = cv2.VideoWriter(
        output_video_path, fourcc, fps, (final_width, final_height)
    )

    if not video_out.isOpened():
        print(f"无法创建视频文件: {output_video_path}")
        return False

    # 用于绘制轨迹的中心点历史
    center_point_trajectory_dict: dict = {}

    file_count = len(annotation_directory.annotation_file_list)

    print(f"开始处理序列: {os.path.basename(sequence_dir_path)}, 共{file_count}帧")

    for i, annotation in enumerate(
        tqdm.tqdm(annotation_directory.annotation_file_list)
    ):
        frame_index = i + 1

        if show_box:
            # 创建渲染配置对象
            render_config = RenderConfig(
                with_text=with_text,
                color=unselected_color,
                text_color=text_color,
                thickness=thickness,
                center_point_trajectory=center_point_trajectory_dict,
                draw_trajectory=center_point_trajectory,
                selection_label=selection_label,
                selection_color=selected_color,
                only_selection_box=only_selection_box,
                crop_selection=only_near_selection,
                not_found_return_none=only_near_selection,
                crop_padding=crop_padding,
                color_dict=color_dict,
            )

            # 使用新版接口
            image = annotation.get_cv_mat_with_box(render_config)
        else:
            image = annotation.get_cv_mat()

        if image is None:
            continue

        # 添加帧信息文本
        if show_frame_text:
            text_list: List[str] = []
            if show_frame_progress:
                text_list.append(f"Frame: {frame_index}/{file_count}")
            if show_frame_object_count:
                text_list.append(f"Objects: {annotation.annotation_count}")

            text = " | ".join(text_list)
            cv2.putText(
                image, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
            )

        # 缩放图像
        if scale_ratio != 1:
            image = cv2.resize(image, (final_width, final_height))

        # 写入视频
        video_out.write(image)

    video_out.release()
    print(f"视频已保存到: {output_video_path}")
    return True


def main():
    """主函数"""
    # 配置参数
    base_path = r"/home/konghaomin/Datasets/MaritimeTrackAllData/MT20250319/LabelMe"
    # base_path = r"H:\Datasets\MaritimeTrackAllData\LabelMe"
    # base_path = r"H:\Datasets\SMD\SMD_LabelMe_Fix_20250509"

    # 输出目录设置
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_base_dir = os.path.join(current_dir, "output", "seq_gt")

    # 视频生成设置
    video_settings = {
        "fps": 30.0,
        "max_width": 1920,
        "max_height": 1080,
        # 显示设置
        "show_frame_text": True,
        "show_frame_progress": True,
        "show_frame_object_count": True,
        # 框设置
        "show_box": True,
        "different_color": True,
        "with_text": False,
        "center_point_trajectory": True,
        "thickness": 2,
        # 颜色设置 (BGR格式)
        "selected_color": (0, 255, 255),  # 黄色
        "unselected_color": (0, 255, 0),  # 绿色
        "text_color": (0, 0, 255),  # 红色
        # 过滤设置
        "selection_label": "",
        "only_selection_box": False,
        "only_near_selection": False,
        "crop_padding": 50,
    }

    # 获取所有序列目录
    sequence_dir_list = get_dataset_dir_list(base_path)

    if not sequence_dir_list:
        print(f"在路径 {base_path} 下未找到任何序列目录")
        return

    print(f"找到 {len(sequence_dir_list)} 个序列目录")

    # 处理每个序列
    success_count = 0
    for sequence_dir_path in sequence_dir_list:
        # 获取视频名和序列名
        sequence_name = os.path.basename(sequence_dir_path)
        video_name = os.path.basename(os.path.dirname(sequence_dir_path))

        # 生成输出视频文件名
        output_video_name = f"{video_name}_{sequence_name}.mp4"
        output_video_path = os.path.join(output_base_dir, output_video_name)

        print(f"\n处理序列: {video_name}/{sequence_name}")

        # 处理序列
        if process_sequence(sequence_dir_path, output_video_path, **video_settings):
            success_count += 1
        else:
            print(f"处理失败: {video_name}/{sequence_name}")

    print(f"\n完成! 成功处理了 {success_count}/{len(sequence_dir_list)} 个序列")
    print(f"输出目录: {output_base_dir}")


if __name__ == "__main__":
    main()
