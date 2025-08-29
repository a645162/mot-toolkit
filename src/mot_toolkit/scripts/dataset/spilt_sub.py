import os
import shutil
import concurrent.futures
from tqdm import tqdm

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list


def copy_directory(src_dst_tuple):
    """复制目录函数，包含错误处理"""
    src, dst = src_dst_tuple
    try:
        # 确保目标目录的父目录存在
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        # 如果目标已存在，则删除
        if os.path.exists(dst):
            shutil.rmtree(dst)
        # 复制目录
        shutil.copytree(src, dst)
        return True, f"成功复制: {src} -> {dst}"
    except Exception as e:
        return False, f"复制失败: {src} -> {dst}, 错误: {str(e)}"


def spilt_sub(base_dir, profile, keywords_list_str):
    keywords_list = keywords_list_str.split("\n")
    keywords_list = [i.strip() for i in keywords_list if i.strip()]
    # 去重 提升性能
    keywords_list = list(set(keywords_list))

    dataset_dir = get_dataset_dir_list(dataset_dir_path=base_dir)

    print("All Total: ", len(dataset_dir))
    # print(dataset_dir)

    selected_dir_list = []

    for dir_path in dataset_dir:
        for keywords in keywords_list:
            if keywords in dir_path:
                selected_dir_list.append(dir_path)
                break

    rel_path_list = [os.path.relpath(i, base_dir) for i in selected_dir_list]

    copy_dir_task_list = []
    target_dir = base_dir + "_" + profile
    for rel_path in rel_path_list:
        copy_dir_task_list.append(
            (os.path.join(base_dir, rel_path), os.path.join(target_dir, rel_path))
        )

    # 多线程复制目录（优先创建父目录）
    print(f"开始复制 {len(copy_dir_task_list)} 个目录...")

    # 使用线程池执行复制任务
    max_workers = min(32, os.cpu_count() + 4)  # 根据CPU核心数设置合适的线程数
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 使用tqdm显示进度
        results = list(
            tqdm(
                executor.map(copy_directory, copy_dir_task_list),
                total=len(copy_dir_task_list),
                desc="复制进度",
            )
        )

    # 统计复制结果
    success_count = sum(1 for success, _ in results if success)
    failed_count = len(results) - success_count

    print(f"复制完成: 成功 {success_count}, 失败 {failed_count}")

    # 打印失败的任务
    if failed_count > 0:
        print("以下是失败的任务:")
        for success, message in results:
            if not success:
                print(f"  {message}")


def main():
    profile = "LowLight"
    base_dir = r"/mnt/h/Datasets/MaritimeTrackAllData/LabelMe_River"
    keywords_list_str = """
    """

    spilt_sub(base_dir, profile, keywords_list_str)


if __name__ == "__main__":
    main()
