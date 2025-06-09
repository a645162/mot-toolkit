import os
import time
from datetime import datetime, timedelta
from typing import List
from multiprocessing import Pool

import shutil

from mot_toolkit.config.hardware import cpu_count

import cv2
import tqdm

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list
from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotationDirectory
from mot_toolkit.vis.scheme.genshin.sigewinne_colors import SIGEWINNEColorScheme
from mot_toolkit.utils.image_renderer import RenderConfig


# 全局视频设置参数
VIDEO_SETTINGS = {
    # 视频设置
    "fps": 60.0,
    "max_width": 1920,
    "max_height": 1080,
    # 输出设置
    "save_video": False,  # 是否保存视频文件
    "save_frames": True,  # 是否保存每一帧图像
    # 显示设置
    "show_frame_text": True,
    "show_frame_progress": True,
    "show_frame_object_count": True,
    # 框设置
    "show_box": True,
    "different_color": True,
    "with_text": False,
    "center_point_trajectory": True,
    "thickness": 5,
    # 矩形填充设置
    "fill_rectangle": True,  # 是否启用矩形填充
    "fill_alpha": 0.35,  # 填充透明度 (0.0-1.0)
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

# 多进程设置
MULTIPROCESS_SETTINGS = {
    "enable_multiprocess": True,
    "process_count": max(4, cpu_count // 2),  # 至少使用4个进程或CPU核心数的一半
}


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
    sequence_dir_path: str, output_video_path: str, output_frames_dir: str = None
):
    """处理单个序列，生成带GT框的视频和/或帧图像"""

    start_time = time.time()

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
    if VIDEO_SETTINGS["max_width"] > 0 or VIDEO_SETTINGS["max_height"] > 0:
        width_ratio = (
            VIDEO_SETTINGS["max_width"] / image_width
            if VIDEO_SETTINGS["max_width"] > 0
            else 1
        )
        height_ratio = (
            VIDEO_SETTINGS["max_height"] / image_height
            if VIDEO_SETTINGS["max_height"] > 0
            else 1
        )
        scale_ratio = min(width_ratio, height_ratio)

    # 计算最终尺寸（无论是否保存视频都需要）
    final_width = int(image_width * scale_ratio)
    final_height = int(image_height * scale_ratio)

    # 生成颜色字典
    color_dict = (
        generate_color_dict(annotation_directory)
        if VIDEO_SETTINGS["different_color"]
        else None
    )

    # 创建视频输出器
    video_out = None
    if VIDEO_SETTINGS["save_video"]:
        output_dir = os.path.dirname(output_video_path)
        os.makedirs(output_dir, exist_ok=True)

        if output_video_path.endswith(".mp4"):
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        else:
            fourcc = cv2.VideoWriter_fourcc(*"XVID")

        video_out = cv2.VideoWriter(
            output_video_path,
            fourcc,
            VIDEO_SETTINGS["fps"],
            (final_width, final_height),
        )

        if not video_out.isOpened():
            print(f"无法创建视频文件: {output_video_path}")
            return False

    # 创建帧图像输出目录
    if VIDEO_SETTINGS["save_frames"] and output_frames_dir:
        os.makedirs(output_frames_dir, exist_ok=True)

    # 用于绘制轨迹的中心点历史
    center_point_trajectory_dict: dict = {}

    file_count = len(annotation_directory.annotation_file_list)

    print(f"开始处理序列: {os.path.basename(sequence_dir_path)}, 共{file_count}帧")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    frame_start_time = time.time()

    for i, annotation in enumerate(
        tqdm.tqdm(annotation_directory.annotation_file_list, desc="处理帧")
    ):
        frame_index = i + 1

        if VIDEO_SETTINGS["show_box"]:
            # 创建渲染配置对象
            render_config = RenderConfig(
                with_text=VIDEO_SETTINGS["with_text"],
                color=VIDEO_SETTINGS["unselected_color"],
                text_color=VIDEO_SETTINGS["text_color"],
                thickness=VIDEO_SETTINGS["thickness"],
                center_point_trajectory=center_point_trajectory_dict,
                draw_trajectory=VIDEO_SETTINGS["center_point_trajectory"],
                selection_label=VIDEO_SETTINGS["selection_label"],
                selection_color=VIDEO_SETTINGS["selected_color"],
                only_selection_box=VIDEO_SETTINGS["only_selection_box"],
                crop_selection=VIDEO_SETTINGS["only_near_selection"],
                not_found_return_none=VIDEO_SETTINGS["only_near_selection"],
                crop_padding=VIDEO_SETTINGS["crop_padding"],
                color_dict=color_dict,
                # 添加矩形填充配置
                fill_rectangle=VIDEO_SETTINGS["fill_rectangle"],
                fill_alpha=VIDEO_SETTINGS["fill_alpha"],
            )

            # 使用新版接口
            image = annotation.get_cv_mat_with_box(render_config)
        else:
            image = annotation.get_cv_mat()

        if image is None:
            continue

        # 添加帧信息文本
        if VIDEO_SETTINGS["show_frame_text"]:
            text_list: List[str] = []
            if VIDEO_SETTINGS["show_frame_progress"]:
                text_list.append(f"Frame: {frame_index}/{file_count}")
            if VIDEO_SETTINGS["show_frame_object_count"]:
                text_list.append(f"Objects: {annotation.annotation_count}")

            text = " | ".join(text_list)
            cv2.putText(
                image, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
            )

        # 缩放图像
        if scale_ratio != 1:
            image = cv2.resize(image, (final_width, final_height))

        # 保存帧图像
        if VIDEO_SETTINGS["save_frames"] and output_frames_dir:
            # 获取原始图像文件名（不包含扩展名）
            original_filename = os.path.splitext(annotation.pic_file_name)[0]
            frame_output_path = os.path.join(
                output_frames_dir, f"{original_filename}.jpg"
            )
            cv2.imwrite(frame_output_path, image)

        # 写入视频
        if VIDEO_SETTINGS["save_video"] and video_out:
            video_out.write(image)

        # 每处理10帧显示一次时间信息
        if frame_index % 10 == 0 or frame_index == file_count:
            current_time = time.time()
            elapsed_time = current_time - frame_start_time
            avg_time_per_frame = elapsed_time / frame_index
            remaining_frames = file_count - frame_index
            estimated_remaining_time = avg_time_per_frame * remaining_frames

            print(
                f"已处理 {frame_index}/{file_count} 帧, "
                f"平均 {avg_time_per_frame:.3f}s/帧, "
                f"预计剩余时间: {timedelta(seconds=int(estimated_remaining_time))}"
            )

    if video_out:
        video_out.release()
        print(f"视频已保存到: {output_video_path}")

    if VIDEO_SETTINGS["save_frames"] and output_frames_dir:
        print(f"帧图像已保存到: {output_frames_dir}")

    total_time = time.time() - start_time
    print(f"序列处理完成，总用时: {timedelta(seconds=int(total_time))}")
    print(f"平均处理速度: {file_count/total_time:.2f} 帧/秒")

    return True


def process_single_sequence(args):
    """处理单个序列的包装函数，用于多进程"""
    sequence_dir_path, output_video_path, output_frames_dir = args
    start_time = time.time()
    try:
        result = process_sequence(
            sequence_dir_path, output_video_path, output_frames_dir
        )
        end_time = time.time()
        process_time = end_time - start_time
        sequence_name = os.path.basename(sequence_dir_path)
        print(f"序列 {sequence_name} 处理用时: {timedelta(seconds=int(process_time))}")
        return result
    except Exception as e:
        print(f"处理序列时发生错误 {sequence_dir_path}: {str(e)}")
        return False


def main():
    """主函数"""
    main_start_time = time.time()
    print(f"程序开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 配置参数
    base_path = r"/home/konghaomin/Datasets/MaritimeTrackAllData/MT20250319/LabelMe"
    # base_path = r"H:\Datasets\MaritimeTrackAllData\LabelMe"
    # base_path = r"H:\Datasets\SMD\SMD_LabelMe_Fix_20250509"

    level_1 = os.path.basename(base_path)
    level_2 = os.path.basename(os.path.dirname(base_path))

    # 输出目录设置
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_base_dir = os.path.join(current_dir, "output", "seq_gt")
    frames_base_dir = os.path.join(current_dir, "output", "seq_gt_frames")

    frames_base_dir = os.path.join(frames_base_dir, level_2, level_1)

    if os.path.exists(frames_base_dir):
        shutil.rmtree(frames_base_dir)

    os.makedirs(frames_base_dir, exist_ok=True)

    # 获取所有序列目录
    sequence_dir_list = get_dataset_dir_list(
        base_path,
        depth=1,
    )

    if not sequence_dir_list:
        print(f"在路径 {base_path} 下未找到任何序列目录")
        return

    print(f"在路径 {base_path} 下找到 {len(sequence_dir_list)} 个序列目录")

    # 准备处理参数
    process_args = []
    for sequence_dir_path in sequence_dir_list:
        # 获取视频名和序列名
        sequence_name = os.path.basename(sequence_dir_path)
        video_name = os.path.basename(os.path.dirname(sequence_dir_path))

        # 生成输出视频文件名
        output_video_name = f"{video_name}_{sequence_name}.mp4"
        output_video_path = os.path.join(output_base_dir, output_video_name)

        # 生成帧图像输出目录
        output_frames_dir = os.path.join(frames_base_dir, video_name, sequence_name)

        process_args.append((sequence_dir_path, output_video_path, output_frames_dir))

    # 处理序列
    success_count = 0
    processing_start_time = time.time()

    if MULTIPROCESS_SETTINGS["enable_multiprocess"] and len(sequence_dir_list) > 1:
        # 多进程处理
        print(f"使用 {MULTIPROCESS_SETTINGS['process_count']} 个进程并行处理序列")
        print(f"多进程处理开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        with Pool(processes=MULTIPROCESS_SETTINGS["process_count"]) as pool:
            # 使用进度条显示整体进度
            results = list(
                tqdm.tqdm(
                    pool.imap(process_single_sequence, process_args),
                    total=len(process_args),
                    desc="处理序列",
                )
            )

        success_count = sum(results)
    else:
        # 单进程处理（保持原有逻辑）
        print(f"单进程处理开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        for i, (sequence_dir_path, output_video_path, output_frames_dir) in enumerate(
            process_args
        ):
            sequence_name = os.path.basename(sequence_dir_path)
            video_name = os.path.basename(os.path.dirname(sequence_dir_path))

            print(
                f"\n处理序列 ({i+1}/{len(process_args)}): {video_name}/{sequence_name}"
            )

            seq_start_time = time.time()
            if process_sequence(
                sequence_dir_path, output_video_path, output_frames_dir
            ):
                success_count += 1
            else:
                print(f"处理失败: {video_name}/{sequence_name}")

            # 计算剩余时间估算
            if i > 0:  # 至少处理一个序列后才能估算
                elapsed_time = time.time() - processing_start_time
                avg_time_per_seq = elapsed_time / (i + 1)
                remaining_sequences = len(process_args) - (i + 1)
                estimated_remaining_time = avg_time_per_seq * remaining_sequences

                print(
                    f"已完成 {i+1}/{len(process_args)} 个序列, "
                    f"平均 {timedelta(seconds=int(avg_time_per_seq))}/序列, "
                    f"预计剩余时间: {timedelta(seconds=int(estimated_remaining_time))}"
                )

    processing_end_time = time.time()
    total_processing_time = processing_end_time - processing_start_time
    total_main_time = processing_end_time - main_start_time

    print(f"\n{'='*50}")
    print(f"处理完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"完成! 成功处理了 {success_count}/{len(sequence_dir_list)} 个序列")
    print(f"序列处理总用时: {timedelta(seconds=int(total_processing_time))}")
    print(f"程序总运行时间: {timedelta(seconds=int(total_main_time))}")

    if success_count > 0:
        avg_time_per_success = total_processing_time / success_count
        print(f"平均每个序列处理时间: {timedelta(seconds=int(avg_time_per_success))}")

    if VIDEO_SETTINGS["save_video"]:
        print(f"视频输出目录: {output_base_dir}")
    if VIDEO_SETTINGS["save_frames"]:
        print(f"帧图像输出目录: {frames_base_dir}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
