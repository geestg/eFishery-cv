from ultralytics import YOLO
import cv2
import os
import csv
import torch
import time
import json
import requests
import subprocess
from datetime import datetime

# --- FIX untuk PyTorch 2.6 ---
from ultralytics.nn.tasks import DetectionModel
from ultralytics.nn.modules.conv import Conv
from torch.nn.modules.container import Sequential
from torch.nn.modules.conv import Conv2d
from torch.nn.modules.batchnorm import BatchNorm2d
from torch.nn.modules.activation import SiLU
torch.serialization.add_safe_globals([DetectionModel, Sequential, Conv, Conv2d, BatchNorm2d, SiLU])

# =========================
# KONFIGURASI
# =========================
MODEL_PATH = r"D:\eFishery-cv\train_ikan_mas_v1\weights\best.pt"
IP_CAM_URL = "http://172.27.67.108:8080/video"   # IP Webcam HP
SERVER_URL = "http://127.0.0.1:5000/upload"      # endpoint Flask
OUTPUT_FOLDER = "output"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

DURATION = 180          # 3 menit rekam
SAVE_FPS = 10.0         # fps output video (lebih ringan)
FRAME_RESIZE = (640, 480)
CONF_THRESH = 0.45
IOU_THRESH = 0.40

# =========================
# LOAD MODEL YOLOv8
# =========================
print("[INFO] Loading YOLOv8 model...")
model = YOLO(MODEL_PATH)

# =========================
# BUKA STREAM DARI IP CAM
# =========================
cap = cv2.VideoCapture(IP_CAM_URL)
if not cap.isOpened():
    raise Exception("Tidak dapat membuka IP Webcam! Pastikan kamera menyala dan URL benar.")

orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"[INFO] Resolusi IP Cam: {orig_width}x{orig_height}  --> diproses sebagai {FRAME_RESIZE[0]}x{FRAME_RESIZE[1]}")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
video_name = f"fish_{timestamp}.mp4"
output_video_path = os.path.join(OUTPUT_FOLDER, video_name)
csv_path = os.path.join(OUTPUT_FOLDER, f"fish_{timestamp}.csv")

# Gunakan codec H.264 agar bisa diputar di browser
fourcc = cv2.VideoWriter_fourcc(*'avc1')
out = cv2.VideoWriter(output_video_path, fourcc, SAVE_FPS, FRAME_RESIZE)

print(f"[INFO] Mulai merekam dari IP Webcam selama {DURATION/60} menit...")
start_time = time.time()
tracked_ids = set()
font = cv2.FONT_HERSHEY_DUPLEX

# =========================
# CSV LOG
# =========================
with open(csv_path, mode='w', newline='') as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=['Frame', 'Fish_ID', 'Center_X', 'Center_Y'])
    writer.writeheader()

    frame_num = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Frame tidak terbaca dari IP cam, stop.")
            break

        frame_num += 1
        frame_resized = cv2.resize(frame, FRAME_RESIZE)

        # =========================
        # DETEKSI + TRACKING
        # =========================
        results = model.track(
            source=frame_resized,
            persist=True,
            tracker='counter.yaml',
            conf=CONF_THRESH,
            iou=IOU_THRESH,
            verbose=False
        )

        annotated_frame = results[0].plot()
        boxes_obj = results[0].boxes

        if boxes_obj is not None and boxes_obj.id is not None:
            ids = boxes_obj.id.int().tolist()
            boxes = boxes_obj.xyxy.tolist()

            for i, box_id in enumerate(ids):
                x1, y1, x2, y2 = map(int, boxes[i])
                center_x, center_y = int((x1 + x2) / 2), int((y1 + y2) / 2)
                tracked_ids.add(int(box_id))

                writer.writerow({
                    'Frame': frame_num,
                    'Fish_ID': int(box_id),
                    'Center_X': center_x,
                    'Center_Y': center_y
                })

        # =========================
        # OVERLAY INFO (HANYA JUMLAH IKAN)
        # =========================
        cv2.putText(
            annotated_frame,
            f"Jumlah ikan: {len(tracked_ids)}",
            (15, 40),
            font, 0.9, (0, 255, 255), 2, cv2.LINE_AA
        )

        out.write(annotated_frame)
        cv2.imshow("Fish Counting - eFishery Vision", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("[INFO] Dihentikan manual (tombol Q).")
            break

        if time.time() - start_time > DURATION:
            print("[INFO] Rekaman selesai (3 menit).")
            break

cap.release()
out.release()
cv2.destroyAllWindows()

# =========================
# KONVERSI OTOMATIS KE H.264 (JIKA PERLU)
# =========================
converted_path = output_video_path.replace(".mp4", "_web.mp4")
try:
    subprocess.run([
        "ffmpeg", "-y", "-i", output_video_path,
        "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "28", "-pix_fmt", "yuv420p",
        converted_path
    ], check=True)
    os.remove(output_video_path)
    os.rename(converted_path, output_video_path)
    print("[INFO] Video berhasil dikonversi ke format web-compatible (H.264).")
except Exception as e:
    print(f"[WARN] Gagal konversi video ke H.264: {e}")

# =========================
# SIMPAN HASIL COUNTING
# =========================
result_data = {
    "Jumlah Ikan": int(len(tracked_ids)),
    "Ukuran Rata-rata (cm)": "Belum dikalibrasi",
    "Nama Video": video_name,
    "Waktu Deteksi": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

result_json_path = os.path.join(OUTPUT_FOLDER, f"fish_{timestamp}.json")
with open(result_json_path, "w") as f:
    json.dump(result_data, f, indent=4)

print(f"✅ Counting selesai! Video: {output_video_path}")
print(f"📄 Log CSV: {csv_path}")
print(f"🎯 Total ikan: {len(tracked_ids)}")

# =========================
# UPLOAD KE SERVER FLASK
# =========================
try:
    with open(output_video_path, "rb") as video_file, open(result_json_path, "rb") as json_file:
        files = {
            'video': (os.path.basename(output_video_path), video_file, 'video/mp4'),
            'json': (os.path.basename(result_json_path), json_file, 'application/json')
        }
        print("[INFO] Mengirim hasil ke server Flask...")
        response = requests.post(SERVER_URL, files=files)

    if response.status_code == 200:
        print("[✅] Upload sukses ke server Flask!")
    else:
        print(f"[❌] Gagal upload: {response.status_code}, {response.text}")
except Exception as e:
    print(f"[ERROR] Tidak dapat upload ke server: {e}")
