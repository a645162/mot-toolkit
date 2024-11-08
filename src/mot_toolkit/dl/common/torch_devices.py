import os
import platform

import torch

from mot_toolkit.utils.logs import get_logger

logger = get_logger()


def get_recommended_device():
    """
    获取推荐的设备
    :return:
    """
    logger.info("Checking device...")

    if 'Darwin' in platform.system():
        # 如果是macOS系统，则启用Metal后端
        if torch.backends.mps.is_available():
            # Apple Metal可用

            # PYTORCH_ENABLE_MPS_FALLBACK=1
            os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

            logger.info("Metal backend is available.")
            logger.info("Using Apple Metal Backend...")
            return torch.device("mps")
        else:
            print("Metal backend is not available!")
    else:
        if torch.cuda.is_available():
            # CUDA可用
            logger.info("CUDA is available!")
            logger.info("Using NVIDIA CUDA...")
            return torch.device("cuda")
        else:
            # CUDA不可用
            logger.info("CUDA is not available!")

    logger.info("Using CPU...")
    return torch.device("cpu")


def get_device():
    try:
        import torch_directml

        if torch_directml.is_available():
            dml = torch_directml.device()

            logger.info(f"DirectML Device: {dml}")

            return dml
    except Exception:
        pass

    return get_recommended_device()


def get_device_index(device: torch.device):
    """
    Get device index
    :param device:
    :return:
    """
    if str(device.type) == "cuda":
        return device.index

    return -1


def get_device_name(device: torch.device | int):
    """
    Get device name
    :param device:
    :return:
    """
    try:
        if isinstance(device, int):
            return torch.cuda.get_device_name(device)
        if device.type == "cuda":
            return torch.cuda.get_device_name(device.index)
    except Exception:
        pass

    return device.type


def is_amd_rocm_device(device):
    """
    Check if the device is AMD ROCm device
    :param device:
    :return:
    """
    name = get_device_name(device)

    keywords = ["gfx", "AMD"]

    for keyword in keywords:
        if keyword.strip().lower() in name.strip().lower():
            return True

    return False


if __name__ == '__main__':
    device = get_device()

    print("Device:", device)
    print("Device Type:", device.type)
    print("Is AMD ROCm Device:", is_amd_rocm_device(device))
