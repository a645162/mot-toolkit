import os
import subprocess
import re
from multiprocessing import Pool
from functools import partial

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list

use_gpu = "0,1,2,3,4,5,6,7"
task_count_per_gpu = 2

seq_list_dir = r"/home/konghaomin/mot-toolkit/src/mot_toolkit/vis/plot/output/seq_gt_frames/MT20250319/LabelMe"

video_output_dir = "/home/konghaomin/mot-toolkit/src/mot_toolkit/vis/plot/output/seq_gt_frames/MT20250319/LabelMe_video"
if not os.path.exists(video_output_dir):
    os.makedirs(video_output_dir)

# seq_dir_list = os.listdir(seq_list_dir)
# seq_dir_list = [os.path.join(seq_list_dir, i) for i in seq_dir_list]
# seq_dir_list = [i for i in seq_dir_list if os.path.isdir(i)]

seq_dir_list = get_dataset_dir_list(seq_list_dir, depth=1)


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
    if gpu_type == "nvidia":
        encoder = "h264_nvenc"
        gpu_option = f"-gpu {gpu_id}" if gpu_id is not None else ""
        return f"{gpu_option} -c:v {encoder} -preset fast -crf 23"
    elif gpu_type == "amd":
        encoder = "h264_amf"
        return f"-c:v {encoder} -quality speed -rc cqp -qp 23"
    elif gpu_type == "intel":
        encoder = "h264_qsv"
        gpu_option = f"-init_hw_device qsv=hw:{gpu_id}" if gpu_id is not None else ""
        return f"{gpu_option} -c:v {encoder} -preset fast -global_quality 23"
    else:  # CPU
        return "-c:v libx264 -preset fast -crf 23"


def handle_seq(seq_dir_path, gpu_type="cpu", gpu_id=None):
    """处理单个序列，生成视频"""
    seq_name = os.path.basename(seq_dir_path)
    video_name = os.path.basename(os.path.dirname(seq_dir_path))
    video_name = f"{video_name}_{seq_name}.mp4"
    video_path = os.path.join(video_output_dir, video_name)

    if not os.path.exists(seq_dir_path):
        os.makedirs(seq_dir_path, exist_ok=True)

    # 设置GPU环境变量
    env = os.environ.copy()
    if gpu_type == "nvidia" and gpu_id is not None:
        env["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    elif gpu_type == "amd" and gpu_id is not None:
        env["HIP_VISIBLE_DEVICES"] = str(gpu_id)

    # 获取编码器配置
    encoder_config = get_encoder_config(gpu_type, gpu_id)

    # 构建FFmpeg命令
    ffmpeg_cmd = (
        f"ffmpeg -y -r 25 -f image2 -i '{os.path.join(seq_dir_path, '%08d.jpg')}' "
        f"{encoder_config} -pix_fmt yuv420p '{video_path}'"
    )

    try:
        result = subprocess.run(
            ffmpeg_cmd, shell=True, env=env, capture_output=True, text=True
        )
        if result.returncode == 0:
            print(
                f"Generated: {video_path} (using {gpu_type.upper()} GPU {gpu_id if gpu_id is not None else 'CPU'})"
            )
        else:
            print(f"Error generating {video_path}: {result.stderr}")
    except Exception as e:
        print(f"Exception while processing {seq_dir_path}: {e}")


def distribute_tasks(seq_list, gpu_type, available_gpus):
    """将任务分配给可用的GPU"""
    if not available_gpus:
        # 如果没有GPU，使用CPU处理
        return [(seq, "cpu", None) for seq in seq_list]

    # 解析use_gpu参数
    if use_gpu:
        requested_gpus = [
            int(x.strip()) for x in use_gpu.split(",") if x.strip().isdigit()
        ]
        # 只使用请求的且可用的GPU
        available_gpus = [gpu for gpu in available_gpus if gpu in requested_gpus]

    if not available_gpus:
        print("Warning: No requested GPUs available, falling back to CPU")
        return [(seq, "cpu", None) for seq in seq_list]

    # 为每个GPU创建任务队列
    task_assignments = []
    gpu_task_counts = {gpu: 0 for gpu in available_gpus}

    for seq in seq_list:
        # 选择任务数最少的GPU
        selected_gpu = min(available_gpus, key=lambda g: gpu_task_counts[g])
        task_assignments.append((seq, gpu_type, selected_gpu))
        gpu_task_counts[selected_gpu] += 1

        # 如果GPU任务数达到限制，暂时移除该GPU
        if gpu_task_counts[selected_gpu] >= task_count_per_gpu:
            available_gpus.remove(selected_gpu)
            if not available_gpus:
                # 重置GPU列表以继续分配
                available_gpus = [gpu for gpu in gpu_task_counts.keys()]
                gpu_task_counts = {gpu: 0 for gpu in available_gpus}

    return task_assignments


def process_task(task):
    """处理单个任务的包装函数（模块级别函数，可以被多进程序列化）"""
    seq_path, gpu_type, gpu_id = task
    return handle_seq(seq_path, gpu_type, gpu_id)


def main():
    """主函数"""
    print("Detecting available GPUs...")
    gpu_type, available_gpus = detect_gpu_type()

    if gpu_type == "cpu":
        print("No GPU detected, using CPU encoding")
    else:
        print(f"Detected {gpu_type.upper()} GPUs: {available_gpus}")

    # 分配任务
    task_assignments = distribute_tasks(seq_dir_list, gpu_type, available_gpus.copy())

    print(f"Processing {len(task_assignments)} sequences...")

    # 并行处理
    max_workers = (
        len(available_gpus) * task_count_per_gpu
        if available_gpus
        else task_count_per_gpu
    )
    with Pool(processes=max_workers) as pool:
        pool.map(process_task, task_assignments)


if __name__ == "__main__":
    main()
