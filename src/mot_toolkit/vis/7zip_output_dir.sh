#!/bin/bash

source_dir=""

# 所在目录 parent_dir
parent_dir=$(dirname "$(realpath "$0")")

# 获取目录名称
source_dir_name=$(basename "$parent_dir")

zip_name="${source_dir_name}.7z"

zip_path="${parent_dir}/${zip_name}"

# 检查是否存在 7z 命令
if ! command -v 7z &> /dev/null; then
	echo "7z command not found. Please install p7zip."
	exit 1
fi

7z a -t7z "$zip_path" "$parent_dir"/*
