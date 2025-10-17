import json
import os
import re
import shutil
from collections import defaultdict
from tokenize import group

current_py_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_py_path)


def parse_frame_id_from_filename(fn):
    m = re.search(r"(\d+)", fn)
    if m:
        return int(m.group(1))
    return None


def cocovid2labelme(cocovid_json_path, output_dir):
    """
    将 COCO-VID / COCOVID 风格的标注 JSON 转换为 labelme 风格注释
    cocovid_json_path: 输入 JSON 路径
    output_dir: 输出目录，每张图片一个 labelme json
    """
    with open(cocovid_json_path, "r") as f:
        data = json.load(f)

    images = data.get("images", [])
    annotations = data.get("annotations", [])
    categories = {cat["id"]: cat["name"] for cat in data.get("categories", [])}

    # 构建 image_id -> image info
    imageid_to_info = {img["id"]: img for img in images}

    # 聚合 annotation 为 image_id -> list of ann
    imgid_to_anns = defaultdict(list)
    for ann in annotations:
        img_id = ann.get("image_id")
        bbox = ann.get("bbox")
        cat = ann.get("category_id")
        track_id = ann.get("track_id") or ann.get("instance_id")
        if img_id is None or bbox is None or cat is None:
            continue
        imgid_to_anns[img_id].append(
            {
                "bbox": bbox,
                "category_id": cat,
                "category_name": categories.get(cat, str(cat)),
                "track_id": track_id,
            }
        )

    os.makedirs(output_dir, exist_ok=True)

    for img_id, img in imageid_to_info.items():
        file_name = img.get("file_name")
        height = img.get("height")
        width = img.get("width")
        shapes = []
        for ann in imgid_to_anns.get(img_id, []):
            x, y, w, h = ann["bbox"]
            label = ann["category_name"]
            track_id = ann["track_id"]
            # labelme bbox: [x1, y1], [x2, y2]
            shapes.append(
                {
                    "label": f"{label}_{track_id}",
                    "points": [[x, y], [x + w, y + h]],
                    "group_id": track_id,
                    "shape_type": "rectangle",
                    "flags": {},
                }
            )
        labelme_json = {
            "version": "5.0.1",
            "flags": {},
            "shapes": shapes,
            "imagePath": file_name,
            "imageHeight": height,
            "imageWidth": width,
        }
        out_path = os.path.join(output_dir, os.path.splitext(file_name)[0] + ".json")
        with open(out_path, "w") as fw:
            json.dump(labelme_json, fw, indent=2, ensure_ascii=False)

    print("转换完毕,输出目录:", output_dir)


def organize_images_by_foldername(images, src_img_root, dst_root):
    """
    将 images 按 source.folder_name 分目录，重命名为8位数字.jpg
    images: COCO images 列表
    src_img_root: 原始图片根目录
    dst_root: 输出根目录
    """
    for img in images:
        folder = img.get("source", {}).get("folder_name")
        frame_no = img.get("source", {}).get("frame_no")
        file_name = img.get("file_name")
        file_name = file_name.replace(".png", ".jpg")
        if folder is None or frame_no is None or file_name is None:
            continue
        dst_dir = os.path.join(dst_root, folder)
        os.makedirs(dst_dir, exist_ok=True)
        new_name = f"{int(frame_no):08d}.jpg"
        src_path = os.path.join(src_img_root, file_name)
        dst_path = os.path.join(dst_dir, new_name)
        # 拷贝图片
        if os.path.exists(src_path):
            shutil.copy2(src_path, dst_path)
        else:
            print(f"Warning: {src_path} not found, skip.")


