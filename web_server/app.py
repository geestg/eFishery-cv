from flask import Flask, render_template, send_from_directory, jsonify
import os, json

app = Flask(__name__)

# Pastikan folder penting selalu ada
os.makedirs("static/videos", exist_ok=True)
os.makedirs("static/css", exist_ok=True)

@app.route('/')
def dashboard():
    video_folder = os.path.join('static', 'videos')
    videos = [f for f in os.listdir(video_folder) if f.endswith(('.mp4', '.avi', '.mov'))]

    results_path = os.path.join('static', 'results.json')
    results = {}
    if os.path.exists(results_path):
        with open(results_path) as f:
            results = json.load(f)

    return render_template('dashboard.html', videos=videos, results=results)

@app.route('/api/results')
def api_results():
    results_path = os.path.join('static', 'results.json')
    if os.path.exists(results_path):
        with open(results_path) as f:
            return jsonify(json.load(f))
    return jsonify({})

@app.route('/static/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory('static/videos', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
