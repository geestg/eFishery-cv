from ultralytics import YOLO
import cv2
import os
import csv
import torch
from ultralytics.nn.tasks import DetectionModel
from ultralytics.nn.modules.conv import Conv
from torch.nn.modules.container import Sequential
from torch.nn.modules.conv import Conv2d
from torch.nn.modules.batchnorm import BatchNorm2d
from torch.nn.modules.activation import SiLU

# ===== FIX UNTUK PYTORCH 2.6 =====
torch.serialization.add_safe_globals([DetectionModel, Sequential, Conv, Conv2d, BatchNorm2d, SiLU])

# =========================
# KONFIGURASI
# =========================
model_path = r"D:\eFishery-cv\train_ikan_mas_v1\weights\best.pt"
video_path = r"D:\eFishery-cv\efishery_yolov8\videos\mas1.mp4"
output_path = r"D:\eFishery-cv\output\output_tracking_counter.mp4"
csv_path = r"D:\eFishery-cv\output\fish_tracking_log.csv"

os.makedirs(os.path.dirname(output_path), exist_ok=True)

# =========================
# LOAD MODEL
# =========================
print("[INFO] Loading YOLOv8 model with BOTSort (counter.yaml)...")
model = YOLO(model_path)

# =========================
# BUKA VIDEO
# =========================
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print(f"[ERROR] Gagal membuka video: {video_path}")
    exit()

fps = int(cap.get(cv2.CAP_PROP_FPS))
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(f"[INFO] Video terbuka ({width}x{height}, {fps} fps, {total_frames} frame).")

# =========================
# TRACKING
# =========================
tracked_ids = set()
frame_num = 0

# Warna & font modern
font = cv2.FONT_HERSHEY_DUPLEX
color_active = (57, 255, 20)
color_unique = (0, 255, 255)
color_id = (255, 100, 100)
color_box = (255, 60, 60)

# =========================
# CSV LOG
# =========================
with open(csv_path, mode='w', newline='') as csv_file:
    fieldnames = ['Frame', 'Fish_ID', 'Center_X', 'Center_Y']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_num += 1

        results = model.track(source=frame, persist=True, tracker='counter.yaml')
        annotated_frame = results[0].plot()

        margin_x, margin_y = int(width * 0.1), int(height * 0.1)
        cv2.rectangle(annotated_frame, (margin_x, margin_y),
                      (width - margin_x, height - margin_y), (255, 255, 255), 2)

        current_ids = []
        if results[0].boxes.id is not None:
            ids = results[0].boxes.id.int().tolist()
            boxes = results[0].boxes.xyxy.tolist()

            for i, box_id in enumerate(ids):
                x1, y1, x2, y2 = map(int, boxes[i])
                center_x, center_y = int((x1 + x2) / 2), int((y1 + y2) / 2)

                if margin_x < center_x < width - margin_x and margin_y < center_y < height - margin_y:
                    current_ids.append(box_id)
                    tracked_ids.add(box_id)

                    # Buat overlay label semi transparan
                    overlay = annotated_frame.copy()
                    cv2.rectangle(overlay, (x1, y1 - 25), (x1 + 130, y1), color_box, -1)
                    annotated_frame = cv2.addWeighted(overlay, 0.6, annotated_frame, 0.4, 0)

                    cv2.putText(annotated_frame, f"ID {box_id}", (x1 + 5, y1 - 7),
                                font, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color_box, 2)

                    writer.writerow({'Frame': frame_num, 'Fish_ID': box_id,
                                     'Center_X': center_x, 'Center_Y': center_y})

        # ========================
        # MODERN OVERLAY
        # ========================
        cv2.putText(annotated_frame, f"Ikan aktif: {len(current_ids)}", (25, 45),
                    font, 1.0, color_active, 2, cv2.LINE_AA)
        cv2.putText(annotated_frame, f"Ikan unik total: {len(tracked_ids)}", (25, 85),
                    font, 1.0, color_unique, 2, cv2.LINE_AA)

        # Watermark bawah kanan
        cv2.putText(annotated_frame, "eFishery Vision", (width - 240, height - 25),
                    font, 0.7, (180, 255, 255), 2, cv2.LINE_AA)

        out.write(annotated_frame)
        cv2.imshow("Fish Tracking (Counter.yaml) - Tekan Q untuk keluar", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
out.release()
cv2.destroyAllWindows()

print(f"✅ Tracking selesai! Video disimpan di:\n{output_path}")
print(f"📄 Log tracking disimpan di:\n{csv_path}")
print(f"🎯 Total ikan unik terdeteksi: {len(tracked_ids)}")
