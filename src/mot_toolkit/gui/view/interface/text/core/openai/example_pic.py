import os
import math
import traceback

# 导入新的工具类
try:
    from .openai_api import OpenAIImageAnalyzer
except ImportError:
    from openai_api import OpenAIImageAnalyzer

try:
    from PIL import Image, ImageDraw

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("警告：未找到 Pillow 库 (pip install Pillow)。无法生成测试图片。")

# 建议从环境变量或安全配置中加载 API 密钥
# from dotenv import load_dotenv
# load_dotenv()
# openai_api_key = os.getenv("OPENAI_API_KEY")
# if not openai_api_key:
#     raise ValueError("请设置 OPENAI_API_KEY 环境变量")

# 为了示例，直接使用占位符，实际使用时请替换为真实密钥或环境变量加载
openai_api_key = "YOUR_OPENAI_API_KEY"  # 请替换为您的 API 密钥或使用环境变量加载


def create_complex_test_image(filepath: str, width: int = 300, height: int = 200):
    """
    创建一个包含多种形状的复杂测试图片

    Args:
        filepath: 保存图片的路径
        width: 图像宽度
        height: 图像高度

    Returns:
        创建成功返回 True，否则返回 False

    图像内容:
    - 左上角: 蓝色方块
    - 右上角: 红色圆形
    - 中间: 黄色五角星
    - 底部: 绿色矩形和黑色轮廓椭圆
    """
    if not PIL_AVAILABLE:
        print("错误：需要 Pillow 库来创建测试图片。请运行 'pip install Pillow'")
        return False

    # 创建空白图像
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    # 定义颜色
    red = (255, 0, 0)
    blue = (0, 0, 255)
    green = (0, 128, 0)
    black = (0, 0, 0)
    yellow = (255, 255, 0)

    # 1. 左上角方块 (蓝色)
    square_size = 40
    draw.rectangle(
        [(10, 10), (10 + square_size, 10 + square_size)], fill=blue, outline=black
    )

    # 2. 右上角圆形 (红色)
    circle_radius = 20
    circle_center_x = width - 10 - circle_radius
    circle_center_y = 10 + circle_radius
    draw.ellipse(
        [
            (circle_center_x - circle_radius, circle_center_y - circle_radius),
            (circle_center_x + circle_radius, circle_center_y + circle_radius),
        ],
        fill=red,
        outline=black,
    )

    # 3. 中间五角星 (黄色) - 使用三角函数计算点坐标
    star_center_x = width // 2
    star_center_y = height // 2
    star_radius_outer = 30  # 外接圆半径
    star_radius_inner = star_radius_outer * 0.4  # 内接圆半径，调整为大约 0.4 倍外半径
    star_points = []

    # 计算五角星的十个顶点（5个外顶点，5个内顶点）
    for i in range(5):
        # 外顶点 - 每个角度间隔 72 度(2π/5)
        angle_outer = math.pi / 2 - 2 * math.pi * i / 5  # 从顶部开始，逆时针
        x_outer = star_center_x + star_radius_outer * math.cos(angle_outer)
        y_outer = star_center_y - star_radius_outer * math.sin(angle_outer)
        star_points.append((x_outer, y_outer))

        # 内顶点 - 位于两个外顶点之间
        angle_inner = math.pi / 2 - 2 * math.pi * (i + 0.5) / 5
        x_inner = star_center_x + star_radius_inner * math.cos(angle_inner)
        y_inner = star_center_y - star_radius_inner * math.sin(angle_inner)
        star_points.append((x_inner, y_inner))

    # 绘制五角星
    draw.polygon(star_points, fill=yellow, outline=black)

    # 4. 底部其他图形 (绿色矩形和黑色椭圆)
    bottom_rect_y = height - 40
    # 绿色矩形
    draw.rectangle(
        [(30, bottom_rect_y), (width // 2 - 10, height - 10)], fill=green, outline=black
    )
    # 黑色轮廓椭圆
    draw.ellipse(
        [(width // 2 + 10, bottom_rect_y), (width - 30, height - 10)],
        fill=None,  # 无填充
        outline=black,
        width=2,  # 线条宽度
    )

    # 保存图像到文件
    try:
        img.save(filepath)
        print(f"测试图片已保存到: {filepath}")
        return True
    except Exception as e:
        print(f"保存测试图片时出错：{e}")
        return False


# 示例用法
if __name__ == "__main__":
    """
    测试 OpenAIImageAnalyzer 的使用示例

    工作流程:
    1. 创建测试图片
    2. 初始化 OpenAIImageAnalyzer
    3. 向模型提问关于图片的问题
    4. 展示响应结果
    5. 进行额外测试（如多次提问、更新配置）
    6. 清理测试资源
    """
    test_image_filename = "complex_test_image.jpg"
    image_created = False

    # 尝试创建复杂的测试图片
    if PIL_AVAILABLE:
        image_created = create_complex_test_image(test_image_filename)
    else:
        print("无法创建测试图片，请确保 Pillow 已安装或提供现有图片路径。")

    # 只有在图片成功创建或存在时才继续
    if image_created or (not PIL_AVAILABLE and os.path.exists(test_image_filename)):
        image_path = test_image_filename
        question = "详细描述这张图片中有什么？就是各个位置分别有什么。"
        custom_model = "gpt-4o"  # 可以根据需要改为其他模型
        # 如果需要使用自定义 API URL，请取消注释下一行并设置您的 URL
        # custom_api_url = "YOUR_API_BASE_URL" # 例如 "http://localhost:12345/v1"
        custom_api_url = None  # 默认使用 OpenAI 官方 URL

        # 检查 API 密钥是否已配置
        if openai_api_key == "YOUR_OPENAI_API_KEY":
            print(
                "\n错误：OpenAI API 密钥未配置。请在脚本中设置 `openai_api_key` 或使用环境变量。"
            )
        else:
            try:
                # 示例1: 基本用法 - 初始化分析器并提问
                print("\n=== 示例1: 基本图像分析 ===")
                analyzer = OpenAIImageAnalyzer(
                    api_key=openai_api_key,
                    model=custom_model,
                    api_base_url=custom_api_url,
                )

                # 使用分析器提问
                print(f"向模型 {analyzer.model} 提问: {question}")
                answer = analyzer.ask_question_about_image(image_path, question)

                if answer:
                    print(f"模型: {analyzer.model}")
                    if analyzer.api_base_url:
                        print(f"API URL: {analyzer.api_base_url}")
                    print(f"问题: {question}")
                    print(f"回答: {answer}")
                else:
                    print("未能获取回答。")

                # 示例2: 多次提问同一张图片
                if answer:  # 如果第一次提问成功，再提一个问题
                    print("\n=== 示例2: 多次提问同一张图片 ===")
                    follow_up_question = "图中有几个几何图形？请列出它们的颜色。"
                    print(f"提问: {follow_up_question}")
                    follow_up_answer = analyzer.ask_question_about_image(
                        image_path, follow_up_question
                    )
                    if follow_up_answer:
                        print(f"回答: {follow_up_answer}")
                    else:
                        print("未能获取回答。")

                # 示例3: 更新配置后提问
                if answer:  # 如果提问成功
                    print("\n=== 示例3: 更新配置后提问 ===")
                    print(f"更新配置: max_tokens={100}")
                    analyzer.update_config(
                        max_tokens=100
                    )  # 减小 token 数量，获取更简洁的回答
                    concise_question = "用一句话概括这张图片。"
                    print(f"提问: {concise_question}")
                    concise_answer = analyzer.ask_question_about_image(
                        image_path, concise_question
                    )
                    if concise_answer:
                        print(
                            f"回答 (最大 token={analyzer.max_tokens}): {concise_answer}"
                        )
                    else:
                        print("未能获取回答。")

            except ValueError as ve:  # 捕获初始化时的 API Key 错误
                print(f"初始化错误: {ve}")
            except Exception as e:  # 捕获其他潜在错误
                print(f"运行示例时发生意外错误: {e}")
                traceback.print_exc()

        # 清理创建的测试图片
        if image_created and os.path.exists(test_image_filename):
            try:
                os.remove(test_image_filename)
                print(f"\n已清理测试图片: {test_image_filename}")
            except OSError as e:
                print(f"清理测试图片时出错: {e}")
    elif not PIL_AVAILABLE:
        print("跳过提问，因为 Pillow 不可用且未找到默认测试图片。")
    else:
        print(f"错误：未能创建或找到测试图片 '{test_image_filename}'。")
