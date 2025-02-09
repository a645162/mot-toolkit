from typing import Tuple

import torch


def validate_device(
        device: torch.device,
        use_double_precision: bool = False,
        tensor_size: int = 10
) -> Tuple[bool, bool, str]:
    """
    Validate the given device object.

    :param device: The device object to validate.
    :param use_double_precision: If True, uses double precision (FP64) for computations, otherwise uses single precision (FP32).
    :return: A tuple containing (is_gpu, available, device_name)
    """
    is_gpu = device.type == 'cuda'
    available = False
    device_name = 'CPU'

    if is_gpu:
        if not torch.cuda.is_available():
            device_name = "CUDA unavailable"
        else:
            try:
                # Choose data type based on precision requirement
                dtype = torch.float64 if use_double_precision else torch.float32

                index = device.index if device.index is not None else 0

                def operate_tensor(
                        tensor1: torch.Tensor,
                        tensor2: torch.Tensor
                ) -> torch.Tensor:
                    """
                    Perform some operations on two tensors and return a result tensor.
                    """

                    # Transpose
                    tensor3 = tensor1.cos().sin()
                    tensor4 = tensor2.atan().absolute()

                    # Add
                    tensor5 = tensor1.add(tensor2)
                    tensor6 = tensor3.add(tensor4)

                    # Multiply and Divide
                    tensor7 = tensor5.div(tensor6)
                    tensor8 = tensor5.mul(tensor6)

                    # FFT
                    tensor9 = torch.fft.fft(tensor7)
                    tensor10 = torch.fft.fft(tensor8)

                    # Inverse FFT
                    tensor11 = torch.fft.ifft(tensor9)
                    tensor12 = torch.fft.ifft(tensor10)

                    # Multiply
                    tensor_result = tensor11.mul(tensor12)

                    return tensor_result

                tensor1_cpu = torch.randn(tensor_size, dtype=dtype).to('cpu')
                tensor2_cpu = torch.randn(tensor_size, dtype=dtype).to('cpu')

                result_cpu = operate_tensor(tensor1_cpu, tensor2_cpu)

                tensor1_gpu = tensor1_cpu.clone().to(device=device, dtype=dtype)
                tensor2_gpu = tensor2_cpu.clone().to(device=device, dtype=dtype)

                result_gpu = operate_tensor(tensor1_gpu, tensor2_gpu)

                result_gpu_cpu = result_gpu.to('cpu')

                diff_tensor = result_cpu - result_gpu_cpu
                diff_value = diff_tensor.abs().sum()

                # Adjust tolerance based on precision used
                tolerance = 1e-4 if use_double_precision else 1e-5

                if diff_value > tolerance:
                    raise ValueError(f"Device result is not equal to CPU result({diff_value}>{tolerance})")

                available = True
                device_name = torch.cuda.get_device_name(index)
            except Exception as e:
                device_name = f"Device Validation Failed: {str(e)}"
    else:
        available = True  # CPU is always available

    return is_gpu, available, device_name


if __name__ == '__main__':
    # Determine whether to use GPU or fallback to CPU
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Validate the device and print the results
    result = validate_device(device, use_double_precision=True)

    is_gpu, available, device_name = result

    print(f"Is GPU: {is_gpu}")
    print(f"Is Available: {available}")
    print(f"Device Name: {device_name}")
