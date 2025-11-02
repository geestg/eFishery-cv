from flask import Flask, request, render_template, send_from_directory, jsonify
import os
import subprocess
import json
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
DATA_FILE = "fish_data.json"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Load or init JSON data
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'file' not in request.files:
        return "No file uploaded", 400
    file = request.files['file']
    filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_") + file.filename
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)

    # Jalankan YOLO counting otomatis
    subprocess.Popen(["python", "counter_server.py", save_path])

    return f"✅ Video diterima dan sedang diproses: {filename}"

@app.route('/videos')
def list_videos():
    files = sorted(os.listdir(PROCESSED_FOLDER), reverse=True)
    return render_template('videos.html', files=files)

@app.route('/uploads/<path:filename>')
def serve_video(filename):
    return send_from_directory(PROCESSED_FOLDER, filename)

@app.route('/dashboard')
def dashboard():
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    return render_template('dashboard.html', data=data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
