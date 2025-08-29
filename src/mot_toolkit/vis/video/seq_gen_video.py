import os
import subprocess
import re
from multiprocessing import Pool
from functools import partial

import shutil
from multiprocessing import Manager

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list

use_gpu = "0,1,2,3,4,5,6,7"
# use_gpu = "0"
task_count_per_gpu = 2

# ========== 视频质量配置参数 ==========
# 质量级别预设: "low", "medium", "high", "best", "custom"
QUALITY_PRESET = "high"

# 自定义质量参数 (当QUALITY_PRESET="custom"时生效)
VIDEO_CONFIG = {
    # 通用参数
    "framerate": 25,  # 视频帧率
    "pixel_format": "yuv420p",  # 像素格式
    # 质量控制参数
    "crf_qp": 18,  # CRF/QP值 (越小质量越高: 0-51, 推荐: 18-28)
    "bitrate": "5M",  # 目标比特率 (如: "2M", "5M", "10M")
    "max_bitrate": "8M",  # 最大比特率
    "buffer_size": "10M",  # 缓冲区大小
    # 编码预设 (速度vs质量平衡)
    "nvidia_preset": "slow",  # NVIDIA: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
    "amd_quality": "quality",  # AMD: speed, balanced, quality
    "intel_preset": "slower",  # Intel: veryfast, faster, fast, medium, slow, slower, veryslow
    "cpu_preset": "slower",  # CPU: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
}

# 预定义质量级别
QUALITY_PRESETS = {
    "low": {
        "crf_qp": 28,
        "bitrate": "1M",
        "max_bitrate": "2M",
        "buffer_size": "3M",
        "nvidia_preset": "fast",
        "amd_quality": "speed",
        "intel_preset": "fast",
        "cpu_preset": "fast",
    },
    "medium": {
        "crf_qp": 23,
        "bitrate": "3M",
        "max_bitrate": "5M",
        "buffer_size": "7M",
        "nvidia_preset": "medium",
        "amd_quality": "balanced",
        "intel_preset": "medium",
        "cpu_preset": "medium",
    },
    "high": {
        "crf_qp": 18,
        "bitrate": "5M",
        "max_bitrate": "8M",
        "buffer_size": "10M",
        "nvidia_preset": "slow",
        "amd_quality": "quality",
        "intel_preset": "slower",
        "cpu_preset": "slow",
    },
    "best": {
        "crf_qp": 15,
        "bitrate": "8M",
        "max_bitrate": "12M",
        "buffer_size": "15M",
        "nvidia_preset": "slower",
        "amd_quality": "quality",
        "intel_preset": "veryslow",
        "cpu_preset": "slower",
    },
}

seq_list_dir = r"/home/konghaomin/mot-toolkit/src/mot_toolkit/vis/plot/output/seq_gt_frames/MT20250319/LabelMe"
seq_list_dir = r"/home/konghaomin/MOTIP/inference_outputs/MT_All_mt_anchor_v4_ffn_v2_c_20250624164142/submit/default/DanceTrack/val/checkpoint_8/tracker/plot_img"

video_output_dir = "/home/konghaomin/mot-toolkit/src/mot_toolkit/vis/plot/output/seq_gt_frames/MT20250319/LabelMe_video"
video_output_dir = "/home/konghaomin/mot-toolkit/src/mot_toolkit/vis/plot/output/infer_result/All"

if os.path.exists(video_output_dir):
    shutil.rmtree(video_output_dir)

os.makedirs(video_output_dir)

# seq_dir_list = os.listdir(seq_list_dir)
# seq_dir_list = [os.path.join(seq_list_dir, i) for i in seq_dir_list]
# seq_dir_list = [i for i in seq_dir_list if os.path.isdir(i)]

seq_dir_list = get_dataset_dir_list(seq_list_dir, depth=1)

# Debug only
# seq_dir_list = seq_dir_list[:1]

# 添加全局变量来跟踪失败的序列
failed_sequences = []


