#!/bin/bash

# 安装字体依赖
sudo apt-get update
sudo apt-get install -y fontconfig

# 方法1：如果你有 Times New Roman.ttf 文件
# cp Times\ New\ Roman.ttf ~/.fonts/

# 方法2：自动安装微软核心字体包（包含 Times New Roman）
sudo apt-get install -y ttf-mscorefonts-installer

# 刷新字体缓存
fc-cache -fv

# 检查 Times New Roman 字体是否已安装
echo "检查 Times New Roman 字体安装情况："
fc-list | grep -i "Times New Roman" && echo "✓ Times New Roman 已安装" || echo "✗ Times New Roman 未找到"

echo "Times New Roman 字体安装完成。"
