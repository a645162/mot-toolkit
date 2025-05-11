import os
import cv2
import argparse
from multiprocessing import Pool
import numpy as np
from typing import List, Tuple, Dict, Any, Optional

"""
跟踪结果文本文件格式示例 (e.g., BV14C4y13752-qtZR69rqL543PVoe_00000000-00000744.txt):

Format:
frame_index,track_id,center_x,center_y,width,height,confidence,class,visibility,unused
(Note: Original comment had center_y, but MOT format usually has x,y,w,h or tl_x, tl_y, w, h.
 Assuming the provided example data uses: frame, id, top_left_x, top_left_y, width, height, conf, class_id, visibility, unused)
Example line:
1,0,247.25921630859375,574.379638671875,412.816162109375,52.2425537109375,1,-1,-1,-1
The example data seems to be: frame, id, tl_x, tl_y, w, h, conf, class_id, visibility, unused
Let's assume the columns are:
0: frame_index (int)
1: track_id (int)
2: bbox_top_left_x (float)
3: bbox_top_left_y (float)
4: width (float)
5: height (float)
6: confidence (float)
7: class (int)
8: visibility (float or int, depends on usage, often float)
9: unused (often int or float)
"""


def parse_args() -> argparse.Namespace:
    """
    解析命令行参数。

    返回:
        argparse.Namespace: 解析后的参数对象。
    """
    parser = argparse.ArgumentParser(description="绘制跟踪结果可视化")
    parser.add_argument(
        "--txt_dir",
        type=str,
        default="/home/konghaomin/me-motr-modify/outputs/MeMOTR_MaritimeTrack_Full_Same_523/val/checkpoint_19_tracker",
        help="包含跟踪结果文本文件的目录路径。",
    )
    parser.add_argument(
        "--seq_dir",
        type=str,
        default="/home/konghaomin/Datasets/MaritimeTrackAllData/Spilt/523/MaritimeTrack/val",
        help="包含原始图像序列的目录路径。",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        help="输出可视化结果的目录路径。默认为: <txt_dir>/plot_img。",
    )
    parser.add_argument(
        "--num_workers",
        type=int,
        default=None,
        help="用于处理的多进程数量。默认为系统CPU核心数。",
    )

    args = parser.parse_args()

    # 如果未指定输出目录，则设置默认输出目录
    if args.output_dir is None:
        args.output_dir = os.path.join(args.txt_dir, "plot_img")

    return args


def generate_colors(num_colors: int) -> List[Tuple[int, int, int]]:
    """
    生成一组视觉上可区分的颜色，用于可视化不同的跟踪ID。

    参数:
        num_colors (int): 需要生成的颜色数量。

    返回:
        List[Tuple[int, int, int]]: 包含BGR颜色元组的列表。
    """
    # 确保至少请求一种颜色
    num_colors = max(1, num_colors)

    colors: List[Tuple[int, int, int]] = []
    for i in range(num_colors):
        # 在HSV颜色空间中生成不同的色调 (H)
        hue = i / num_colors
        # 将饱和度 (S) 和亮度 (V) 设置为较高值，以获得鲜艳的颜色
        hsv_color = np.array(
            [[[hue * 180, 0.8 * 255, 0.9 * 255]]], dtype=np.uint8
        )  # OpenCV HSV H range is 0-179
        # 将HSV颜色转换为BGR颜色
        bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR).flatten()
        colors.append((int(bgr_color[0]), int(bgr_color[1]), int(bgr_color[2])))

    return colors


def draw_bbox(
    img: np.ndarray,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color: Tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2,
) -> None:
    """
    在图像上绘制边界框。

    参数:
        img (np.ndarray): 输入图像 (OpenCV BGR格式)。
        x1 (float): 边界框左上角x坐标。
        y1 (float): 边界框左上角y坐标。
        x2 (float): 边界框右下角x坐标。
        y2 (float): 边界框右下角y坐标。
        color (Tuple[int, int, int], optional): BGR格式的颜色元组。默认为绿色。
        thickness (int, optional): 线条粗细。默认为2。
    """
    # 确保坐标为整数类型，以便OpenCV绘制
    pt1 = (int(round(x1)), int(round(y1)))
    pt2 = (int(round(x2)), int(round(y2)))
    cv2.rectangle(img, pt1, pt2, color, thickness)


