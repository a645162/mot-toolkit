import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path
from typing import Tuple, Union
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import cairosvg
from PIL import Image
import io


def create_tag(
    output_path: str,
    text: str = "TL",
    text_size: int = 40,
    color: str = "#FF0000",
    line_width: float = 5,
    padding: Tuple[float, float, float, float] = (
        5,
        5,
        5,
        5,
    ),  # (top, right, bottom, left)
    fill_color: str = "#FFFFFF",  # 矩形填充颜色，"none"为透明
) -> str:
    """
    创建一个矢量图TAG

    Args:
        output_path (str): 输出文件路径
        text (str): 标签文字，默认"TL"
        text_size (int): 文字大小，默认40
        color (str): 颜色（文字和边框），默认红色
        line_width (float): 边框线宽，默认5
        padding (Tuple[float, float, float, float]): 文字与边框的间距 (top, right, bottom, left)，默认(5, 5, 5, 5)
        fill_color (str): 矩形填充颜色，"none"为透明，默认"#FFFFFF"

    Returns:
        str: 输出文件路径
    """
    # 解包padding参数
    pad_top, pad_right, pad_bottom, pad_left = padding

    # 第一步：创建临时图形获取文字的精确尺寸
    fig_temp, ax_temp = plt.subplots()
    text_obj = ax_temp.text(
        0, 0, text, fontsize=text_size, weight="bold", family="monospace"
    )

    # 获取文字的实际边界框
    fig_temp.canvas.draw()
    bbox = text_obj.get_window_extent(renderer=fig_temp.canvas.get_renderer())

    # 转换为点单位
    text_width_pt = bbox.width
    text_height_pt = bbox.height

    # 转换为数据单位（72 points = 1 inch）
    dpi = fig_temp.dpi
    text_width = text_width_pt * 72 / dpi
    text_height = text_height_pt * 72 / dpi

    plt.close(fig_temp)

    # 计算矩形尺寸
    rect_width = text_width + pad_left + pad_right
    rect_height = text_height + pad_top + pad_bottom

    # 创建最终的TAG矢量图
    fig, ax = plt.subplots(figsize=(rect_width / 50, rect_height / 50))
    ax.set_xlim(0, rect_width)
    ax.set_ylim(0, rect_height)
    ax.set_aspect("equal")
    ax.axis("off")

    # 创建填充的矩形
    rect = patches.Rectangle(
        (0, 0),
        rect_width,
        rect_height,
        linewidth=line_width,
        edgecolor=color,
        facecolor=fill_color,  # 使用填充颜色参数
    )
    ax.add_patch(rect)

    # 添加完全居中的文字 - 使用更精确的垂直居中方法
    # 对于大多数字体，文字的视觉中心通常比几何中心稍低一些
    vertical_offset = text_size * 0.08  # 根据字体大小调整偏移量

    ax.text(
        rect_width / 2,
        rect_height / 2 - vertical_offset,  # 向下微调
        text,
        fontsize=text_size,
        color=color,
        ha="center",
        va="center",
        weight="bold",
        family="monospace",
    )

    plt.savefig(
        output_path, format="svg", bbox_inches="tight", pad_inches=0, transparent=True
    )
    plt.close()

    return output_path


def insert_tag_to_image(
    image_path: str,
    tag_svg_path: str,
    output_path: str,
    tag_scale: float = 0.1,
    position: Tuple[float, float] = (0.05, 0.95),
) -> str:
    """
    将SVG标签插入到图片的指定位置

    Args:
        image_path (str): 输入图片路径
        tag_svg_path (str): SVG标签文件路径
        output_path (str): 输出图片路径
        tag_scale (float): 标签缩放比例（相对于图片宽度），默认0.1
        position (Tuple[float, float]): 标签位置 (x, y)，使用相对坐标(0-1)，默认左上角(0.05, 0.95)

    Returns:
        str: 输出文件路径
    """
    # 读取原始图片
    img = mpimg.imread(image_path)
    img_height, img_width = img.shape[:2]

    # 将SVG转换为PNG
    png_data = cairosvg.svg2png(url=tag_svg_path)
    tag_img = Image.open(io.BytesIO(png_data))

    # 计算标签尺寸
    tag_width = int(img_width * tag_scale)
    tag_height = int(tag_img.height * tag_width / tag_img.width)
    tag_img_resized = tag_img.resize((tag_width, tag_height), Image.Resampling.LANCZOS)

    # 创建图形
    fig, ax = plt.subplots(figsize=(img_width / 100, img_height / 100))
    ax.imshow(img)
    ax.axis("off")

    # 计算标签位置
    x_pos = position[0] * img_width
    y_pos = (1 - position[1]) * img_height  # matplotlib的y轴是反向的

    # 添加标签
    imagebox = OffsetImage(tag_img_resized, zoom=1)
    ab = AnnotationBbox(imagebox, (x_pos, y_pos), frameon=False, pad=0)
    ax.add_artist(ab)

    # 保存结果
    plt.savefig(output_path, dpi=100, bbox_inches="tight", pad_inches=0)
    plt.close()

    return output_path


def main() -> None:
    """主函数 - 创建默认TAG"""

    # 创建输出目录
    current_dir: Path = Path(__file__).parent
    output_dir: Path = current_dir / "output" / "tag"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 创建透明背景的TAG
    create_tag(
        output_path=str(output_dir / "tl_transparent.svg"),
        text="TL",
        text_size=40,
        color="#FF0000",
        line_width=5,
        padding=(5, 5, 5, 5),
        fill_color="none",
    )

    # 创建白色背景的TAG
    create_tag(
        output_path=str(output_dir / "tl_white.svg"),
        text="TL",
        text_size=50,
        color="#0000FF",
        line_width=3,
        padding=(8, 10, 8, 10),
        fill_color="#FFFFFF",
    )

    # 创建彩色背景的TAG
    create_tag(
        output_path=str(output_dir / "tl_colored.svg"),
        text="TL",
        text_size=30,
        color="#FFFFFF",
        line_width=2,
        padding=(6, 8, 6, 8),
        fill_color="#00AA00",
    )

    # 示例：将标签插入到图片中（需要提供图片路径）
    # image_path = str(current_dir / "sample_image.jpg")  # 您需要提供实际的图片路径
    # tagged_image_path = str(output_dir / "tagged_image.jpg")
    #
    # if Path(image_path).exists():
    #     insert_tag_to_image(
    #         image_path=image_path,
    #         tag_svg_path=str(output_dir / "tl_white.svg"),
    #         output_path=tagged_image_path,
    #         tag_scale=0.1,
    #         position=(0.05, 0.95)
    #     )
    #     print(f"带标签的图片已保存到: {tagged_image_path}")


if __name__ == "__main__":
    main()
