import json
import os


def convert_labelme_to_voc(labelme_dir, voc_dir):
    # 首先检查并创建voc格式的文件夹
    if not os.path.exists(voc_dir):
        os.makedirs(voc_dir)

    # 然后遍历labelme格式的文件夹，并将文件转换为voc格式
    for filename in os.listdir(labelme_dir):
        if filename.endswith(".json"):
            # 读取labelme的json文件
            with open(os.path.join(labelme_dir, filename), "r") as f:
                data = json.load(f)
            annotations = data["shapes"]

            # VOC格式的标注文件名为"image_XXXX.xml"，其中XXXX为图像的文件名
            voc_filename = os.path.splitext(filename)[0] + ".xml"
            with open(os.path.join(voc_dir, voc_filename), "w") as f:
                f.write("<annotation>\n")
                f.write("    <folder>{}</folder>\n".format(os.path.split(filename)[0]))
                f.write(
                    "    <filename>{}</filename>\n".format(
                        voc_filename.replace("xml", "jpg")
                    )
                )
                f.write("    <size>\n")
                f.write("        <width>{}</width>\n".format(data["imageWidth"]))
                f.write("        <height>{}</height>\n".format(data["imageHeight"]))
                f.write("        <depth>{}</depth>\n".format(3))
                f.write("    </size>\n")
                for annotation in annotations:
                    f.write("    <object>\n")
                    f.write("        <name>{}</name>\n".format(annotation["label"]))
                    f.write("        <bndbox>\n")
                    f.write(
                        "            <xmin>{}</xmin>\n".format(
                            annotation["points"][0][0]
                        )
                    )
                    f.write(
                        "            <ymin>{}</ymin>\n".format(
                            annotation["points"][0][1]
                        )
                    )
                    f.write(
                        "            <xmax>{}</xmax>\n".format(
                            annotation["points"][1][0]
                        )
                    )
                    f.write(
                        "            <ymax>{}</ymax>\n".format(
                            annotation["points"][1][1]
                        )
                    )
                    f.write("        </bndbox>\n")
                    f.write("    </object>\n")
                f.write("</annotation>")


json_path = r"D:\Dataset\label\json"
voc_path = r"D:\Dataset\label\voc"

convert_labelme_to_voc(json_path, voc_path)