def draw_track_id(
    img: np.ndarray,
    track_id: int,
    x: float,
    y: float,
    color: Tuple[int, int, int] = (0, 255, 0),
) -> None:
    """
    在图像上绘制跟踪ID文本。

    参数:
        img (np.ndarray): 输入图像 (OpenCV BGR格式)。
        track_id (int): 要绘制的跟踪ID。
        x (float): 文本绘制位置的左上角x坐标 (通常是边界框的x1)。
        y (float): 文本绘制位置的左上角y坐标 (通常是边界框的y1)。
        color (Tuple[int, int, int], optional): BGR格式的颜色元组。默认为绿色。
    """
    # 确保文本位置坐标为整数
    text_x, text_y = int(round(x)), int(round(y))

    text = f"ID:{track_id}"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    text_thickness = 2

    # 计算文本尺寸以便绘制背景
    (text_width, text_height), baseline = cv2.getTextSize(
        text, font, font_scale, text_thickness
    )

    # 绘制文本背景矩形，以增强可读性
    # 背景矩形的y坐标需要向上偏移，使其位于ID文本的上方
    background_y1 = max(0, text_y - text_height - baseline - 5)  # 确保不超出图像顶部
    background_y2 = text_y - baseline + 5

    cv2.rectangle(
        img,
        (text_x, background_y1),
        (text_x + text_width, background_y2),
        (0, 0, 0),
        cv2.FILLED,
    )  # 使用黑色填充背景

    # 绘制文本
    # 文本的y坐标是基线位置，getTextSize返回的y是相对于基线的文本高度
    cv2.putText(
        img,
        text,
        (text_x, text_y - baseline),  # 文本锚点在左下角
        font,
        font_scale,
        color,
        text_thickness,
        cv2.LINE_AA,  # 抗锯齿以获得更平滑的文本
    )


def process_image(
    img_path: str,
    frame_index: int,
    detections_in_frame: List[List[Any]],
    save_path: str,
    track_id_colors: Dict[int, Tuple[int, int, int]],
) -> None:
    """
    处理单张图像：在其上绘制当前帧的所有检测框和跟踪ID，并保存结果。

    参数:
        img_path (str): 原始图像的路径。
        frame_index (int): 当前图像的帧索引。
        detections_in_frame (List[List[Any]]): 当前帧的所有检测结果列表。
                                                每条检测结果格式: [frame, id, x1, y1, w, h, ...]
        save_path (str): 处理后图像的保存路径。
        track_id_colors (Dict[int, Tuple[int, int, int]]): 跟踪ID到颜色的映射字典。
    """
    # 读取原始图像
    img = cv2.imread(img_path)
    if img is None:
        print(f"警告：无法读取图像 {img_path}，跳过此帧。")
        return

    # 先进行数据验证和预处理
    valid_detections = _validate_detections(detections_in_frame)
    if not valid_detections:
        print(f"警告：帧 {frame_index} 没有有效的检测结果，将保存原始图像。")
        cv2.imwrite(save_path, img)
        return

    # 绘制所有检测结果
    img = _draw_detections(img, valid_detections, track_id_colors)

    # 可选：添加帧信息
    _draw_frame_info(img, frame_index, len(valid_detections))

    # 保存处理后的图像
    cv2.imwrite(save_path, img)


