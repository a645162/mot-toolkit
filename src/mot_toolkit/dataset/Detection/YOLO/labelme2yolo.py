import json
import os


def json2yolo(path):
    dic = {
        "cargo ship": "0",
        "container ship": "1",
        "fishing boat": "2",
        "passenger ship": "3",
        "island": "4",
        "buoy": "5",
    }  # 类别字典
    data = json.load(open(path, encoding="utf-8"))  # 读取带有中文的文件
    w = data["imageWidth"]  # 获取jaon文件里图片的宽高
    h = data["imageHeight"]
    all_line = ""
    print(path)
    for i in data["shapes"]:
        # 归一化坐标点。并得到cx,cy,w,h
        [[x1, y1], [x2, y2]] = i["points"]
        x1, x2 = x1 / w, x2 / w
        y1, y2 = y1 / h, y2 / h
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        w = abs(x2 - x1)
        h = abs(y2 - y1)

        # 将数据组装成yolo格式
        line = "%s %.4f %.4f %.4f %.4f\n" % (
            dic[i["label"]],
            cx,
            cy,
            w,
            h,
        )  # 生成txt文件里每行的内容
        all_line += line
    # print(all_line)
    filename = path.replace(
        "json", "txt"
    )  # 将path里的json替换成txt,生成txt里相对应的文件路径
    fh = open(filename, "w", encoding="utf-8")
    fh.write(all_line)
    fh.close()


path = r"D:\Dataset\seaship_new\datasets\flotage_island\island"
path_list = os.listdir(path)
path_list2 = [x for x in path_list if ".json" in x]  # 获取所有json文件的路径
for p in path_list2:
    json2yolo(os.path.join(path, p))
