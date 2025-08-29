import os
import subprocess
import threading
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict

import tqdm

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list

# 导出环境变量，避免NVIDIA任务通知
os.environ["NVI_NOTIFY_IGNORE_TASK"] = "1"

# 配置
base_dir = "/home/konghaomin/Datasets/MaritimeTrackAllData/LabelMe"
use_gpu = "0,1,2,3"

# 每个GPU同时处理的任务数量
task_count_per_gpu = 2

# GPU内存估计 (单位: GB)
memory_per_task = 4.0  # Depth Anything可能比SAM更耗内存
reserved_memory = 1.0  # 保留内存
current_available_memory = 12  # 当前估计可用内存

# 重新计算每个GPU的可用任务数
task_count_per_gpu = min(
    task_count_per_gpu,
    int((current_available_memory - reserved_memory) / memory_per_task),
)

if task_count_per_gpu < 1:
    raise ValueError("当前可用内存不足，无法处理任务。请检查内存设置。")

# 创建一个全局的进度条对象
progress_bar = None
completed_tasks = 0
total_tasks = 0
progress_lock = threading.Lock()


def update_progress():
    """更新全局进度条"""
    global completed_tasks, progress_bar
    with progress_lock:
        completed_tasks += 1
        if progress_bar is not None:
            progress_bar.update(1)


def process_sequence(gpu_id: int, sequence_path: str) -> None:
    """在指定GPU上处理一个序列

    Args:
        gpu_id: 用于处理该序列的GPU ID
        sequence_path: 需要处理的序列路径

    Returns:
        None
    """
    # 复制当前环境变量，以便设置CUDA_VISIBLE_DEVICES
    env = os.environ.copy()
    # 设置当前进程使用的GPU ID
    env["CUDA_VISIBLE_DEVICES"] = str(gpu_id)

    # 获取当前python进程的路径（不是py文件）
    python_executable = sys.executable

    # 构建运行depth_anything_v2_worker.py的命令行参数
    cmd = [
        python_executable,
        "-m",
        "mot_toolkit.scripts.hf.depth_anything_v2.depth_anything_v2_worker",
        sequence_path,
    ]
    # 启动子进程执行序列处理
    subprocess.run(cmd, env=env)

    # 更新进度
    update_progress()


def worker_for_gpu(gpu_id: int, sequence_paths: List[str]) -> None:
    """为一个GPU创建线程池处理多个序列

    Args:
        gpu_id: GPU ID
        sequence_paths: 需要在此GPU上处理的所有序列路径列表

    Returns:
        None
    """
    # 创建线程池，限制最大并行任务数为task_count_per_gpu
    with ThreadPoolExecutor(max_workers=task_count_per_gpu) as executor:
        futures = []
        # 为每个序列提交一个处理任务
        for seq_path in sequence_paths:
            futures.append(executor.submit(process_sequence, gpu_id, seq_path))
        # 等待所有任务完成并获取结果（如果有异常会在这里抛出）
        for future in futures:
            future.result()


def main() -> None:
    """主函数：分配序列到各个GPU并启动处理

    将所有序列均匀分配到可用的GPU上，并为每个GPU创建一个工作线程
    每个工作线程内部使用线程池同时处理多个序列
    """
    # 记录开始时间
    start_time = time.time()

    # 解析GPU ID列表
    gpu_ids: List[int] = [int(gpu.strip()) for gpu in use_gpu.split(",")]

    # 获取所有需要处理的序列路径
    sequence_path_list: List[str] = get_dataset_dir_list(
        dataset_dir_path=base_dir, depth=1
    )

    print(f"找到 {len(sequence_path_list)} 个需要处理的序列目录")

    # 初始化全局进度条
    global progress_bar, total_tasks
    total_tasks = len(sequence_path_list)
    progress_bar = tqdm.tqdm(total=total_tasks, desc="处理序列进度", unit="seq")

    # 将任务分配到不同的GPU，使用字典存储每个GPU分配的序列
    gpu_tasks: Dict[int, List[str]] = {}
    for i, seq_path in enumerate(sequence_path_list):
        # 使用余数进行任务分配，实现任务均衡
        gpu_index: int = i % len(gpu_ids)
        gpu_id: int = gpu_ids[gpu_index]
        # 为每个GPU创建序列列表
        if gpu_id not in gpu_tasks:
            gpu_tasks[gpu_id] = []
        gpu_tasks[gpu_id].append(seq_path)

    # 显示任务分配情况
    for gpu_id, sequences in gpu_tasks.items():
        print(f"GPU {gpu_id} 分配了 {len(sequences)} 个序列")

    # 为每个GPU启动一个线程
    threads: List[threading.Thread] = []
    for gpu_id, sequences in gpu_tasks.items():
        # 创建并启动线程
        thread = threading.Thread(target=worker_for_gpu, args=(gpu_id, sequences))
        threads.append(thread)
        thread.start()

    # 等待所有GPU的工作线程完成
    for thread in threads:
        thread.join()

    # 确保进度条完成
    progress_bar.close()

    # 计算并显示总运行时间
    end_time = time.time()
    elapsed_time = end_time - start_time
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"总运行时间: {int(hours)}小时 {int(minutes)}分钟 {seconds:.2f}秒")


if __name__ == "__main__":
    main()
