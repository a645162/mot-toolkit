#!/bin/bash

# Install vscode "Bash Run Button" extension to run this script easily.

source_dir="/home/konghaomin/mot-toolkit/src/mot_toolkit/vis/plot/output/seq_gt_frames/MT20250319/LabelMe_video"

# 所在目录 parent_dir
parent_dir=$(dirname "$(realpath "${source_dir}")")

# 获取目录名称
source_dir_name=$(basename "$source_dir")

# Time str
time_str=$(date +%Y%m%d_%H%M%S)

zip_name="${source_dir_name}_${time_str}.7z"

zip_path="${parent_dir}/${zip_name}"

# 检查是否存在 7z 命令
if ! command -v 7z &> /dev/null; then
	echo "7z command not found. Please install p7zip."
	exit 1
fi

echo "Compressing directory: $parent_dir"
echo "Output zip file: $zip_path"

7z a -t7z "$zip_path" "$source_dir"/*