def coco2labelme_and_images(
    cocovid_json_path,
    src_img_root,
    output_dir,
    save_images=True,
    save_jsons=True,
    filter_folders=None,
):
    """
    按序列分目录，将图片和 labelme 标注 json 都输出到同一个目录，文件名为8位帧号
    cocovid_json_path: 输入 JSON 路径
    src_img_root: 原始图片根目录
    output_dir: 输出根目录
    save_images: 是否输出图片
    save_jsons: 是否输出json
    filter_folders: 只处理指定的序列（folder_name），为空则处理全部
    """
    with open(cocovid_json_path, "r") as f:
        data = json.load(f)

    images = data.get("images", [])
    annotations = data.get("annotations", [])
    if annotations is None:  # 如果 annotations 为 None，设置为空列表
        annotations = []
    categories = {cat["id"]: cat["name"] for cat in data.get("categories", [])}

    # 构建 image_id -> image info
    imageid_to_info = {img["id"]: img for img in images}

    # 聚合 annotation 为 image_id -> list of ann
    imgid_to_anns = defaultdict(list)
    for ann in annotations:
        img_id = ann.get("image_id")
        bbox = ann.get("bbox")
        cat = ann.get("category_id")
        track_id = ann.get("track_id") or ann.get("instance_id")
        if img_id is None or bbox is None or cat is None:
            continue
        imgid_to_anns[img_id].append(
            {
                "bbox": bbox,
                "category_id": cat,
                "category_name": categories.get(cat, str(cat)),
                "track_id": track_id,
            }
        )

    # 过滤模式
    if filter_folders is not None and len(filter_folders) > 0:
        filter_set = set(filter_folders)
    else:
        filter_set = None

    for img_id, img in imageid_to_info.items():
        folder = img.get("source", {}).get("folder_name")
        frame_no = img.get("source", {}).get("frame_no")

        file_name = img.get("file_name")
        file_name_jpg = file_name.replace(".png", ".jpg")

        height = img.get("height")
        width = img.get("width")

        if folder is None or frame_no is None or file_name_jpg is None:
            continue

        # 过滤
        if filter_set is not None and folder not in filter_set:
            continue

        seq_dir = os.path.join(output_dir, folder)
        os.makedirs(seq_dir, exist_ok=True)

        new_img_name = f"{int(frame_no):08d}.jpg"
        new_json_name = f"{int(frame_no):08d}.json"

        src_img_path = os.path.join(src_img_root, file_name_jpg)

        dst_img_path = os.path.join(seq_dir, new_img_name)
        dst_json_path = os.path.join(seq_dir, new_json_name)

        # 拷贝图片
        if save_images:
            if os.path.exists(src_img_path):
                shutil.copy2(src_img_path, dst_img_path)
            else:
                print(f"Warning: {src_img_path} not found, skip.")

        # 生成 labelme json
        if save_jsons:
            shapes = []
            for ann in imgid_to_anns.get(img_id, []):
                x, y, w, h = ann["bbox"]
                label = ann["category_name"]
                track_id = ann["track_id"]
                group_id = ann["category_id"]
                shapes.append(
                    {
                        "label": f"{track_id}",
                        "points": [[x, y], [x + w, y + h]],
                        "group_id": f"{group_id}",
                        "shape_type": "rectangle",
                        "flags": {},
                    }
                )
            labelme_json = {
                "version": "5.8.3",
                "flags": {},
                "shapes": shapes,
                "imagePath": new_img_name,
                "imageHeight": height,
                "imageWidth": width,
                "imageData": None,  # 不嵌入图片数据
            }
            with open(dst_json_path, "w") as fw:
                json.dump(labelme_json, fw, indent=2, ensure_ascii=False)

    print("转换完毕,输出目录:", output_dir)


if __name__ == "__main__":
    # 适用于微调标注的结构/数据风格
    handle_images = False

    handle_spilt = []
    handle_spilt = ["train", "val", "test"]
    # handle_spilt = ["val"]

    print("Handle Spilt:", handle_spilt)

    if "train" in handle_spilt:
        coco2labelme_and_images(
            cocovid_json_path=os.path.join(
                current_dir, "instances_train_objects_in_water.json"
            ),
            src_img_root=r"E:\Downloads\SeaDronesSee_MOT_jpg_compressed\train",
            output_dir=os.path.join(current_dir, "SeaDronesSee_MOT_LabelMe", "train"),
            save_images=handle_images,  # 控制是否输出图片
            save_jsons=True,  # 控制是否输出json
            filter_folders=[
                # "DJI_0032"
            ],  # 只处理指定序列
        )
    else:
        print("Skip spilt train")
    print("=" * 10)
    if "val" in handle_spilt:
        coco2labelme_and_images(
            cocovid_json_path=os.path.join(
                current_dir, "instances_val_objects_in_water.json"
            ),
            src_img_root=r"E:\Downloads\SeaDronesSee_MOT_jpg_compressed\val",
            output_dir=os.path.join(current_dir, "SeaDronesSee_MOT_LabelMe", "val"),
            save_images=handle_images,  # 控制是否输出图片
            save_jsons=True,  # 控制是否输出json
            filter_folders=[
                # ""
            ],  # 只处理指定序列
        )
    else:
        print("Skip spilt val")
    print("=" * 10)
    if "test" in handle_spilt:
        coco2labelme_and_images(
            cocovid_json_path=os.path.join(
                current_dir, "instances_test_objects_in_water.json"
            ),
            src_img_root=r"E:\Downloads\SeaDronesSee_MOT_jpg_compressed\test",
            output_dir=os.path.join(current_dir, "SeaDronesSee_MOT_LabelMe", "test"),
            save_images=True,  # 控制是否输出图片
            save_jsons=False,  # 控制是否输出json
            filter_folders=[
                # ""
            ],  # 只处理指定序列
        )
    else:
        print("Skip spilt test")
