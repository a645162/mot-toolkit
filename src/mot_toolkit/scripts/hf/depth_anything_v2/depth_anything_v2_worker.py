import os
import sys
import torch
from PIL import Image
from transformers import pipeline
import glob
from pathlib import Path


def set_process_start_mode():
    """设置进程启动模式，防止多进程竞争"""
    # 这里可以添加一些进程启动的设置，如果需要的话
    os.environ["TOKENIZERS_PARALLELISM"] = "false"


def process_image(image_path, pipe):
    """处理单张图片，生成深度信息并保存为.pt文件"""
    try:
        # 读取图片
        image = Image.open(image_path)

        # 执行深度估计
        output = pipe(image)
        predicted_depth = output["predicted_depth"]

        # 生成并保存深度数据
        depth_path = (
            str(image_path).replace(".jpg", ".depth.pt").replace(".png", ".depth.pt")
        )
        torch.save(predicted_depth, depth_path)

        return True
    except Exception as e:
        print(f"处理图片 {image_path} 时出错: {e}")
        return False


def handle_sequence(
    sequence_dir_path, model_name="depth-anything/Depth-Anything-V2-Base-hf"
):
    """处理序列目录中的所有图片"""
    # 创建深度估计pipeline，只创建一次
    print(f"正在加载模型 {model_name}...")
    pipe = pipeline(task="depth-estimation", model=model_name)
    print(f"模型加载完成")

    # 查找目录中所有图片
    image_paths = []
    for ext in ["jpg", "jpeg", "png"]:
        image_paths.extend(glob.glob(os.path.join(sequence_dir_path, f"*.{ext}")))

    print(f"在 {sequence_dir_path} 中找到 {len(image_paths)} 张图片")

    # 处理每张图片
    for image_path in image_paths:
        print(f"处理图片: {image_path}")
        process_image(image_path, pipe)

    return True


def main():
    """处理单个序列的主函数"""
    if len(sys.argv) < 2:
        print(
            "Usage: python -m mot_toolkit.scripts.hf.depth_anything_v2.depth_anything_v2_worker <sequence_path>"
        )
        return

    set_process_start_mode()
    sequence_path = sys.argv[1]

    # 可以通过命令行参数指定模型
    model_name = "depth-anything/Depth-Anything-V2-Base-hf"
    if len(sys.argv) > 2:
        model_name = sys.argv[2]

    print(f"Processing sequence: {sequence_path} on GPU")
    handle_sequence(sequence_dir_path=sequence_path, model_name=model_name)
    print(f"Finished processing: {sequence_path}")


if __name__ == "__main__":
    main()
