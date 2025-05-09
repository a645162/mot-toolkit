import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List
from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list

# export NVI_NOTIFY_IGNORE_TASK=1
os.environ["NVI_NOTIFY_IGNORE_TASK"] = "1"

# 配置使用的单个GPU设备ID
use_gpu: str = "0"

# 2.2G per Task
memory_per_task: float = 2.2  # 2.2G
reserved_memory: float = 0.5  # 0.5G
current_available_memory: float = 10  # 当前可用内存
# 计算GPU可同时处理的任务数量
task_count: int = int((current_available_memory - reserved_memory) / memory_per_task)
task_count = 1

if task_count < 1:
    raise ValueError("当前可用内存不足，无法处理任务。请检查内存设置。")


def process_sequence(sequence_path: str) -> None:
    """在指定GPU上处理一个序列

    Args:
        sequence_path: 需要处理的序列路径

    Returns:
        None
    """
    # 复制当前环境变量，以便设置CUDA_VISIBLE_DEVICES
    env = os.environ.copy()
    # 设置当前进程使用的GPU ID
    env["CUDA_VISIBLE_DEVICES"] = use_gpu

    # 获取当前python进程的路径（不是py文件）
    python_executable = sys.executable

    # 构建运行sam_seq.py的命令行参数
    cmd = [
        python_executable,
        "-m",
        "mot_toolkit.scripts.auto.sam.sam_seq",
        sequence_path,
    ]
    # 启动子进程执行序列处理
    subprocess.run(cmd, env=env)


def main() -> None:
    """主函数：在单GPU上处理所有序列

    使用线程池在单个GPU上并行处理多个序列，
    同时控制并发数量以避免内存溢出
    """
    # 记录开始时间
    start_time = time.time()

    # 获取所有需要处理的序列路径
    base_dir: str = r"/home/konghaomin/Datasets/SMD_LabelMe"
    sequence_path_list: List[str] = get_dataset_dir_list(
        dataset_dir_path=base_dir, depth=1
    )

    # 使用线程池在单个GPU上并行处理序列
    with ThreadPoolExecutor(max_workers=task_count) as executor:
        # 提交所有序列处理任务
        futures = [
            executor.submit(process_sequence, seq_path)
            for seq_path in sequence_path_list
        ]

        # 等待所有任务完成并获取结果
        for future in futures:
            future.result()

    # 计算并显示总运行时间
    end_time = time.time()
    elapsed_time = end_time - start_time
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"总运行时间: {int(hours)}小时 {int(minutes)}分钟 {seconds:.2f}秒")


if __name__ == "__main__":
    main()
