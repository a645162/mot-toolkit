import os
import platform
import subprocess
import sys

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


def is_cpu_device(device: torch.device):
    return str(device.type) == "cpu"


def is_nvidia_device(device: torch.device):
    name = get_device_name(device)

    keywords = ["gtx", "rtx", "tesla", "NVIDIA"]

    for keyword in keywords:
        if keyword.strip().lower() in name.strip().lower():
            return True

    return False


def get_nvidia_version() -> str:
    command = "nvidia-smi --version"
    output = subprocess.check_output(command, shell=True)
    output = output.decode("utf-8").strip()

    return output


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


def get_cpu_name() -> str:
    system = platform.system()
    if system == "Windows":
        try:
            result = subprocess.run(
                ['wmic', 'cpu', 'get', 'Name'],
                capture_output=True, text=True, check=True
            )
            output = result.stdout.strip().split('\n')
            output = [
                line.strip()
                for line in output
                if line.strip() != "" and line.strip() != "Name"
            ]
            return output[0].strip()
        except Exception as e:
            print(f"Error: {e}")
            return ""
    elif system == "Linux":
        try:
            with open('/proc/cpuinfo', 'r') as f:
                lines = f.readlines()
            for line in lines:
                if "model name" in line:
                    return line.split(':')[1].strip()
            return ""
        except Exception as e:
            print(f"Error: {e}")
            return ""
    elif system == "Darwin":  # macOS
        try:
            result = subprocess.run(
                ['sysctl', 'machdep.cpu.brand_string'],
                capture_output=True, text=True, check=True
            )
            output = result.stdout.strip().split(':')
            return output[1].strip()
        except Exception as e:
            print(f"Error: {e}")
            return ""
    else:
        print(f"Unsupported system: {system}")
        return ""


def get_linux_vga_device():
    """
    Get VGA device on Linux
    :return:
    """
    if sys.platform != "linux":
        return "Unknown"

    try:
        command = "lspci | grep VGA"
        output = subprocess.check_output(command, shell=True)
        output = output.decode("utf-8").strip()

        return output
    except Exception:
        return "Unknown"


if __name__ == '__main__':
    device = get_device()

    print("CPU Name:", get_cpu_name())

    print("Device:", device)
    print("Device Type:", device.type)
    print("Is AMD ROCm Device:", is_amd_rocm_device(device))
