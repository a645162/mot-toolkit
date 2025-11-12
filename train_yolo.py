import os
from ultralytics import YOLO

os.environ["HTTPS_PROXY"] = "http://proxy.329509.xyz:7890"

# Load a pretrained YOLO model (recommended for training)

pt_name = "yolov8n.pt"
# pt_name = "yolo11n.pt"

# Remove ext
model_name = os.path.splitext(os.path.basename(pt_name))[0]
print(model_name)

model = YOLO(pt_name)

# Train the model using the 'coco8.yaml' dataset for 3 epochs

devices = [0, 1, 2, 3, 4, 5, 6, 7]

# 16 => 2.2G

batch_each_gpu = 16
batch = len(devices) * batch_each_gpu

dataset = "Dataset/yolo_maritime_track.yaml"
# dataset = "Dataset/yolo_sds.yaml"
# dataset = "Dataset/yolo_mt_sds.yaml"

dataset_name = os.path.splitext(os.path.basename(dataset))[0]
print(dataset_name)

exp_name = dataset_name + "_" + model_name

# exit(0)

results = model.train(
    name=exp_name,
    data=dataset,
    epochs=500,
    device=devices,
    batch=batch,
    cache=False,
    # patience=100,
    # dropout=0.1,
)
