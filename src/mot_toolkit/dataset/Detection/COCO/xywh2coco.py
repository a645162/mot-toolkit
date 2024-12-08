import json


def create_coco_format(data, image_prefix="", category_mapping=None):
    coco_data = {
        "info": {
            "description": "Custom COCO Format for Object Detection",
            "version": "1.0",
            "year": 2023,
            "contributor": "Your Name",
            "date_created": "2023-09-27",
        },
        "licenses": [],
        "images": [],
        "annotations": [],
        "categories": [],
    }

    if category_mapping is None:
        category_mapping = {}

    image_id = 1
    annotation_id = 1

    for line in data:
        image_filename, category, x, y, w, h = line.strip().split()

        if category not in category_mapping:
            category_mapping[category] = len(category_mapping) + 1

        image_info = {
            "id": image_id,
            "file_name": image_prefix + image_filename,
            "width": 0,  # Set the actual image width here
            "height": 0,  # Set the actual image height here
            "date_captured": "",
            "license": 0,
            "coco_url": "",
            "flickr_url": "",
        }

        annotation_info = {
            "id": annotation_id,
            "image_id": image_id,
            "category_id": category_mapping[category],
            "segmentation": [],
            "area": float(w) * float(h),
            "bbox": [float(x), float(y), float(w), float(h)],
            "iscrowd": 0,
        }

        coco_data["images"].append(image_info)
        coco_data["annotations"].append(annotation_info)

        image_id += 1
        annotation_id += 1

    for category, category_id in category_mapping.items():
        category_info = {
            "id": category_id,
            "name": category,
            "supercategory": "object",
        }
        coco_data["categories"].append(category_info)

    return coco_data


if __name__ == "__main__":
    # 读取包含目标检测框信息的文本文件
    with open("your_detection_data.txt", "r") as file:
        detection_data = file.readlines()

    # 设置自定义图像编号前缀和类别映射（如果需要）
    image_prefix = "path/to/images/"
    custom_category_mapping = {"class1": 1, "class2": 2, "class3": 3}

    # 创建COCO格式的数据
    coco_format_data = create_coco_format(
        detection_data, image_prefix, custom_category_mapping
    )

    # 保存为JSON文件
    with open("coco_format.json", "w") as json_file:
        json.dump(coco_format_data, json_file, indent=4)