def _validate_detections(detections: List[List[Any]]) -> List[Dict[str, Any]]:
    """
    验证并格式化检测结果，将列表格式转换为更易用的字典格式。

    参数:
        detections (List[List[Any]]): 原始检测结果列表。

    返回:
        List[Dict[str, Any]]: 格式化后的有效检测结果列表。
    """
    valid_detections = []

    for det in detections:
        # 确保检测数据至少包含必要的元素：frame, id, x, y, w, h
        if len(det) < 6:
            continue

        # 提取检测数据
        try:
            detection_dict = {
                "frame_idx": int(det[0]),
                "track_id": int(det[1]),
                "x1": float(det[2]),
                "y1": float(det[3]),
                "width": float(det[4]),
                "height": float(det[5]),
                # 提取可选字段
                "confidence": float(det[6]) if len(det) > 6 else None,
                "class_id": int(det[7]) if len(det) > 7 else None,
                "visibility": float(det[8]) if len(det) > 8 else None,
            }

            # 计算右下角坐标
            detection_dict["x2"] = detection_dict["x1"] + detection_dict["width"]
            detection_dict["y2"] = detection_dict["y1"] + detection_dict["height"]

            # 验证边界框是否合法 (非负宽高)
            if detection_dict["width"] > 0 and detection_dict["height"] > 0:
                valid_detections.append(detection_dict)
        except (ValueError, TypeError) as e:
            # 忽略无效的检测数据
            continue

    return valid_detections


def _draw_detections(
    img: np.ndarray,
    detections: List[Dict[str, Any]],
    track_id_colors: Dict[int, Tuple[int, int, int]],
) -> np.ndarray:
    """
    在图像上绘制所有检测结果。

    参数:
        img (np.ndarray): 输入图像。
        detections (List[Dict[str, Any]]): 格式化后的检测结果列表。
        track_id_colors (Dict[int, Tuple[int, int, int]]): 跟踪ID到颜色的映射。

    返回:
        np.ndarray: 绘制了检测结果的图像。
    """
    # 创建图像副本，避免修改原始图像
    result_img = img.copy()

    for det in detections:
        track_id = det["track_id"]
        x1, y1 = det["x1"], det["y1"]
        x2, y2 = det["x2"], det["y2"]

        # 获取此跟踪ID对应的颜色
        color = track_id_colors.get(track_id, (255, 0, 255))  # 紫色作为默认备用颜色

        # 绘制边界框
        draw_bbox(result_img, x1, y1, x2, y2, color, thickness=2)

        # 绘制跟踪ID
        draw_track_id(result_img, track_id, x1, y1, color)

        # 可选：显示置信度 (如果有)
        if det.get("confidence") is not None:
            _draw_confidence(result_img, det["confidence"], x1, y2, color)

    return result_img


def _draw_confidence(
    img: np.ndarray, confidence: float, x: float, y: float, color: Tuple[int, int, int]
) -> None:
    """
    在图像上绘制置信度信息。

    参数:
        img (np.ndarray): 输入图像。
        confidence (float): 置信度值。
        x (float): 文本x坐标。
        y (float): 文本y坐标。
        color (Tuple[int, int, int]): 文本颜色。
    """
    # 文本信息
    text = f"{confidence:.2f}"

    # 文本参数
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    thickness = 1

    # 文本位置 (在边界框底部)
    text_x, text_y = int(round(x)), int(round(y + 15))

    # 绘制背景 (提高可读性)
    (text_width, text_height), baseline = cv2.getTextSize(
        text, font, font_scale, thickness
    )
    cv2.rectangle(
        img,
        (text_x, text_y - text_height - baseline - 2),
        (text_x + text_width, text_y + 2),
        (0, 0, 0),
        cv2.FILLED,
    )

    # 绘制文本
    cv2.putText(
        img,
        text,
        (text_x, text_y - baseline),
        font,
        font_scale,
        color,
        thickness,
        cv2.LINE_AA,
    )


def _draw_frame_info(img: np.ndarray, frame_index: int, num_detections: int) -> None:
    """
    在图像上绘制帧信息 (帧索引和检测数量)。

    参数:
        img (np.ndarray): 输入图像。
        frame_index (int): 帧索引。
        num_detections (int): 检测结果数量。
    """
    # 图像尺寸
    h, w = img.shape[:2]

    # 文本信息
    text = f"Frame: {frame_index} | Detections: {num_detections}"

    # 文本参数
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    thickness = 2
    color = (255, 255, 255)  # 白色

    # 获取文本尺寸
    (text_width, text_height), baseline = cv2.getTextSize(
        text, font, font_scale, thickness
    )

    # 确保文本在图像上方且可见
    text_x = 10
    text_y = 30

    # 绘制背景矩形
    cv2.rectangle(
        img,
        (text_x - 5, text_y - text_height - 5),
        (text_x + text_width + 5, text_y + 5),
        (0, 0, 0),
        cv2.FILLED,
    )

    # 绘制文本
    cv2.putText(
        img, text, (text_x, text_y), font, font_scale, color, thickness, cv2.LINE_AA
    )


