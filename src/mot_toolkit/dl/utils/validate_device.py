import torch


def validate_device(device: torch.device) -> tuple:
    """
    Validate the given device object.

    :param
        device (torch.device): The device object to validate.

    :return
        tuple: (is_gpu, available, device_name)
    """
    is_gpu = device.type == 'cuda'
    available = False
    device_name = 'CPU'

    if is_gpu:
        if not torch.cuda.is_available():
            device_name = "CUDA不可用"
        else:
            try:
                # Get the device index
                index = device.index if device.index is not None else 0

                device_count = torch.cuda.device_count()
                if index >= device_count:
                    raise ValueError(f"Device index {index} out of range({device_count})")

                size = 10

                def operate_tensor(tensor1: torch.Tensor, tensor2: torch.Tensor):
                    tensor3 = tensor1.add_(tensor2)
                    tensor4 = tensor1.mul(tensor3)

                    return tensor4

                tensor1_cpu = torch.ones(size).to('cpu')
                tensor2_cpu = torch.ones(size).to('cpu')

                result_cpu = operate_tensor(tensor1_cpu, tensor2_cpu)

                # 测试设备可用性
                tensor1_gpu = torch.ones(10).to(device)
                tensor2_gpu = torch.ones(10).to(device)

                result_gpu = operate_tensor(tensor1_gpu, tensor2_gpu)

                result_device = result_gpu.device
                if (result_device.type != device.type or
                        (device.index is not None and result_device.index != device.index)):
                    raise ValueError("Result Tensor device mismatch")

                result_gpu_cpu = result_gpu.to('cpu')

                if not torch.equal(result_cpu, result_gpu_cpu):
                    raise ValueError("Device operation failed")

                available = True
                device_name = torch.cuda.get_device_name(index)
            except Exception as e:
                device_name = f"Device Validation Failed: {str(e)}"
    else:
        available = True  # CPU is always available

    return is_gpu, available, device_name


if __name__ == '__main__':
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    result = validate_device(device)

    is_gpu, available, device_name = result

    print(f"是否为GPU: {is_gpu}")
    print(f"是否可用: {available}")
    print(f"设备名称: {device_name}")
