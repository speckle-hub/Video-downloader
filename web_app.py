from flask import Flask, render_template, request, jsonify, send_from_directory
from core.downloader import Downloader
import threading
import uuid
import os
import re
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__,
    template_folder=os.path.join(base_path, 'templates'),
    static_folder=os.path.join(base_path, 'static'))

DOWNLOAD_DIR = str(Path.home() / "Downloads" / "VideoDownloader")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

tasks = {}


class DownloadTask:
    def __init__(self):
        self.status = "pending"
        self.percent = 0
        self.speed = ""
        self.message = ""
        self.filename = ""

    def to_dict(self):
        return {
            "status": self.status,
            "percent": self.percent,
            "speed": self.speed,
            "message": self.message,
            "filename": self.filename,
        }


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/info', methods=['POST'])
def api_info():
    data = request.get_json()
    url = data.get('url', '').strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        d = Downloader()
        info = d.get_info(url)
        title = info.get('title', 'Unknown')
        duration = info.get('duration', 0)
        uploader = info.get('uploader', info.get('channel', 'Unknown'))
        mins, secs = divmod(int(duration), 60)
        hrs, mins = divmod(mins, 60)
        dur_str = f"{hrs}h {mins}m {secs}s" if hrs else f"{mins}m {secs}s"
        raw_formats = info.get('formats', [])

        seen = set()
        formats = []
        for f in raw_formats:
            fid = f.get('format_id', '?')
            height = f.get('height', 0) or 0
            width = f.get('width', 0) or 0
            vcodec = f.get('vcodec', 'none')
            acodec = f.get('acodec', 'none')
            fps = f.get('fps') or ''
            filesize = f.get('filesize', 0) or 0

            if vcodec == 'none' and acodec == 'none':
                continue

            dedup = (fid, height, width)
            if dedup in seen:
                continue
            seen.add(dedup)

            if vcodec != 'none':
                if width and height:
                    res = f"{width}x{height}"
                elif not height:
                    res = "Audio only"
                else:
                    res = f"{height}p"
            else:
                res = f"Audio {f.get('abr', 0):.0f}k" if f.get('abr', 0) else "Audio only"

            note = ""
            if vcodec != 'none' and acodec != 'none':
                note = "Video+Audio"
            elif vcodec != 'none':
                note = "Video only"
            elif acodec != 'none':
                note = "Audio only"

            formats.append({
                "id": fid,
                "resolution": res,
                "vcodec": vcodec if vcodec != 'none' else '-',
                "acodec": acodec if acodec != 'none' else '-',
                "fps": str(fps) if fps else '',
                "filesize": filesize,
                "note": note,
            })

        return jsonify({
            "title": title,
            "uploader": uploader,
            "duration_str": dur_str,
            "format_count": len(formats),
            "formats": formats,
            "webpage_url": info.get('webpage_url', url),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/download', methods=['POST'])
def api_download():
    data = request.get_json()
    url = data.get('url', '').strip()
    mode = data.get('mode', 'best')
    format_id = data.get('format_id')

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    task_id = str(uuid.uuid4())
    task = DownloadTask()
    tasks[task_id] = task

    def hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            if total:
                task.percent = int(downloaded / total * 100)
            speed = d.get('speed', 0)
            if speed:
                task.speed = f"{speed / 1024:.0f} KB/s"
            task.status = "downloading"
        elif d['status'] == 'finished':
            task.percent = 100
            task.status = "processing"

    def run():
        try:
            downloader = Downloader(download_dir=DOWNLOAD_DIR)
            downloader.on_progress(hook)

            if mode == 'audio':
                downloader.download_audio(url)
            elif mode == 'photo':
                downloader.download_thumbnail(url)
            elif mode == 'mp4':
                downloader.download_mp4(url)
            elif mode == 'best':
                downloader.download_best_video(url)
            else:
                downloader.download(url, format_spec=format_id)

            task.status = "complete"
            task.message = "Download complete!"
            downloader.remove_progress_hook(hook)
        except Exception as e:
            task.status = "error"
            task.message = str(e)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    return jsonify({"task_id": task_id})


@app.route('/api/progress/<task_id>')
def api_progress(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({"status": "error", "message": "Task not found"}), 404
    return jsonify(task.to_dict())


def main():
    print(f"Web app starting...")
    print(f"Downloads go to: {DOWNLOAD_DIR}")
    print(f"Open http://127.0.0.1:5000 in your browser")
    print(f"Works on both desktop and mobile (same WiFi)")
    app.run(debug=False, host='0.0.0.0', port=5000)


if __name__ == '__main__':
    main()
