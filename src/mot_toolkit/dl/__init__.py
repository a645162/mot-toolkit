from mot_toolkit.utils.logs import get_logger

support_torch = False
support_v8 = False

logger = get_logger()

logger.info("Start Load Init Deep Learning Module")

try:
    import torch

    logger.info(f"torch version: {torch.__version__}")

    support_torch = True
except ImportError:
    logger.info("No torch found!")
except AttributeError:
    logger.info("Cannot get torch version!")

try:
    import ultralytics

    logger.info(f"Ultralytics version: {ultralytics.__version__}")

    support_v8 = True
except ImportError:
    logger.info("No ultralytics found!")
except Exception:
    pass

try:
    from mot_toolkit.dl.common.torch_devices import get_device

    device = get_device()

    logger.info(f"Torch Device: {device}")
except Exception:
    logger.info("Cannot get device!")

if __name__ == "__main__":
    print("Support Torch: ", support_torch)
    print("Support V8: ", support_v8)
