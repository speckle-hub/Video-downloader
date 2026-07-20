import yt_dlp
import os
import threading
import re
import json
from pathlib import Path


def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name)


class Downloader:
    def __init__(self, download_dir=None):
        self.download_dir = download_dir or str(Path.home() / "Downloads" / "VideoDownloader")
        self._progress_hooks = []
        self._cancel_flag = False
        self.ffmpeg_available = self._check_ffmpeg()

    def on_progress(self, hook):
        self._progress_hooks.append(hook)

    def remove_progress_hook(self, hook):
        if hook in self._progress_hooks:
            self._progress_hooks.remove(hook)

    def _progress_callback(self, d):
        if self._cancel_flag:
            raise Exception("Download cancelled")
        for hook in self._progress_hooks:
            hook(d)

    def cancel(self):
        self._cancel_flag = True

    def reset_cancel(self):
        self._cancel_flag = False

    def get_info(self, url):
        opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    def list_formats(self, url):
        info = self.get_info(url)
        return info.get('formats', [])

    def get_format_string(self, info):
        formats = info.get('formats', [])
        if not formats:
            return 'best'

        has_ffmpeg = self._check_ffmpeg()

        best_single = None
        best_video = None
        best_audio = None
        for f in formats:
            vcodec = f.get('vcodec', 'none')
            acodec = f.get('acodec', 'none')
            height = f.get('height', 0) or 0
            abr = f.get('abr', 0) or 0
            if vcodec != 'none' and acodec != 'none':
                if not best_single or height > (best_single.get('height', 0) or 0):
                    best_single = f
            elif vcodec != 'none':
                if not best_video or height > (best_video.get('height', 0) or 0):
                    best_video = f
            elif acodec != 'none':
                if not best_audio or abr > (best_audio.get('abr', 0) or 0):
                    best_audio = f

        if has_ffmpeg and best_video and best_audio:
            return f"{best_video.get('format_id')}+{best_audio.get('format_id')}"
        if best_single:
            return best_single.get('format_id', 'best')
        if best_video:
            return best_video.get('format_id', 'best')
        return 'best'

    def _check_ffmpeg(self):
        import subprocess, shutil
        if shutil.which('ffmpeg'):
            return True
        common_paths = [
            r'C:\ProgramData\chocolatey\bin\ffmpeg.exe',
            r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
            r'C:\ffmpeg\bin\ffmpeg.exe',
            os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe'),
        ]
        for p in common_paths:
            if os.path.isfile(p):
                os.environ['PATH'] = os.path.dirname(p) + os.pathsep + os.environ.get('PATH', '')
                return True
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, shell=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def download(self, url, format_spec=None, output_template=None):
        os.makedirs(self.download_dir, exist_ok=True)
        self.reset_cancel()

        outtmpl = output_template or os.path.join(self.download_dir, '%(title)s.%(ext)s')

        print(f"Downloading to: {self.download_dir}")
        print(f"Output template: {outtmpl}")
        print(f"Format: {format_spec or 'best'}")

        opts = {
            'format': format_spec or 'best',
            'outtmpl': outtmpl,
            'progress_hooks': [self._progress_callback],
            'quiet': True,
            'no_warnings': True,
            'noprogress': True,
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    def download_best_video(self, url):
        info = self.get_info(url)
        fmt = self.get_format_string(info)
        self.download(url, format_spec=fmt)

    def download_mp4(self, url):
        info = self.get_info(url)
        fmt = self.get_format_string(info)

        os.makedirs(self.download_dir, exist_ok=True)
        self.reset_cancel()

        outtmpl = os.path.join(self.download_dir, '%(title)s.%(ext)s')
        opts = {
            'format': f'{fmt}+bestaudio/best',
            'outtmpl': outtmpl,
            'progress_hooks': [self._progress_callback],
            'quiet': True,
            'no_warnings': True,
            'noprogress': True,
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    def download_audio(self, url):
        os.makedirs(self.download_dir, exist_ok=True)
        self.reset_cancel()

        outtmpl = os.path.join(self.download_dir, '%(title)s.%(ext)s')
        opts = {
            'format': 'bestaudio/best',
            'outtmpl': outtmpl,
            'progress_hooks': [self._progress_callback],
            'quiet': True,
            'no_warnings': True,
            'noprogress': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    def download_thumbnail(self, url):
        os.makedirs(self.download_dir, exist_ok=True)
        self.reset_cancel()

        outtmpl = os.path.join(self.download_dir, '%(title)s_thumbnail.%(ext)s')
        opts = {
            'format': 'best',
            'outtmpl': outtmpl,
            'progress_hooks': [self._progress_callback],
            'quiet': True,
            'no_warnings': True,
            'noprogress': True,
            'writethumbnail': True,
            'skip_download': True,
            'postprocessors': [{
                'key': 'FFmpegThumbnailsConvertor',
                'format': 'jpg',
            }],
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
            info = ydl.extract_info(url, download=False)
            thumbnails = info.get('thumbnails', [])
            if thumbnails:
                best_thumb = thumbnails[-1]
                url = best_thumb.get('url', '')
                return url
            return None
