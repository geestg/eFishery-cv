import cv2
import time
import requests
import os
from datetime import datetime

# IP Webcam URL dari HP kamu (cek di app)
IP_WEBCAM_URL = "http://192.168.0.103:8080/video"
SERVER_URL = "http://localhost:5000/upload"  # ganti jika server Docker di IP lain
RECORD_SECONDS = 3 * 60

SAVE_DIR = "recorded_videos"
os.makedirs(SAVE_DIR, exist_ok=True)

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
video_name = f"fish_record_{timestamp}.mp4"
video_path = os.path.join(SAVE_DIR, video_name)

cap = cv2.VideoCapture(IP_WEBCAM_URL)
fps = 20
width = int(cap.get(3))
height = int(cap.get(4))
out = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

print(f"[INFO] Mulai merekam dari IP Webcam selama {RECORD_SECONDS} detik...")
start_time = time.time()

while int(time.time() - start_time) < RECORD_SECONDS:
    ret, frame = cap.read()
    if not ret:
        break
    out.write(frame)
    cv2.imshow("Recording - Tekan Q untuk berhenti", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
out.release()
cv2.destroyAllWindows()

print(f"[INFO] Video selesai disimpan: {video_path}")
print("[INFO] Mengunggah video ke server...")

with open(video_path, "rb") as f:
    response = requests.post(SERVER_URL, files={"file": f})
    print("[SERVER RESPONSE]:", response.text)
