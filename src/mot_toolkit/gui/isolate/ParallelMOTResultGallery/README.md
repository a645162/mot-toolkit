# 多目标跟踪结果并行对比工具

## 功能概述

这是一个基于PySide6的多目标跟踪结果可视化对比工具，支持：

- **多算法并行对比**：可同时加载多个算法的跟踪结果
- **实时可视化**：显示相邻5帧的跟踪结果
- **直观对比**：不同算法结果从上到下垂直排列
- **交互式操作**：支持播放、暂停、停止等控制
- **模块化设计**：分离为配置窗口和预览窗口

## 项目结构

```
ParallelMOTResultGallery/
├── main.py              # 主程序入口
├── README.md           # 说明文档
├── config.json         # 配置文件（自动生成）
├── core/               # 核心模块
│   ├── __init__.py
│   ├── mot_loader.py   # MOT结果加载器
│   ├── video_loader.py # 视频加载器
│   └── mot_parser.py   # MOT结果解析器
└── gui/                # GUI模块
    ├── __init__.py
    ├── config_window.py # 配置窗口
    └── preview_window.py # 预览窗口
```

## 使用方法

### 1. 启动程序

```bash
python main.py
```

### 2. 配置设置

1. 点击"配置设置"按钮打开配置窗口
2. 添加算法结果目录（包含.txt跟踪结果文件）
3. 设置数据集路径（支持DanceTrack格式）
4. 选择要使用的数据集split（train/val/test复选框）
5. 选择要预览的序列

### 3. 开始预览

1. 在主窗口选择序列
2. 点击"开始预览"打开预览窗口
3. 使用播放控制按钮进行操作

## 支持的格式

### 算法结果格式

- 标准MOT格式：frame_id, track_id, x, y, w, h, confidence
- 文件扩展名：.txt
- 文件名：序列名称.txt

### 数据集格式

- DanceTrack格式：

  ```bash
  dataset/
  ├── train/
  │   ├── sequence1/
  │   │   ├── sequence1.mp4
  │   │   └── gt/
  │   └── ...
  ├── val/
  │   ├── sequence1/
  │   │   ├── sequence1.mp4
  │   │   └── gt/
  │   └── ...
  └── test/
      ├── sequence1/
      │   ├── sequence1.mp4
      │   └── gt/
      └── ...
  ```

- 支持多split混合选择，可同时选择train/val/test中的序列进行对比

## 功能特点

### 配置窗口

- 添加/移除算法目录
- 设置数据集路径
- 自动检测可用序列
- 配置持久化保存

### 预览窗口

- 5帧垂直排列显示
- 多算法并行对比
- 实时播放控制
- 跟踪结果可视化（边界框+ID）

## 快捷键

- **空格键**：播放/暂停
- **←/→**：上一帧/下一帧
- **Home**：跳转到第一帧
- **End**：跳转到最后一帧

## 依赖要求

```txt
PySide6>=6.5.0
opencv-python>=4.5.0
numpy>=1.20.0
```

## 示例使用

1. 准备数据：
   - 将不同算法的跟踪结果放在不同目录
   - 确保文件名与序列名称匹配

2. 启动程序：

   ```bash
   python main.py
   ```

3. 配置：
   - 添加算法目录：`/path/to/algorithm1/results/`
   - 设置数据集：`/path/to/dancetrack/`

4. 预览：
   - 选择序列：`dancetrack0001`
   - 开始预览，观察不同算法的效果差异

## 注意事项

- 确保视频文件与跟踪结果文件名称匹配
- 算法结果文件应为标准MOT格式
- 支持的视频格式：.mp4, .avi, .mov, .mkv
