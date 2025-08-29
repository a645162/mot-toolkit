import os
import shutil
from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list

base_dir = r"D:\Datasets\MaritimeTrackAllData\LabelMe"

# 获取所有depth=2的目录
depth_2_dirs = get_dataset_dir_list(base_dir, depth=2)


video_name_list = [
    os.path.basename(dir_path) for dir_path in depth_2_dirs if os.path.isdir(dir_path)
]

for video_name in video_name_list:
    print(video_name)

video_source_dir = r"E:\Datasets\shipvideos_original\bilibili"
video_save_dir = r"E:\Datasets\shipvideos_original\bilibili_output"

used_dir = os.path.join(video_save_dir, "used")
unused_dir = os.path.join(video_save_dir, "unused")

os.makedirs(used_dir, exist_ok=True)
os.makedirs(unused_dir, exist_ok=True)


# 获取所有视频文件
def get_video_files(source_dir):
    """获取目录下所有视频文件"""
    video_extensions = [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".m4v"]
    video_files = []

    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if any(file.lower().endswith(ext) for ext in video_extensions):
                video_files.append(os.path.join(root, file))

    return video_files


# 检查视频文件名是否包含视频名称列表中的关键词
def check_video_usage(video_path, video_name_list):
    """检查视频文件名是否包含已使用的关键词"""
    video_filename = os.path.basename(video_path)
    video_name_lower = video_filename.lower()

    for used_name in video_name_list:
        if used_name.lower() in video_name_lower:
            return True, used_name
    return False, None


# 获取所有视频文件
print("正在扫描视频文件...")
all_video_files = get_video_files(video_source_dir)
print(f"找到 {len(all_video_files)} 个视频文件")

# 分类视频文件
used_videos = []
unused_videos = []

for video_path in all_video_files:
    is_used, matched_name = check_video_usage(video_path, video_name_list)
    if is_used:
        used_videos.append((video_path, matched_name))
    else:
        unused_videos.append(video_path)

# 显示分类结果
print("\n" + "=" * 60)
print(f"已使用的视频 ({len(used_videos)} 个):")
print("=" * 60)
for video_path, matched_name in used_videos:
    print(f"  {os.path.basename(video_path)} -> 匹配: {matched_name}")

print("\n" + "=" * 60)
print(f"未使用的视频 ({len(unused_videos)} 个):")
print("=" * 60)
for video_path in unused_videos:
    print(f"  {os.path.basename(video_path)}")

# 请求用户确认
print("\n" + "=" * 60)
confirmation = input("请确认分类结果，按回车继续移动操作，或输入 'n' 取消: ")

if confirmation.lower() != "n":
    print("\n开始移动文件...")

    # 移动已使用的视频
    print(f"正在移动 {len(used_videos)} 个已使用视频到 {used_dir}")
    for i, (video_path, matched_name) in enumerate(used_videos, 1):
        filename = os.path.basename(video_path)
        dest_path = os.path.join(used_dir, filename)
        print(f"  [{i}/{len(used_videos)}] {filename}")
        shutil.move(video_path, dest_path)

    # 移动未使用的视频
    print(f"\n正在移动 {len(unused_videos)} 个未使用视频到 {unused_dir}")
    for i, video_path in enumerate(unused_videos, 1):
        filename = os.path.basename(video_path)
        dest_path = os.path.join(unused_dir, filename)
        print(f"  [{i}/{len(unused_videos)}] {filename}")
        shutil.move(video_path, dest_path)

    print("\n移动完成!")
    print(f"已使用视频: {used_dir}")
    print(f"未使用视频: {unused_dir}")
else:
    print("操作已取消")
