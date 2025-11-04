import os
import json
from PIL import Image
from tqdm import tqdm
from multiprocessing import Pool, Manager, cpu_count

source_dir_path = r"/mnt/d/Datasets/Sea-MOT-Datasets/SeaDronesSee/SeaDronesSee_MOT_LabelMe/"
target_dir_path = r"/mnt/d/Datasets/Sea-MOT-Datasets/SeaDronesSee/SeaDronesSee_MOT_LabelMe_1080p/"
TARGET_WIDTH = 1920

def process_one(args):
    json_path, jpg_path, rel_json_path = args
    # 打开图片
    img = Image.open(jpg_path)
    orig_w, orig_h = img.size
    scale = TARGET_WIDTH / orig_w
    target_h = int(orig_h * scale)
    img_resized = img.resize((TARGET_WIDTH, target_h), Image.LANCZOS)

    # 读取json
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 修改json中的图片尺寸
    if "imageWidth" in data:
        data["imageWidth"] = TARGET_WIDTH
    if "imageHeight" in data:
        data["imageHeight"] = target_h

    # 修改bbox（LabelMe格式通常在shapes字段，points为[[x1,y1],[x2,y2]]）
    if "shapes" in data:
        for shape in data["shapes"]:
            if "points" in shape:
                shape["points"] = [
                    [p[0] * scale, p[1] * scale] for p in shape["points"]
                ]

    # 保存图片和json到目标目录
    target_json_path = os.path.join(target_dir_path, rel_json_path)
    target_img_path = os.path.splitext(target_json_path)[0] + ".jpg"
    os.makedirs(os.path.dirname(target_json_path), exist_ok=True)
    img_resized.save(target_img_path)
    with open(target_json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return 1  # 用于进度计数

def main():
    tasks = []
    for root, _, files in os.walk(source_dir_path):
        for file in files:
            if file.lower().endswith('.json'):
                json_path = os.path.join(root, file)
                jpg_path = os.path.splitext(json_path)[0] + '.jpg'
                if os.path.exists(jpg_path):
                    rel_json_path = os.path.relpath(json_path, source_dir_path)
                    tasks.append((json_path, jpg_path, rel_json_path))

    with Pool(processes=cpu_count()) as pool:
        with tqdm(total=len(tasks), desc="Processing", ncols=100) as pbar:
            for _ in pool.imap_unordered(process_one, tasks):
                pbar.update(1)

if __name__ == "__main__":
    main()
