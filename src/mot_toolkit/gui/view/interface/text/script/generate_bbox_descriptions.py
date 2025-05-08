import argparse
import multiprocessing
import os
import json
from typing import List, Dict

from mot_toolkit.config.hardware import io_cpu_count
from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list
from mot_toolkit.gui.view.interface.text.script.handle import update_bbox_descriptions
from mot_toolkit.gui.view.interface.text.core.openai.openai_api import (
    OpenAIImageAnalyzer,
)

from mot_toolkit.utils.logs import get_logger

logger = get_logger()

# 添加默认的类别映射字典
DEFAULT_CLASS_MAP = {
    "0": "Ship",
    "1": "Cargo Ship",
    "2": "Fishing Boat",
    "3": "Container Ship",
    "4": "Passenger Ship",
    "5": "Island",
    "6": "Buoy",
    "7": "Obstacle",
    "8": "Tugboat",
}

# 工作流程:
# 1. 获取要处理的数据集目录列表
# 2. 根据提供的 API 密钥创建 OpenAIImageAnalyzer 实例
# 3. 启动多进程，每个进程处理一个序列目录
# 4. 每个进程内部使用单线程处理，因为 API 不支持多并发
# 5. 处理完成后汇总结果


def create_analyzers(analyzer_configs: List[tuple]) -> List[OpenAIImageAnalyzer]:
    """
    创建 OpenAIImageAnalyzer 实例

    Args:
        analyzer_configs: 配置元组列表，每个元组包含 (api_key, model, api_base_url, max_tokens)
                         支持不同长度的元组:
                         - 4个元素: (api_key, model, api_base_url, max_tokens)
                         - 3个元素: (api_key, model, api_base_url)
                         - 2个元素: (api_key, model)
                         - 1个元素: (api_key,) - 此时使用默认模型 "gpt-4o"

    Returns:
        OpenAIImageAnalyzer 实例列表，如果创建失败则返回空列表
    """
    analyzers = []
    for config in analyzer_configs:
        try:
            # 解析配置元组（支持不同长度）
            if len(config) >= 4:
                api_key, model, api_base_url, max_tokens = config
            elif len(config) == 3:
                api_key, model, api_base_url = config
                max_tokens = None
            elif len(config) == 2:
                api_key, model = config
                api_base_url = None
                max_tokens = None
            else:
                api_key = config[0]
                model = "gpt-4o"  # 默认模型
                api_base_url = None
                max_tokens = None

            # 创建分析器实例
            analyzer_params = {"api_key": api_key, "model": model}
            if api_base_url:
                analyzer_params["api_base_url"] = api_base_url
            if max_tokens:
                analyzer_params["max_tokens"] = max_tokens

            analyzer = OpenAIImageAnalyzer(**analyzer_params)
            analyzers.append(analyzer)
            logger.info(f"成功创建 OpenAIImageAnalyzer 实例 (model={model})")
        except Exception as e:
            logger.error(f"创建 OpenAIImageAnalyzer 实例时出错: {e}")

    return analyzers


def handle_sequence(args):
    """
    处理单个序列目录

    这是传递给多进程池的worker函数，负责处理单个序列目录的边界框描述生成

    每个进程独立运行，内部使用单线程调用 OpenAI API，避免 API 并发限制

    Args:
        args: 包含以下元素的元组:
              - sequence_dir_path: 序列目录路径
              - sample_count: 外观采样帧数
              - motion_length: 运动分析帧长度
              - analyzer_config: 单个分析器的配置元组
              - class_map: 类别ID到类别名称的映射字典
              - sequence_index: 当前序列索引
              - total_sequences: 总序列数
    """
    sequence_dir_path, sample_count, motion_length, analyzer_config, class_map, sequence_index, total_sequences = args

    # 在每个进程内部创建自己的 OpenAIImageAnalyzer 实例
    # 这样可以避免跨进程共享对象的问题
    analyzer = None
    try:
        # 解析配置元组
        if len(analyzer_config) >= 4:
            api_key, model, api_base_url, max_tokens = analyzer_config
        elif len(analyzer_config) == 3:
            api_key, model, api_base_url = analyzer_config
            max_tokens = None
        elif len(analyzer_config) == 2:
            api_key, model = analyzer_config
            api_base_url = None
            max_tokens = None
        else:
            api_key = analyzer_config[0]
            model = "gpt-4o"  # 默认模型
            api_base_url = None
            max_tokens = None

        # 创建分析器参数
        analyzer_params = {"api_key": api_key, "model": model}
        if api_base_url:
            analyzer_params["api_base_url"] = api_base_url
        if max_tokens:
            analyzer_params["max_tokens"] = max_tokens

        # 创建分析器实例
        analyzer = OpenAIImageAnalyzer(**analyzer_params)

    except Exception as e:
        logger.error(f"创建 OpenAIImageAnalyzer 实例时出错: {e}")
        return

    if not analyzer:
        logger.error(f"无法为序列创建分析器: {sequence_dir_path}")
        return

    sequence_name = os.path.basename(sequence_dir_path)
    print(f"开始处理序列 [{sequence_index+1}/{total_sequences}]: {sequence_name}")

    success = update_bbox_descriptions(
        dataset_dir_path=sequence_dir_path,
        sample_count=sample_count,
        motion_length=motion_length,
        analyzers=[analyzer],  # 只使用一个分析器实例
        class_map=class_map,
    )

    if success:
        print(f"已完成序列 [{sequence_index+1}/{total_sequences}]: {sequence_name}，剩余 {total_sequences-sequence_index-1} 个序列")
    else:
        print(f"处理序列失败 [{sequence_index+1}/{total_sequences}]: {sequence_name}，剩余 {total_sequences-sequence_index-1} 个序列")


