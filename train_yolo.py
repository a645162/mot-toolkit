from ultralytics import YOLO

# Load a pretrained YOLO model (recommended for training)
model = YOLO("yolo11l.pt")

# Train the model using the 'coco8.yaml' dataset for 3 epochs

devices = [0, 1, 2, 3, 4, 5, 6, 7]

# 16 => 2.2G

batch_each_gpu = 32
batch = len(devices) * batch_each_gpu

results = model.train(
    data="yolo_maritime_track.yaml",
    epochs=500,
    device=devices,
    batch=batch,
    cache=True,
    # patience=100,
    # dropout=0.1,
)
