# https://github.com/DepthAnything/Depth-Anything-V2


"""
Depth-Anything-V2 Demo

Depth-Anything-V2-Small
Depth-Anything-V2-Base
Depth-Anything-V2-Large
Depth-Anything-V2-Giant(Coming soon)
"""

import torch
from transformers import pipeline
from PIL import Image

image_path = "00000030.jpg"
model = "depth-anything/Depth-Anything-V2-Base-hf"

pipe = pipeline(task="depth-estimation", model=model)
image = Image.open(image_path)

output = pipe(image)

# Print output child
# print(output.keys())
predicted_depth = output["predicted_depth"]
print(predicted_depth.shape)
torch.save(predicted_depth, image_path.replace(".jpg", ".depth.pt"))

image_depth = output["depth"]

image_depth.save(image_path.replace(".jpg", ".depth.jpg"))
