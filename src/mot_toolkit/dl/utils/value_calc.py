def calculate_iou(box1: tuple | list[float], box2: tuple | list[float]) -> float:
    # 解构边界框的坐标
    b1_x1, b1_y1, b1_x2, b1_y2 = box1
    b2_x1, b2_y1, b2_x2, b2_y2 = box2

    # 计算交集的坐标
    inter_x1 = max(b1_x1, b2_x1)
    inter_y1 = max(b1_y1, b2_y1)
    inter_x2 = min(b1_x2, b2_x2)
    inter_y2 = min(b1_y2, b2_y2)

    # 计算交集的面积
    inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)

    # 计算各自边界框的面积
    b1_area = (b1_x2 - b1_x1) * (b1_y2 - b1_y1)
    b2_area = (b2_x2 - b2_x1) * (b2_y2 - b2_y1)

    # 计算并集的面积
    union_area = b1_area + b2_area - inter_area

    # 计算IoU
    iou = inter_area / union_area if union_area > 0 else 0.0

    return iou
