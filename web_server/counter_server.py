from ultralytics import YOLO
import cv2
import sys
import os
import json
from datetime import datetime

video_path = sys.argv[1]
model_path = "train_ikan_mas_v1/weights/best.pt"
output_dir = "processed"
data_file = "fish_data.json"

os.makedirs(output_dir, exist_ok=True)

model = YOLO(model_path)
cap = cv2.VideoCapture(video_path)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))

output_name = os.path.basename(video_path).replace(".mp4", "_processed.mp4")
output_path = os.path.join(output_dir, output_name)
out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

tracked_ids = set()
while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model.predict(frame)
    annotated = results[0].plot()
    detections = results[0].boxes.cls.tolist()
    count = len(detections)

    cv2.putText(annotated, f"Ikan: {count}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)
    out.write(annotated)

cap.release()
out.release()

# Simpan jumlah ikan ke JSON harian
day = datetime.now().strftime("%Y-%m-%d")
data = []
if os.path.exists(data_file):
    with open(data_file, "r") as f:
        data = json.load(f)

# update / tambah data hari ini
found = False
for d in data:
    if d["date"] == day:
        d["fish_count"] += count
        found = True
if not found:
    data.append({"date": day, "fish_count": count})

with open(data_file, "w") as f:
    json.dump(data, f, indent=2)

print(f"✅ Video selesai diproses ({output_path}) — total ikan: {count}")
