import os
import shutil

file_ext = [".mp4"]

source_dir = r"D:\AE\AE20250608\LabelMe_video_select"
used_dir = r"D:\AE\AE20250608\LabelMe_video_select30"

unused_dir = r"D:\AE\AE20250608\LabelMe_video_select104-30"

# 创建未使用文件目录
if os.path.exists(unused_dir):
    shutil.rmtree(unused_dir)

os.makedirs(unused_dir, exist_ok=True)

# 获取源目录中所有指定扩展名的文件
all_files = []
for ext in file_ext:
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.lower().endswith(ext.lower()):
                all_files.append(os.path.join(root, file))

print(f"源目录找到 {len(all_files)} 个文件")

# 获取已使用目录中的文件名列表
used_filenames = set()
if os.path.exists(used_dir):
    for ext in file_ext:
        for root, dirs, files in os.walk(used_dir):
            for file in files:
                if file.lower().endswith(ext.lower()):
                    used_filenames.add(file)

print(f"已使用目录找到 {len(used_filenames)} 个文件")

# 找出未使用的文件（源目录中存在但已使用目录中不存在的文件）
unused_files = []
for file_path in all_files:
    filename = os.path.basename(file_path)
    if filename not in used_filenames:
        unused_files.append(file_path)

# 只移动未使用的文件到指定目录
for file_path in unused_files:
    filename = os.path.basename(file_path)
    dest_path = os.path.join(unused_dir, filename)
    # shutil.move(file_path, dest_path)  # 使用move而不是copy2，直接移动文件
    
    # Copy
    shutil.copy2(file_path, dest_path)  # 使用copy2保留文件元数据
    
    print(f"已复制未使用文件: {filename}")

print("处理完成:")
print(f"- 已使用文件: {len(used_filenames)} 个")
print(f"- 未使用文件: {len(unused_files)} 个")
