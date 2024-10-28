import torch

from mot_toolkit.utils.logs import get_logger

logger = get_logger()


def get_device():
    device = torch.device('cpu')

    if torch.cuda.is_available():
        device = torch.device('cuda')
        return device

    try:
        import torch_directml

        if torch_directml.is_available():
            dml = torch_directml.device()

            logger.info(f"DirectML Device: {dml}")

            device = dml
    except Exception:
        pass

    return device