def parse_mot_line(line: str) -> Optional[List[Any]]:
    """
    解析MOT格式的一行跟踪数据。
    将适当的列转换为正确的类型（整数或浮点数）。

    参数:
        line (str): 从跟踪结果文件中读取的一行字符串。

    返回:
        Optional[List[Any]]: 解析后的数据列表，如果解析失败则返回None。
                               [frame_idx, track_id, x1, y1, w, h, conf, cls, vis, unused]
    """
    parts = line.strip().split(",")
    if len(parts) < 6:  # 至少需要 frame, id, x, y, w, h
        return None
    try:
        # 0: frame_index (int)
        # 1: track_id (int)
        # 2: bbox_top_left_x (float)
        # 3: bbox_top_left_y (float)
        # 4: width (float)
        # 5: height (float)
        # 6: confidence (float) - 可选，但常见
        # 7: class (int) - 可选
        # 8: visibility (float) - 可选
        # 9: unused (any) - 可选

        parsed_data = [
            int(parts[0]),  # frame_index
            int(parts[1]),  # track_id
            float(parts[2]),  # x1
            float(parts[3]),  # y1
            float(parts[4]),  # width
            float(parts[5]),  # height
        ]
        # 处理可选字段
        if len(parts) > 6:
            parsed_data.append(float(parts[6]))  # confidence
        if len(parts) > 7:
            parsed_data.append(int(parts[7]))  # class
        if len(parts) > 8:
            parsed_data.append(float(parts[8]))  # visibility
        if len(parts) > 9:
            parsed_data.append(parts[9])  # unused (保留为字符串或尝试转换为float/int)

        return parsed_data
    except ValueError as e:
        print(f"警告: 解析行 '{line.strip()}' 时发生值错误: {e}")
        return None


