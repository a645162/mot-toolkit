import os
import shutil
import argparse
from typing import List, Tuple

import tqdm
import cv2

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list

crop = True

ratio = (16, 9)


def walk_dir_get_dir_list(dir_path: str) -> List[str]:
    """获取目录下的所有子目录列表"""
    dir_path = dir_path.strip()

    if dir_path == "":
        return []

    dir_path = os.path.abspath(dir_path)

    dir_list = []
    # Not include child directory

    for dir_name in os.listdir(dir_path):
        dir_path_tmp = os.path.join(dir_path, dir_name)
        if os.path.isdir(dir_path_tmp):
            dir_list.append(dir_path_tmp)

    return dir_list


def get_first_frame_from_sequence(sequence_dir_path: str) -> str:
    """
    获取序列目录中的首帧图片路径

    Args:
        sequence_dir_path: 序列目录路径

    Returns:
        str: 首帧图片的完整路径，如果没有找到则返回空字符串
    """
    if not os.path.exists(sequence_dir_path) or not os.path.isdir(sequence_dir_path):
        return ""

    # 获取所有jpg文件
    jpg_files = []
    for file_name in os.listdir(sequence_dir_path):
        if file_name.lower().endswith(".jpg"):
            # 尝试提取文件名中的数字序号
            try:
                # 移除.jpg扩展名
                name_without_ext = os.path.splitext(file_name)[0]
                # 转换为整数（假设文件名就是数字）
                frame_number = int(name_without_ext)
                jpg_files.append((frame_number, file_name))
            except ValueError:
                continue

    if not jpg_files:
        return ""

    # 按帧号排序，获取首帧
    jpg_files.sort(key=lambda x: x[0])
    first_frame_name = jpg_files[0][1]
    first_frame_path = os.path.join(sequence_dir_path, first_frame_name)

    return first_frame_path


def normalize_ratio(ratio: Tuple[int, int]) -> Tuple[int, int]:
    """
    确保ratio是一个元组，并且前面的数字大于或等于后面的数字

    Args:
        ratio: 宽高比元组

    Returns:
        Tuple[int, int]: 标准化后的比例，确保第一个数字>=第二个数字
    """
    if not isinstance(ratio, tuple) or len(ratio) != 2:
        ratio = (16, 9)  # 默认值

    a, b = ratio
    # 确保第一个数字大于等于第二个数字
    if a < b:
        return (b, a)
    return (a, b)


def crop_and_resize_image(
    image_path: str, output_path: str, target_ratio: Tuple[int, int], crop: bool = True
) -> bool:
    """
    根据crop参数和target_ratio对图片进行处理

    Args:
        image_path: 输入图片路径
        output_path: 输出图片路径
        target_ratio: 目标宽高比 (宽, 高)
        crop: 是否进行裁剪处理

    Returns:
        bool: 处理是否成功
    """
    try:
        # 读取图片
        img = cv2.imread(image_path)
        if img is None:
            return False

        height, width = img.shape[:2]

        if crop:
            # 标准化ratio，确保第一个数字>=第二个数字
            normalized_ratio = normalize_ratio(target_ratio)
            target_w_ratio, target_h_ratio = normalized_ratio

            # 判断当前图片是横屏还是竖屏
            is_landscape = width >= height

            if is_landscape:
                # 横屏：使用原始ratio (宽比高)
                target_aspect = target_w_ratio / target_h_ratio
            else:
                # 竖屏：反转ratio (高比宽)
                target_aspect = target_h_ratio / target_w_ratio

            # 计算当前图片的宽高比
            current_aspect = width / height

            # 根据目标宽高比进行中心裁剪
            if current_aspect > target_aspect:
                # 当前图片更宽，需要裁剪宽度
                new_width = int(height * target_aspect)
                x_offset = (width - new_width) // 2
                cropped_img = img[0:height, x_offset : x_offset + new_width]
            else:
                # 当前图片更高，需要裁剪高度
                new_height = int(width / target_aspect)
                y_offset = (height - new_height) // 2
                cropped_img = img[y_offset : y_offset + new_height, 0:width]

            # 使用裁剪后的图片
            processed_img = cropped_img
        else:
            # 不裁剪，直接使用原图
            processed_img = img

        # 保存处理后的图片
        cv2.imwrite(output_path, processed_img)
        return True

    except Exception as e:
        print(f"处理图片失败 {image_path}: {e}")
        return False


