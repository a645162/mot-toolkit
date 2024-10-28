from mot_toolkit.utils.logs import get_logger

support_torch = False
support_v8 = False

logger = get_logger()

logger.info("Start Load Init Deep Learning Module")

try:
    import torch

    support_torch = True

    logger.info(f"torch version: {torch.__version__}")
except ImportError:
    logger.info("No torch found!")

try:
    import ultralytics

    logger.info(f"ultralytics version: {ultralytics.__version__}")

    support_v8 = True
except ImportError:
    logger.info("No ultralytics found!")

if __name__ == "__main__":
    print("Support Torch: ", support_torch)
    print("Support V8: ", support_v8)