def handle_txt(task_args: Tuple[str, str, str]) -> None:
    """
    处理单个跟踪结果文本文件：读取数据，为每个图像帧绘制检测框，并保存结果。

    参数:
        task_args (Tuple[str, str, str]): 包含以下元素的元组:
            - txt_path (str): 跟踪结果文本文件的路径。
            - val_seq_dir_path (str): 包含图像序列的验证集根目录路径。
            - output_dir (str): 可视化结果的输出目录路径。
    """
    txt_path, val_seq_dir_path, output_dir = task_args

    # 跳过特定的汇总文件（如果存在）
    if "pedestrian_summary.txt" in os.path.basename(txt_path):
        print(f"跳过汇总文件: {txt_path}")
        return

    try:
        with open(txt_path, "r") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"错误: 无法读取文件 {txt_path}。原因: {e}")
        return

    # 解析所有行的跟踪数据
    all_detections: List[List[Any]] = []
    for line in lines:
        parsed_line = parse_mot_line(line)
        if parsed_line:
            all_detections.append(parsed_line)

    if not all_detections:
        print(f"警告: 文件 {txt_path} 中没有有效的跟踪数据或解析失败。")
        return

    # 提取文件名（不含扩展名），用于构建图像序列路径和输出子目录
    txt_name = os.path.basename(txt_path)
    txt_name_no_ext = os.path.splitext(txt_name)[0]

    # 构建对应图像序列的目录路径 (通常在 <val_seq_dir_path>/<txt_name_no_ext>/img1)
    seq_img_dir_path = os.path.join(val_seq_dir_path, txt_name_no_ext, "img1")
    if not os.path.isdir(seq_img_dir_path):
        print(f"警告: 图像序列目录不存在: {seq_img_dir_path}，跳过此文本文件。")
        return

    # 获取序列中的所有图像文件，并按名称排序 (确保帧顺序正确)
    try:
        seq_img_files = sorted(
            [
                f
                for f in os.listdir(seq_img_dir_path)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
            ]
        )
    except OSError as e:
        print(f"错误: 无法读取图像序列目录 {seq_img_dir_path} 中的文件列表。原因: {e}")
        return

    if not seq_img_files:
        print(f"警告: 图像序列目录 {seq_img_dir_path} 中没有找到图像文件。")
        return

    # 创建此序列的输出子目录
    current_seq_save_dir = os.path.join(output_dir, txt_name_no_ext)
    os.makedirs(current_seq_save_dir, exist_ok=True)

    # 为此序列中出现的所有唯一跟踪ID生成颜色
    unique_track_ids = sorted(
        list(set(det[1] for det in all_detections))
    )  # det[1] is track_id
    colors_for_ids = generate_colors(len(unique_track_ids))
    track_id_to_color_map: Dict[int, Tuple[int, int, int]] = {
        track_id: colors_for_ids[i % len(colors_for_ids)]
        for i, track_id in enumerate(unique_track_ids)
    }

    # 按帧索引组织检测数据，以方便查找
    detections_by_frame: Dict[int, List[List[Any]]] = {}
    for det in all_detections:
        frame_idx = det[0]  # det[0] is frame_index
        if frame_idx not in detections_by_frame:
            detections_by_frame[frame_idx] = []
        detections_by_frame[frame_idx].append(det)

    # 遍历序列中的每张图像进行处理
    for img_filename in seq_img_files:
        img_path = os.path.join(seq_img_dir_path, img_filename)
        img_name_no_ext = os.path.splitext(img_filename)[0]

        try:
            # 帧索引通常从图像文件名中提取 (例如, "000001.jpg" -> 1)
            frame_index = int(img_name_no_ext)
        except ValueError:
            print(f"警告: 无法从图像文件名 {img_filename} 中提取帧索引，跳过此图像。")
            continue

        # 获取当前帧的检测结果
        current_frame_detections = detections_by_frame.get(frame_index, [])

        # 定义处理后图像的保存路径
        save_img_path = os.path.join(
            current_seq_save_dir, img_filename
        )  # 保存时使用原始图像名

        # 处理单张图像：绘制检测框并保存
        process_image(
            img_path,
            frame_index,
            current_frame_detections,
            save_img_path,
            track_id_to_color_map,
        )

    print(f"已完成序列处理: {txt_name_no_ext}")


def main() -> None:
    """
    主函数：解析参数，获取跟踪结果文件列表，并使用多进程并行处理它们。
    """
    # 解析命令行参数
    args = parse_args()

    # 确保根输出目录存在
    os.makedirs(args.output_dir, exist_ok=True)

    # 获取所有待处理的跟踪结果文本文件
    try:
        txt_files = [f for f in os.listdir(args.txt_dir) if f.lower().endswith(".txt")]
    except OSError as e:
        print(f"错误: 无法读取跟踪结果目录 {args.txt_dir}。原因: {e}")
        return

    if not txt_files:
        print(f"在目录 {args.txt_dir} 中没有找到 .txt 文件。")
        return

    txt_paths = [os.path.join(args.txt_dir, f) for f in txt_files]

    print(f"找到 {len(txt_paths)} 个跟踪结果文件待处理。")
    user_input = input("按 Enter 键继续，或输入 'q' 退出: ")
    if user_input.lower() == "q":
        print("用户选择退出。")
        return
    print("开始处理...")

    # 准备传递给 handle_txt 函数的参数列表 (每个任务一个元组)
    tasks_args_list = [
        (txt_path, args.seq_dir, args.output_dir) for txt_path in txt_paths
    ]

    # 使用多进程池并行处理所有文本文件
    # 如果 args.num_workers 为 None，Pool 会默认使用 os.cpu_count()
    try:
        with Pool(processes=args.num_workers) as pool:
            pool.map(handle_txt, tasks_args_list)
    except Exception as e:
        print(f"多进程处理时发生错误: {e}")
        # 可以在这里添加更详细的错误处理或日志记录

    print(f"所有处理完成。结果已保存到: {args.output_dir}")


if __name__ == "__main__":
    main()
