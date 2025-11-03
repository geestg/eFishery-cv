from flask import Flask, render_template, send_from_directory, jsonify, request, send_file, Response
import os
import json
from datetime import datetime

app = Flask(__name__)

# =========================
# PASTIKAN FOLDER PENTING SELALU ADA
# =========================
os.makedirs("static/videos", exist_ok=True)
os.makedirs("static", exist_ok=True)

# =========================
# ROUTE: DASHBOARD
# =========================
@app.route('/')
def dashboard():
    log_path = os.path.join('static', 'results_log.json')
    results_log = []
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            results_log = json.load(f)

    return render_template('dashboard.html', results_log=results_log)


# =========================
# ROUTE: UPLOAD FILE DARI COUNTER.PY
# =========================
@app.route('/upload', methods=['POST'])
def upload_file():
    video = request.files.get('video')
    json_file = request.files.get('json')

    if not video or not json_file:
        return "File video atau JSON tidak ditemukan!", 400

    video_folder = os.path.join('static', 'videos')
    log_path = os.path.join('static', 'results_log.json')

    # Simpan video
    video_path = os.path.join(video_folder, video.filename)
    video.save(video_path)

    # Baca data dari file JSON hasil deteksi
    data = json.load(json_file)
    data["Nama Video"] = video.filename

    # Tambahkan data ke log (append)
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            try:
                log_data = json.load(f)
            except json.JSONDecodeError:
                log_data = []
    else:
        log_data = []

    log_data.insert(0, data)  # hasil terbaru muncul di atas
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=4)

    print(f"[SERVER] Upload sukses: {video.filename}")
    return "Upload sukses!", 200


# =========================
# ROUTE: STREAM VIDEO (fix agar bisa diputar di browser)
# =========================
@app.route('/video/<filename>')
def stream_video(filename):
    path = os.path.join('static', 'videos', filename)
    if not os.path.exists(path):
        return "Video tidak ditemukan", 404

    def generate():
        with open(path, "rb") as f:
            while True:
                data = f.read(1024 * 1024)  # stream per 1 MB
                if not data:
                    break
                yield data

    return Response(generate(), mimetype="video/mp4")


# =========================
# ROUTE: STATIC FILES (backup)
# =========================
@app.route('/static/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory('static/videos', filename)


# =========================
# MAIN APP
# =========================
if __name__ == '__main__':
    # Jalankan Flask agar bisa diakses dari host dan Docker
    app.run(host='0.0.0.0', port=5000)
