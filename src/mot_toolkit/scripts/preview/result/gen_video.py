import os
import argparse
import multiprocessing
from typing import List, Tuple
from itertools import cycle


def handle_seq(args: Tuple[str, str]) -> None:
    """
    处理单个序列的图片，将其转换为视频

    Args:
        args: 包含序列目录路径和GPU ID的元组
    """
    seq_dir_path, gpu_id = args
    # 设置环境变量，指定使用的GPU
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)

    seq_name = os.path.basename(seq_dir_path)
    video_name = seq_name + ".mp4"
    video_path = os.path.join(video_output_dir, video_name)

    print(f"Processing {seq_name} on GPU {gpu_id}")

    # 调用FFmpeg将目录中的所有图片合成为视频
    # 文件格式为从00000000.jpg开始的图片
    ffmpeg_cmd = (
        f"ffmpeg -y -r 25 -f image2 -i '{os.path.join(seq_dir_path, '%08d.jpg')}' "
        f"-c:v h264_nvenc -preset fast -crf 23 -pix_fmt yuv420p '{video_path}'"
    )
    os.system(ffmpeg_cmd)
    print(f"Generated: {video_path} on GPU {gpu_id}")


def main() -> None:
    """
    主函数：解析参数并并行处理多个序列的图片到视频的转换
    """
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description="将序列图片转换为视频")
    parser.add_argument(
        "--use-gpu",
        type=str,
        default="0,1,2,3",
        help='指定要使用的GPU ID，用逗号分隔 (默认: "0,1,2,3")',
    )
    parser.add_argument(
        "--count-per-gpu", type=int, default=2, help="每个GPU分配的任务数 (默认: 2)"
    )
    parser.add_argument(
        "--seq-list-dir",
        type=str,
        default=r"outputs/MeMOTR_MaritimeTrack_Full_Same_73/val/checkpoint_19_tracker/plot_img",
        help="包含序列目录的根目录",
    )
    parser.add_argument(
        "--video-output-dir",
        type=str,
        default="outputs/MeMOTR_MaritimeTrack_Full_Same_73/val/checkpoint_19_tracker/plot_img_video",
        help="视频输出目录",
    )

    # 解析命令行参数
    args = parser.parse_args()

    # 从参数获取配置
    use_gpu = args.use_gpu
    count_per_gpu = args.count_per_gpu
    seq_list_dir = args.seq_list_dir

    # 设置全局变量(用于handle_seq函数)
    global video_output_dir
    video_output_dir = args.video_output_dir

    # 确保输出目录存在
    if not os.path.exists(video_output_dir):
        os.makedirs(video_output_dir)

    # 获取所有序列目录
    seq_dir_list = os.listdir(seq_list_dir)
    seq_dir_list = [os.path.join(seq_list_dir, i) for i in seq_dir_list]
    seq_dir_list = [i for i in seq_dir_list if os.path.isdir(i)]

    # 解析GPU ID列表
    gpu_ids = use_gpu.split(",")

    # 计算总的并行任务数
    total_workers = len(gpu_ids) * count_per_gpu

    # 为每个任务分配GPU ID
    # 创建一个循环的GPU ID序列，每个GPU重复count_per_gpu次
    expanded_gpu_ids: List[str] = []
    for gpu_id in gpu_ids:
        expanded_gpu_ids.extend([gpu_id] * count_per_gpu)

    # 准备任务参数列表，每个任务是(seq_dir_path, gpu_id)的元组
    tasks: List[Tuple[str, str]] = []
    for seq_dir, gpu_id in zip(seq_dir_list, cycle(expanded_gpu_ids)):
        tasks.append((seq_dir, gpu_id))

    # 使用多进程池处理任务
    with multiprocessing.Pool(total_workers) as pool:
        pool.map(handle_seq, tasks)


if __name__ == "__main__":
    main()
