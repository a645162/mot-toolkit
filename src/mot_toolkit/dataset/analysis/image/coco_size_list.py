import os
import cv2
from collections import defaultdict
import concurrent.futures
from tqdm import tqdm
import datetime

profile = "train"
image_dir = r"/datasets/COCO2017/raw/Images"

# 创建输出目录（如果不存在）
output_dir = os.path.join(os.path.dirname(__file__), "outputs")
os.makedirs(output_dir, exist_ok=True)

# 创建带时间戳的输出文件名
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = os.path.join(output_dir, f"coco_sizes_{profile}_{timestamp}.log")
log_file = open(output_file, "w", encoding="utf-8")


# 自定义打印函数，同时输出到控制台和文件
def print_and_save(*args, **kwargs):
    # 打印到控制台
    print(*args, **kwargs)

    # 打印到文件
    end = kwargs.get("end", "\n")
    sep = kwargs.get("sep", " ")
    file_content = sep.join(str(arg) for arg in args) + end
    log_file.write(file_content)
    log_file.flush()  # 立即写入文件


# 定义处理单个图片的函数
def process_image(file_path):
    try:
        img = cv2.imread(file_path)
        if img is not None:
            height, width = img.shape[:2]
            size_key = f"{width}x{height}"
            return size_key
        return None
    except Exception as e:
        print(f"处理图片 {os.path.basename(file_path)} 时出错: {e}")
        return None


dir_path = rf"{image_dir}/{profile}2017"

# 获取所有JPG文件路径
image_files = []
for root, dirs, files in os.walk(dir_path):
    for file in files:
        if file.lower().endswith(".jpg"):
            image_files.append(os.path.join(root, file))

# 初始化一个默认字典用于存储尺寸信息和计数
size_counter = defaultdict(int)

print_and_save(f"多线程处理 {len(image_files)} 张图片...")

with concurrent.futures.ThreadPoolExecutor() as executor:
    # 提交所有任务并显示进度条
    futures = {
        executor.submit(process_image, file_path): file_path
        for file_path in image_files
    }

    for future in tqdm(
            concurrent.futures.as_completed(futures),
            total=len(image_files),
            desc="处理图片",
    ):
        size_key = future.result()
        if size_key:
            size_counter[size_key] += 1

# 按照数量排序
sorted_sizes = sorted(size_counter.items(), key=lambda x: x[1], reverse=True)

# 计算总图片数
total_images = sum(size_counter.values())

# 输出结果
print_and_save("图片尺寸统计（按数量从多到少排序）:")
print_and_save("尺寸\t\t数量\t\t百分比")
print_and_save("-" * 40)
for size, count in sorted_sizes:
    # 计算百分比并保留两位小数
    percentage = round(count / total_images * 100, 2)
    print_and_save(f"{size}\t\t{count}\t\t{percentage}%")

# 输出总统计信息
unique_sizes = len(size_counter)
print_and_save(f"\n总计: {total_images} 张图片, {unique_sizes} 种不同尺寸")
print_and_save(f"结果已保存到: {output_file}")

# 关闭输出文件
log_file.close()
