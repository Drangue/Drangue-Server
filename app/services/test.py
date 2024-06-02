from ultralytics import YOLO

# Load a model
model = YOLO("tree.pt")  # load a pretrained model (recommended for training)

# Train the model
results = model.predict("https://sensonomic.com/wp-content/uploads/2018/10/Pexels-aerial-shot-bird-s-eye-view-forest-Square.jpg", imgsz=320, conf=0.1, iou=.15)

# print(bbox[0])
# for result in results:
#     print(
#     break