def detect_gpu_type():
    """检测可用的GPU类型，优先级：NVIDIA > AMD > Intel"""
    gpu_info = {"nvidia": [], "amd": [], "intel": []}

    # 检测NVIDIA GPU
    try:
        result = subprocess.run(
            ["nvidia-smi", "-L"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            for i, line in enumerate(lines):
                if "GPU" in line:
                    gpu_info["nvidia"].append(i)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # 检测AMD GPU (使用rocm-smi)
    try:
        result = subprocess.run(
            ["rocm-smi", "--showid"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if re.search(r"GPU\[\d+\]", line):
                    match = re.search(r"GPU\[(\d+)\]", line)
                    if match:
                        gpu_info["amd"].append(int(match.group(1)))
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # 检测Intel GPU (使用intel_gpu_top或其他方法)
    try:
        result = subprocess.run(
            ["intel_gpu_top", "-l"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and "intel" in result.stdout.lower():
            gpu_info["intel"].append(0)  # Intel通常只有一个集成GPU
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # 返回优先级最高的可用GPU类型
    if gpu_info["nvidia"]:
        return "nvidia", gpu_info["nvidia"]
    elif gpu_info["amd"]:
        return "amd", gpu_info["amd"]
    elif gpu_info["intel"]:
        return "intel", gpu_info["intel"]
    else:
        return "cpu", []


def get_encoder_config(gpu_type, gpu_id=None):
    """根据GPU类型返回相应的编码器配置"""
    # 获取当前配置
    if QUALITY_PRESET == "custom":
        config = VIDEO_CONFIG
    else:
        config = QUALITY_PRESETS.get(QUALITY_PRESET, QUALITY_PRESETS["high"])

    if gpu_type == "nvidia":
        encoder = "h264_nvenc"
        return (
            f"-c:v {encoder} "
            f"-preset {config['nvidia_preset']} "
            f"-crf {config['crf_qp']} "
            f"-b:v {config['bitrate']} "
            f"-maxrate {config['max_bitrate']} "
            f"-bufsize {config['buffer_size']}"
        )
    elif gpu_type == "amd":
        encoder = "h264_amf"
        return (
            f"-c:v {encoder} "
            f"-quality {config['amd_quality']} "
            f"-rc cqp "
            f"-qp {config['crf_qp']} "
            f"-b:v {config['bitrate']}"
        )
    elif gpu_type == "intel":
        encoder = "h264_qsv"
        gpu_option = f"-init_hw_device qsv=hw:{gpu_id}" if gpu_id is not None else ""
        return (
            f"{gpu_option} "
            f"-c:v {encoder} "
            f"-preset {config['intel_preset']} "
            f"-global_quality {config['crf_qp']} "
            f"-b:v {config['bitrate']}"
        )
    else:  # CPU
        return (
            f"-c:v libx264 "
            f"-preset {config['cpu_preset']} "
            f"-crf {config['crf_qp']} "
            f"-b:v {config['bitrate']} "
            f"-maxrate {config['max_bitrate']} "
            f"-bufsize {config['buffer_size']}"
        )


def get_start_frame_and_pattern(seq_dir_path):
    """检测目录中图片文件的起始帧号和文件名模式"""
    if not os.path.exists(seq_dir_path):
        return 1, "%08d.jpg"

    # 获取所有jpg文件
    jpg_files = [f for f in os.listdir(seq_dir_path) if f.lower().endswith(".jpg")]

    if not jpg_files:
        return 1, "%08d.jpg"

    # 提取文件名中的数字部分
    frame_numbers = []
    for filename in jpg_files:
        # 提取文件名中的数字部分（不包括扩展名）
        basename = os.path.splitext(filename)[0]
        if basename.isdigit():
            frame_numbers.append(int(basename))

    if not frame_numbers:
        return 1, "%08d.jpg"

    # 找到最小的帧号作为起始帧
    start_frame = min(frame_numbers)

    # 根据文件名长度确定格式模式
    first_file = jpg_files[0]
    basename = os.path.splitext(first_file)[0]
    if basename.isdigit():
        digit_count = len(basename)
        pattern = f"%0{digit_count}d.jpg"
    else:
        pattern = "%08d.jpg"

    return start_frame, pattern


def handle_seq(seq_dir_path, gpu_type="cpu", gpu_id=None, failed_list=None):
    """处理单个序列，生成视频"""

    print(
        f"Processing sequence: {seq_dir_path} on {gpu_type.upper()} GPU {gpu_id if gpu_id is not None else 'CPU'}"
    )

    seq_name = os.path.basename(seq_dir_path)
    video_name = os.path.basename(os.path.dirname(seq_dir_path))
    video_name = f"{video_name}_{seq_name}.mp4"
    video_path = os.path.join(video_output_dir, video_name)

    if not os.path.exists(seq_dir_path):
        os.makedirs(seq_dir_path, exist_ok=True)

    # 检测起始帧和文件名模式
    start_frame, pattern = get_start_frame_and_pattern(seq_dir_path)
    print(f"  Start frame: {start_frame}, Pattern: {pattern}")

    # 设置GPU环境变量
    env = os.environ.copy()
    if gpu_type == "nvidia" and gpu_id is not None:
        env["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    elif gpu_type == "amd" and gpu_id is not None:
        env["HIP_VISIBLE_DEVICES"] = str(gpu_id)

    # 获取编码器配置
    encoder_config = get_encoder_config(gpu_type, gpu_id)

    # 构建FFmpeg命令，使用检测到的起始帧号
    input_pattern = os.path.join(seq_dir_path, pattern)

    # 获取当前配置用于帧率和像素格式
    if QUALITY_PRESET == "custom":
        config = VIDEO_CONFIG
    else:
        config = QUALITY_PRESETS.get(QUALITY_PRESET, QUALITY_PRESETS["high"])

    ffmpeg_cmd = (
        f"ffmpeg -y -start_number {start_frame} "
        f"-r {config.get('framerate', VIDEO_CONFIG['framerate'])} "
        f"-f image2 -i '{input_pattern}' "
        f"{encoder_config} "
        f"-pix_fmt {config.get('pixel_format', VIDEO_CONFIG['pixel_format'])} "
        f"'{video_path}'"
    )

    try:
        result = subprocess.run(
            ffmpeg_cmd, shell=True, env=env, capture_output=True, text=True
        )
        if result.returncode == 0:
            print(
                f"✅ Generated: {video_path} (using {gpu_type.upper()} GPU {gpu_id if gpu_id is not None else 'CPU'})"
            )
            return True
        else:
            error_msg = f"FFmpeg error: {result.stderr}"
            print(f"❌ Error generating {video_path}: {error_msg}")
            if failed_list is not None:
                failed_list.append((seq_dir_path, error_msg))
            return False
    except Exception as e:
        error_msg = f"Exception: {str(e)}"
        print(f"❌ Exception while processing {seq_dir_path}: {error_msg}")
        if failed_list is not None:
            failed_list.append((seq_dir_path, error_msg))
        return False


def distribute_tasks_by_queue(seq_list, gpu_type, available_gpus):
    """将任务按队列分配给GPU，每个GPU一个队列"""
    if not available_gpus:
        # 如果没有GPU，使用CPU处理
        return [[(seq, "cpu", None) for seq in seq_list]]

    # 解析use_gpu参数
    if use_gpu:
        requested_gpus = [
            int(x.strip()) for x in use_gpu.split(",") if x.strip().isdigit()
        ]
        # 只使用请求的且可用的GPU
        available_gpus = [gpu for gpu in available_gpus if gpu in requested_gpus]

    if not available_gpus:
        print("Warning: No requested GPUs available, falling back to CPU")
        return [[(seq, "cpu", None) for seq in seq_list]]

    # 为每个GPU创建一个任务队列
    gpu_queues = [[] for _ in available_gpus]

    # 轮流分配任务到各个GPU队列
    for i, seq in enumerate(seq_list):
        gpu_index = i % len(available_gpus)
        gpu_id = available_gpus[gpu_index]
        gpu_queues[gpu_index].append((seq, gpu_type, gpu_id))

    # 打印每个GPU的任务数量
    for i, (gpu_id, queue) in enumerate(zip(available_gpus, gpu_queues)):
        print(f"GPU {gpu_id}: {len(queue)} tasks")

    return gpu_queues


def process_gpu_queue(gpu_queue_with_failed):
    """处理单个GPU的任务队列（串行执行）"""
    gpu_queue, failed_list = gpu_queue_with_failed
    results = []

    for task in gpu_queue:
        seq_path, gpu_type, gpu_id = task
        result = handle_seq(seq_path, gpu_type, gpu_id, failed_list)
        results.append(result)

    return results


def main():
    """主函数"""
    print("Detecting available GPUs...")
    gpu_type, available_gpus = detect_gpu_type()

    if gpu_type == "cpu":
        print("No GPU detected, using CPU encoding")
    else:
        print(f"Detected {gpu_type.upper()} GPUs: {available_gpus}")

    # 创建共享的失败列表
    manager = Manager()
    failed_list = manager.list()

    # 按队列分配任务
    gpu_queues = distribute_tasks_by_queue(
        seq_dir_list, gpu_type, available_gpus.copy()
    )

    # 为每个队列添加失败列表
    gpu_queues_with_failed = [(queue, failed_list) for queue in gpu_queues]

    print(
        f"Processing {len(seq_dir_list)} sequences across {len(gpu_queues)} GPU queues..."
    )

    # 并行处理各个GPU队列（每个GPU队列内部串行执行）
    max_workers = len(gpu_queues)

    all_results = []
    with Pool(processes=max_workers) as pool:
        queue_results = pool.map(process_gpu_queue, gpu_queues_with_failed)
        # 展平结果列表
        for queue_result in queue_results:
            all_results.extend(queue_result)

    # 统计结果
    total_sequences = len(seq_dir_list)
    successful_count = sum(1 for result in all_results if result)
    failed_count = len(failed_list)

    print(f"\n{'='*60}")
    print("处理完成！\n")
    
    print(f"总序列数: {total_sequences}")
    print(f"成功: {successful_count}")
    print(f"失败: {failed_count}")
    print(f"{'='*60}")

    # 输出失败的序列列表
    if failed_list:
        print(f"\n❌ 失败的序列列表 ({failed_count} 个):")
        print("-" * 60)
        for i, (seq_path, error_msg) in enumerate(failed_list, 1):
            print(f"{i:3d}. {seq_path}")
            print(f"     错误: {error_msg}")
            print()

        # 将失败列表保存到文件
        failed_log_path = os.path.join(video_output_dir, "failed_sequences.txt")
        with open(failed_log_path, "w", encoding="utf-8") as f:
            f.write(f"失败的序列列表 (共 {failed_count} 个)\n")
            f.write("=" * 60 + "\n\n")
            for i, (seq_path, error_msg) in enumerate(failed_list, 1):
                f.write(f"{i:3d}. {seq_path}\n")
                f.write(f"     错误: {error_msg}\n\n")

        print(f"失败列表已保存到: {failed_log_path}")
    else:
        print("\n✅ 所有序列都处理成功！")


if __name__ == "__main__":
    main()
