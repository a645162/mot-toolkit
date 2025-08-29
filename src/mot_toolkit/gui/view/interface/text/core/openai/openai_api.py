import base64
import os
import traceback
import io
from typing import Union, Optional, Tuple, Any  # 使用 Python 3.6 兼容的类型标注

# 尝试导入可选的库
try:
    from PIL import Image as PILImage

    PIL_AVAILABLE = True
except ImportError:
    PILImage = None
    PIL_AVAILABLE = False

try:
    import cv2
    import numpy as np

    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    np = None
    CV2_AVAILABLE = False


from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# 定义兼容 Python 3.6 的类型别名
if CV2_AVAILABLE and PIL_AVAILABLE:
    ImageSourceType = Union[str, PILImage.Image, np.ndarray]
elif PIL_AVAILABLE:
    ImageSourceType = Union[str, PILImage.Image]
elif CV2_AVAILABLE:
    ImageSourceType = Union[str, np.ndarray]
else:
    ImageSourceType = str


class OpenAIImageAnalyzer:
    """
    一个使用 OpenAI API (特别是支持视觉的模型) 分析图像内容的工具类。
    支持文件路径、PIL.Image 或 OpenCV (NumPy) 图像作为输入。
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        api_base_url: Optional[str] = None,
        max_tokens: int = 300,
    ):
        # type: (...) -> None
        """
        初始化 OpenAIImageAnalyzer。

        Args:
            api_key: 您的 OpenAI API 密钥。
            model: 要使用的 OpenAI 模型 (例如 "gpt-4o")。
            api_base_url: OpenAI API 的基础 URL (可选)。
            max_tokens: 生成回答的最大 token 数量。
        """
        if not api_key or api_key == "YOUR_OPENAI_API_KEY":
            raise ValueError("必须提供有效的 OpenAI API 密钥。")
        self.api_key = api_key
        self.model = model
        self.api_base_url = api_base_url
        self.max_tokens = max_tokens
        self._initialize_chat_client()

    def _initialize_chat_client(self):
        # type: () -> None
        """根据配置初始化 LangChain ChatOpenAI 客户端。"""
        chat_params = {
            "model": self.model,
            "openai_api_key": self.api_key,
            "max_tokens": self.max_tokens,
        }
        if self.api_base_url:
            chat_params["base_url"] = self.api_base_url
        try:
            self.chat = ChatOpenAI(**chat_params)
        except Exception as e:
            print(f"初始化 ChatOpenAI 客户端时出错: {e}")
            traceback.print_exc()
            self.chat = None  # 标记客户端初始化失败

    @staticmethod
    def encode_image(image_source, target_format="JPEG"):
        # type: (ImageSourceType, str) -> Tuple[str, str]
        """
        将多种来源的图片编码为 Base64 字符串和对应的 MIME 类型。

        Args:
            image_source: 图片来源，可以是文件路径 (str)、PIL.Image 对象或 OpenCV 图像 (numpy.ndarray)。
            target_format: 编码的目标格式 (例如 'JPEG', 'PNG')，主要用于 PIL 和 OpenCV 图像。

        Returns:
            一个包含 Base64 编码字符串和 MIME 类型字符串的元组 (base64_string, mime_type)。

        Raises:
            FileNotFoundError: 如果输入是路径且文件不存在。
            TypeError: 如果输入类型不支持或所需库未安装。
            Exception: 其他编码错误。
        """
        mime_type = f"image/{target_format.lower()}"
        img_bytes = None

        if isinstance(image_source, str):
            # 处理文件路径
            try:
                with open(image_source, "rb") as image_file:
                    img_bytes = image_file.read()
                # 尝试从文件扩展名推断 MIME 类型，如果失败则使用 target_format
                ext = os.path.splitext(image_source)[1].lower()
                if ext == ".png":
                    mime_type = "image/png"
                elif ext in [".jpg", ".jpeg"]:
                    mime_type = "image/jpeg"
                elif ext == ".gif":
                    mime_type = "image/gif"
                elif ext == ".webp":
                    mime_type = "image/webp"
                elif ext == ".bmp":
                    mime_type = "image/bmp"
                elif ext in [".tif", ".tiff"]:
                    mime_type = "image/tiff"
                # 如果无法从扩展名确定，则保留 target_format 对应的 mime_type
            except FileNotFoundError:
                print(f"错误：找不到图片文件 {image_source}")
                raise
            except Exception as e:
                print(f"读取图片文件时出错：{e}")
                raise
        elif PIL_AVAILABLE and isinstance(image_source, PILImage.Image):
            # 处理 PIL Image 对象
            try:
                buffer = io.BytesIO()
                # 确保保存格式有效，Pillow 支持 'JPEG', 'PNG' 等
                save_format = (
                    target_format
                    if target_format in ["JPEG", "PNG", "GIF", "WEBP"]
                    else "JPEG"
                )
                mime_type = f"image/{save_format.lower()}"
                # 对于有透明度的图像，保存为 PNG 可能更好
                if image_source.mode in ("RGBA", "LA") or (
                    image_source.mode == "P" and "transparency" in image_source.info
                ):
                    if save_format == "JPEG":  # JPEG 不支持透明度，强制 PNG
                        save_format = "PNG"
                        mime_type = "image/png"
                    image_source.save(buffer, format=save_format)
                else:
                    # 对于没有透明度的图像，可以转换为 RGB 保存为 JPEG
                    if save_format == "JPEG":
                        rgb_image = image_source.convert("RGB")
                        rgb_image.save(buffer, format=save_format)
                    else:
                        image_source.save(buffer, format=save_format)

                img_bytes = buffer.getvalue()
            except Exception as e:
                print(f"编码 PIL 图片时出错：{e}")
                raise
        elif CV2_AVAILABLE and isinstance(image_source, np.ndarray):
            # 处理 OpenCV 图像 (NumPy array)
            if cv2 is None:  # 再次检查以防万一
                raise TypeError("OpenCV (cv2) 未安装，无法处理 NumPy 数组图像。")
            try:
                # 确保格式字符串以 '.' 开头，例如 '.jpg'
                encode_param = (
                    [int(cv2.IMWRITE_JPEG_QUALITY), 90]
                    if target_format == "JPEG"
                    else []
                )
                ext = f".{target_format.lower()}"
                success, encoded_image = cv2.imencode(ext, image_source, encode_param)
                if not success:
                    raise ValueError(f"cv2.imencode 无法将图像编码为 {target_format}")
                img_bytes = encoded_image.tobytes()
            except Exception as e:
                print(f"编码 OpenCV 图片时出错：{e}")
                raise
        else:
            supported_types = "str"
            if PIL_AVAILABLE:
                supported_types += ", PIL.Image.Image"
            if CV2_AVAILABLE:
                supported_types += ", numpy.ndarray"
            raise TypeError(
                f"不支持的图片来源类型: {type(image_source)}. 支持的类型: {supported_types}."
            )

        if img_bytes is None:
            raise ValueError("未能成功获取图像字节数据。")

        base64_encoded = base64.b64encode(img_bytes).decode("utf-8")
        return base64_encoded, mime_type

    def ask_question_about_image(self, image_source, question):
        # type: (ImageSourceType, str) -> Optional[str]
        """
        对指定图片进行提问。

        Args:
            image_source: 图片来源，可以是文件路径 (str)、PIL.Image 对象或 OpenCV 图像 (numpy.ndarray)。如果为 None，则只提问文本。
            question: 关于图片的问题。

        Returns:
            模型的回答字符串，如果出错则返回 None。
        """
        if not self.chat:
            print("错误：ChatOpenAI 客户端未成功初始化。无法处理请求。")
            return None
        try:
            if image_source is None:
                # 只发送文本消息
                message = HumanMessage(content=question)
            else:
                # 使用新的编码方法
                base64_image, mime_type = self.encode_image(image_source)
                image_url = f"data:{mime_type};base64,{base64_image}"

                message = HumanMessage(
                    content=[
                        {"type": "text", "text": question},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ]
                )

            response = self.chat.invoke([message])
            return response.content

        except (FileNotFoundError, TypeError) as te:
            # encode_image 已经处理了打印
            print(f"图像处理错误: {te}")
            return None
        except Exception as e:
            print(f"使用 LangChain 调用 OpenAI API 时出错：{e}")
            print("详细错误信息：")
            traceback.print_exc()
            return None

    def analyze_image(self, image_source, prompt="Describe this image."):
        """
        简单分析图片，返回模型输出。用于可用性测试。
        """
        return self.ask_question_about_image(image_source, prompt)

    def update_config(
        self,
        api_key=None,  # type: Optional[str]
        model=None,  # type: Optional[str]
        api_base_url=None,  # type: Optional[str]
        max_tokens=None,  # type: Optional[int]
    ):
        # type: (...) -> None
        """
        更新分析器的配置并重新初始化客户端。

        Args:
            api_key: 新的 OpenAI API 密钥 (可选)。
            model: 新的 OpenAI 模型 (可选)。
            api_base_url: 新的 OpenAI API 基础 URL (可选)。
            max_tokens: 新的最大 token 数量 (可选)。
        """
        if api_key:
            self.api_key = api_key
        if model:
            self.model = model
        if api_base_url is not None:  # 允许设置为空字符串或 None
            self.api_base_url = api_base_url
        if max_tokens:
            self.max_tokens = max_tokens

        # 重新初始化客户端以应用更改
        self._initialize_chat_client()
