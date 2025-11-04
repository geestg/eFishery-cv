from flask import Flask, render_template, send_from_directory, jsonify, request, send_file, Response, redirect, url_for
import os
import json
import re
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
            try:
                results_log = json.load(f)
            except json.JSONDecodeError:
                results_log = []
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
# ROUTE: HAPUS VIDEO + DATA LOG
# =========================
@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    video_folder = os.path.join('static', 'videos')
    log_path = os.path.join('static', 'results_log.json')

    # Hapus file video
    video_path = os.path.join(video_folder, filename)
    if os.path.exists(video_path):
        os.remove(video_path)
        print(f"[SERVER] Video dihapus: {filename}")

    # Hapus data dari results_log.json
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            try:
                log_data = json.load(f)
            except json.JSONDecodeError:
                log_data = []
        # Filter log tanpa data yang dihapus
        log_data = [entry for entry in log_data if entry.get("Nama Video") != filename]
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=4)
        print(f"[SERVER] Log dihapus untuk: {filename}")

    return redirect(url_for('dashboard'))


# =========================
# ROUTE: STREAM VIDEO (support byte-range agar bisa diputar)
# =========================
@app.route('/video/<filename>')
def stream_video(filename):
    video_path = os.path.join('static', 'videos', filename)
    if not os.path.exists(video_path):
        return "Video tidak ditemukan", 404

    range_header = request.headers.get('Range', None)
    if not range_header:
        return send_file(video_path, mimetype='video/mp4')

    # ---- Handle byte-range requests ----
    size = os.path.getsize(video_path)
    byte1, byte2 = 0, None
    m = re.search(r'(\d+)-(\d*)', range_header)
    if m:
        g = m.groups()
        byte1 = int(g[0])
        if g[1]:
            byte2 = int(g[1])

    length = size - byte1
    if byte2 is not None:
        length = byte2 - byte1 + 1

    with open(video_path, 'rb') as f:
        f.seek(byte1)
        data = f.read(length)

    # ---- Response partial stream ----
    rv = Response(data, 206, mimetype='video/mp4', direct_passthrough=True)
    rv.headers.add('Content-Range', f'bytes {byte1}-{byte1 + length - 1}/{size}')
    rv.headers.add('Accept-Ranges', 'bytes')
    rv.headers.add('Content-Length', str(length))
    rv.headers.add('Content-Disposition', f'inline; filename={filename}')  # ✅ FIX UTAMA
    return rv


# =========================
# ROUTE: STATIC FILES (backup)
# =========================
@app.route('/static/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory('static/videos', filename)


# =========================
# TAMBAHAN HEADER (untuk dukung browser caching & seek)
# =========================
@app.after_request
def add_headers(response):
    response.headers['Accept-Ranges'] = 'bytes'
    return response


# =========================
# MAIN APP
# =========================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