def process_dataset(base_path: str, output_dir: str, black_list: List[str] = None):
    """
    处理数据集，提取每个序列的首帧

    Args:
        base_path: 数据集基础路径
        output_dir: 输出目录路径
        black_list: 要排除的视频关键词列表
    """
    if black_list is None:
        black_list = []

    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # 获取所有视频目录
    video_dir_list = get_dataset_dir_list(base_path)

    # 过滤黑名单
    filtered_video_dir_list = []
    for video_dir_path in video_dir_list:
        found_in_blacklist = False
        for keywords in black_list:
            if keywords in video_dir_path:
                found_in_blacklist = True
                break
        if not found_in_blacklist:
            filtered_video_dir_list.append(video_dir_path)

    video_dir_list = filtered_video_dir_list

    # 计算总序列数用于进度条
    total_sequences = 0
    for video_dir_path in video_dir_list:
        sequence_dir_list = walk_dir_get_dir_list(video_dir_path)
        total_sequences += len(sequence_dir_list)

    successful_copies = 0
    processed_sequences = 0

    # 创建总进度条
    with tqdm.tqdm(total=total_sequences, desc="处理序列", unit="seq") as pbar:
        for video_dir_path in video_dir_list:
            video_name = os.path.basename(video_dir_path)

            # 获取该视频下的所有序列目录
            sequence_dir_list = walk_dir_get_dir_list(video_dir_path)

            for sequence_dir_path in sequence_dir_list:
                sequence_name = os.path.basename(sequence_dir_path)
                processed_sequences += 1

                # 更新进度条描述
                pbar.set_description(f"处理 {video_name}/{sequence_name}")

                # 获取首帧图片路径
                first_frame_path = get_first_frame_from_sequence(sequence_dir_path)

                if first_frame_path and os.path.exists(first_frame_path):
                    # 构造输出文件名：视频名_序列名.jpg
                    output_filename = f"{video_name}_{sequence_name}.jpg"
                    output_path = os.path.join(output_dir, output_filename)

                    try:
                        if crop:
                            # 使用OpenCV处理图片
                            success = crop_and_resize_image(
                                first_frame_path, output_path, ratio, crop
                            )
                            if success:
                                successful_copies += 1
                        else:
                            # 直接复制文件
                            shutil.copy2(first_frame_path, output_path)
                            successful_copies += 1

                        pbar.set_postfix(
                            {
                                "成功": successful_copies,
                                "失败": processed_sequences - successful_copies,
                            }
                        )
                    except Exception as e:
                        pbar.set_postfix(
                            {
                                "成功": successful_copies,
                                "失败": processed_sequences - successful_copies,
                                "错误": str(e)[:20],
                            }
                        )
                else:
                    pbar.set_postfix(
                        {
                            "成功": successful_copies,
                            "失败": processed_sequences - successful_copies,
                        }
                    )

                # 更新进度条
                pbar.update(1)

    print(f"\n处理完成!")
    print(f"总序列数: {total_sequences}")
    print(f"成功复制: {successful_copies}")
    print(f"失败数量: {total_sequences - successful_copies}")
    print(f"输出目录: {output_dir}")
    print(f"裁剪模式: {'开启' if crop else '关闭'}")
    print(f"目标比例: {ratio}")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="提取数据集每个序列的首帧图片")

    parser.add_argument(
        "--base-path",
        type=str,
        default=r"/home/konghaomin/Datasets/MaritimeTrackAllData/MT20250319/LabelMe",
        help="数据集基础路径",
    )
    parser.add_argument(
        "--black-list",
        nargs="+",
        default=["BV14S4y147jX-t5PTpDLBGiSESMzw"],
        help="要排除的视频关键词列表",
    )

    opt = parser.parse_args()

    # 可以根据需要修改默认路径
    # opt.base_path = r"/home/konghaomin/Datasets/SMD_LabelMe_Fix_20250509"
    opt.base_path = r"D:\Datasets\MaritimeTrackAllData\LabelMe"
    # opt.base_path = r"H:\Datasets\SMD\SMD_LabelMe_Fix_20250509"

    return opt


def main():
    """主函数"""
    args = parse_args()

    base_path = os.path.abspath(args.base_path)
    black_list = args.black_list

    # 获取当前py文件所在目录
    current_script_dir = os.path.dirname(os.path.abspath(__file__))

    # 构造输出目录路径
    output_dir = os.path.join(current_script_dir, "output", "first_frame")

    print(f"数据集路径: {base_path}")
    print(f"输出目录: {output_dir}")
    print(f"黑名单: {black_list}")
    print("-" * 50)

    # 处理数据集
    process_dataset(base_path, output_dir, black_list)


if __name__ == "__main__":
    main()