def set_process_start_mode():
    """设置多进程启动方式为 'spawn'"""
    try:
        logger.info("尝试设置多进程启动方式为spawn")
        multiprocessing.set_start_method("spawn")
        logger.info("已设置多进程启动方式为spawn")
    except RuntimeError:
        # 如果已经设置过，忽略错误
        pass
    except Exception as e:
        logger.error(f"设置多进程启动方式时出错: {e}")


def generate_descriptions(
    dataset_dir_path: str | List[str],
    process_count: int = 1,
    sample_count: int = 20,
    motion_length: int = 15,
    analyzer_configs: List[tuple] = None,
    class_map: Dict[str, str] = None,
):
    """
    为数据集中的所有边界框生成描述信息

    使用多进程处理多个序列目录，每个进程内部使用单线程处理API调用

    主要协调函数，负责创建分析器配置、分配任务并启动多进程处理

    Args:
        dataset_dir_path: 数据集目录路径或路径列表
        process_count: 进程数
        sample_count: 外观采样帧数
        motion_length: 运动分析帧长度
        analyzer_configs: 分析器配置元组列表，每个元组包含 (api_key, model, api_base_url, max_tokens)
        class_map: 类别ID到类别名称的映射字典
    """
    # 确保多进程使用正确的启动方式
    set_process_start_mode()

    # 转换为列表
    if isinstance(dataset_dir_path, str):
        dataset_dir_path = [dataset_dir_path]

    # 如果没有提供配置，尝试从环境变量获取
    if not analyzer_configs:
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            analyzer_configs = [(api_key, "gpt-4o", None, None)]
        else:
            logger.error(
                "未提供 OpenAI API 密钥配置，请设置 OPENAI_API_KEY 环境变量或提供 API 密钥配置列表"
            )
            return

    # 检验配置有效性
    if not analyzer_configs:
        logger.error("无有效的分析器配置，处理终止")
        return

    # 获取 analyzer 数量
    analyzer_count = len(analyzer_configs)
    logger.info(f"准备了 {analyzer_count} 个分析器配置")

    # 根据进程数和目录数，确定并行度
    process_count = min(process_count, len(dataset_dir_path))
    if process_count > 1:
        logger.info(f"将使用 {process_count} 个进程进行并行处理")
    else:
        logger.info("将使用单进程处理")

    # 记录类别映射信息
    if class_map:
        logger.info(f"加载了 {len(class_map)} 个类别映射")
        for class_id, name in list(class_map.items())[:10]:  # 只打印前10个
            logger.debug(f"类别映射: {class_id} -> {name}")
    else:
        logger.info("未提供类别映射，将使用原始类别ID")
        class_map = {}

    # 准备任务参数，添加序列索引和总数
    total_sequences = len(dataset_dir_path)
    print(f"准备处理 {total_sequences} 个序列")

    args_list = []
    for i, path in enumerate(dataset_dir_path):
        # 分配 analyzer 配置给每个序列目录（轮询分配）
        analyzer_idx = i % analyzer_count
        args_list.append(
            (
                path,
                sample_count,
                motion_length,
                analyzer_configs[analyzer_idx],  # 传递配置而不是实例
                class_map,
                i,  # 序列索引
                total_sequences,  # 总序列数
            )
        )

    logger.info(f"总共需要处理 {total_sequences} 个序列目录")

    # 使用多进程处理序列目录
    if process_count > 1:
        with multiprocessing.Pool(processes=process_count) as pool:
            # 处理所有序列
            pool.map(handle_sequence, args_list)
    else:
        # 单进程处理
        for args in args_list:
            handle_sequence(args)

    logger.info("所有序列处理完成")
    print(f"\n成功完成所有 {total_sequences} 个序列的处理！")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="为边界框生成描述信息")
    parser.add_argument(
        "--dataset",
        type=str,
        default="/home/konghaomin/Datasets/MaritimeTrackAllData/MT20250319/LabelMe",
        help="数据集目录路径",
    )
    parser.add_argument("--depth", type=int, default=1, help="目录深度")
    parser.add_argument(
        "--threads", type=int, default=io_cpu_count, help="处理线程数"
    )  # 改为threads
    parser.add_argument("--samples", type=int, default=20, help="外观采样帧数")
    parser.add_argument("--motion-length", type=int, default=15, help="运动分析帧长度")
    parser.add_argument("--api-keys", type=str, nargs="+", help="OpenAI API 密钥列表")
    parser.add_argument(
        "--models", type=str, nargs="+", default=["gpt-4o"], help="使用的模型列表"
    )
    parser.add_argument(
        "--api-base-urls", type=str, nargs="+", help="自定义 API 基础 URL 列表"
    )
    parser.add_argument(
        "--max-tokens", type=int, nargs="+", help="最大输出 token 数列表"
    )
    parser.add_argument("--class-map", type=str, help="类别ID到名称的映射JSON文件路径")

    args = parser.parse_args()

    # 获取数据集目录列表
    sequence_path_list = get_dataset_dir_list(
        dataset_dir_path=args.dataset, depth=args.depth
    )

    print(f"找到 {len(sequence_path_list)} 个序列目录")

    # 加载类别映射
    class_map = {}
    if args.class_map:
        if os.path.exists(args.class_map):
            try:
                with open(args.class_map, "r", encoding="utf-8") as f:
                    class_map = json.load(f)
                print(f"成功从文件加载了 {len(class_map)} 个类别映射")
            except Exception as e:
                print(f"加载类别映射文件失败: {e}")
                class_map = DEFAULT_CLASS_MAP.copy()
                print(f"使用默认类别映射: {len(class_map)} 个类别")
        else:
            print(f"类别映射文件 '{args.class_map}' 不存在")
            class_map = DEFAULT_CLASS_MAP.copy()
            print(f"使用默认类别映射: {len(class_map)} 个类别")
    else:
        print("未提供类别映射，将使用默认类别映射")
        class_map = DEFAULT_CLASS_MAP.copy()
        print(f"使用默认类别映射: {len(class_map)} 个类别")

    # 输出类别映射信息
    if class_map:
        print("类别映射列表:")
        for class_id, name in list(class_map.items())[:10]:  # 只显示前10个
            print(f"  - {class_id}: {name}")
        if len(class_map) > 10:
            print(f"  - ... 以及其他 {len(class_map) - 10} 个类别")

    input("按回车键继续...")

    # 构建分析器配置
    analyzer_configs = []
    if args.api_keys:
        # 确定配置长度
        n_configs = len(args.api_keys)
        models = args.models * n_configs if len(args.models) == 1 else args.models
        urls = args.api_base_urls if args.api_base_urls else [None] * n_configs
        tokens = args.max_tokens if args.max_tokens else [None] * n_configs

        # 确保所有列表长度一致
        models = models[:n_configs]  # 截断过长的列表
        while len(models) < n_configs:  # 扩展过短的列表
            models.append("gpt-4o")

        urls = urls[:n_configs]
        while len(urls) < n_configs:
            urls.append(None)

        tokens = tokens[:n_configs]
        while len(tokens) < n_configs:
            tokens.append(None)

        # 创建配置元组
        for i in range(n_configs):
            analyzer_configs.append((args.api_keys[i], models[i], urls[i], tokens[i]))

    print("开始生成边界框描述信息...")
    generate_descriptions(
        dataset_dir_path=sequence_path_list,
        process_count=args.threads,  # 使用线程数参数
        sample_count=args.samples,
        motion_length=args.motion_length,
        analyzer_configs=analyzer_configs,
        class_map=class_map,
    )
    print("边界框描述信息生成完成！")
