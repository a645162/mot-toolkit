import sys

from mot_toolkit.dl.utils.validate_device import validate_device

from mot_toolkit.utils.logs import get_logger

support_torch = False
support_v8 = False

logger = get_logger()

logger.info("Start Load Init Deep Learning Module")

try:
    import torch

    logger.info(f"PyTorch version: {torch.__version__}")

    support_torch = True
except ImportError:
    logger.info("No PyTorch found!")
except AttributeError:
    logger.info("Cannot get PyTorch version!")

try:
    import ultralytics

    logger.info(f"Ultralytics version: {ultralytics.__version__}")

    support_v8 = True
except ImportError:
    logger.info("No ultralytics found!")
except Exception:
    pass

try:
    from mot_toolkit.dl.common.torch_devices import (
        get_cpu_name,
        get_device,
        get_device_index,
        get_device_name,
        is_cpu_device,
        is_nvidia_device,
        get_nvidia_version,
        is_amd_rocm_device,
        get_linux_vga_device
    )

    cpu_name = get_cpu_name()
    logger.info(f"CPU: {cpu_name}")

    device = get_device()

    logger.info(f"Torch Device: {device}")
    if str(device.type) == "cuda":
        device_index = get_device_index(device)
        logger.info(f"  Device Index: {device_index}")

        device_name = get_device_name(device)
        logger.info(f"  Device Name: {device_name}")

        is_cpu = is_cpu_device(device)
        logger.info(f"  CPU Backend: {is_cpu}")

        is_nvidia = is_nvidia_device(device)
        logger.info(f"  NVIDIA Backend: {is_nvidia}")
        if is_nvidia:
            try:
                nvidia_version_str = get_nvidia_version()
                nvidia_version_lines = nvidia_version_str.split("\n")
                for line in nvidia_version_lines:
                    logger.info(f"    - {line}")
            except Exception:
                logger.info("Cannot get NVIDIA version!")

        is_amd = is_amd_rocm_device(device)
        logger.info(f"  AMD ROCm Backend: {is_amd}")

        if sys.platform == "linux":
            try:
                vga_device_str = get_linux_vga_device()
                vga_device_lines = vga_device_str.split("\n")
                if len(vga_device_lines) > 0:
                    logger.info("VGA Device:")
                for line in vga_device_lines:
                    logger.info(f"  - {line}")
            except Exception:
                logger.info("Cannot get VGA device!")

        # Validation
        logger.info("Validation Device:")
        validation_result = validate_device(device)
        is_gpu, available, device_name = validation_result
        logger.info(f"  - Device Name: {device_name}")
        logger.info(f"  - GPU: {is_gpu}")
        logger.info(f"  - Available: {available}")
        if available:
            logger.info("  => Device is available!")
        else:
            logger.info("Cannot use this device!")
            device = torch.device("cpu")
            logger.info(f"  => Switch to CPU: {device}")
except Exception:
    logger.info("Cannot get device!")

if __name__ == "__main__":
    print("Support Torch: ", support_torch)
    print("Support V8: ", support_v8)
