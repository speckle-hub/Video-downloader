import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
from pathlib import Path
from core.downloader import Downloader


class DesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Downloader")
        self.root.geometry("800x650")
        self.root.minsize(700, 550)

        self.downloader = Downloader()
        self.download_thread = None
        self.current_formats = []
        self.current_info = None

        style = ttk.Style()
        style.theme_use('vista')

        main_frame = ttk.Frame(root, padding="12")
        main_frame.pack(fill=tk.BOTH, expand=True)

        url_frame = ttk.LabelFrame(main_frame, text="URL", padding="8")
        url_frame.pack(fill=tk.X)

        ttk.Label(url_frame, text="Enter video/page URL:").pack(anchor=tk.W)
        url_input_frame = ttk.Frame(url_frame)
        url_input_frame.pack(fill=tk.X, pady=(4, 0))
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(url_input_frame, textvariable=self.url_var, font=('Segoe UI', 10))
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.url_entry.bind('<Return>', lambda e: self.fetch_info())
        self.fetch_btn = ttk.Button(url_input_frame, text="Fetch Info", command=self.fetch_info)
        self.fetch_btn.pack(side=tk.RIGHT, padx=(6, 0))

        info_frame = ttk.LabelFrame(main_frame, text="Media Info", padding="8")
        info_frame.pack(fill=tk.X, pady=(8, 0))

        self.info_text = tk.Text(info_frame, height=3, wrap=tk.WORD, font=('Consolas', 9), state='disabled', bg='#f0f0f0')
        self.info_text.pack(fill=tk.X)

        ffmpeg_frame = ttk.Frame(main_frame)
        ffmpeg_frame.pack(fill=tk.X, pady=(4, 0))
        self.ffmpeg_label = ttk.Label(ffmpeg_frame,
            text="ffmpeg: NOT installed (720p+ quality requires it)",
            foreground='#cc6600')
        self.ffmpeg_label.pack(side=tk.LEFT)
        if self.downloader.ffmpeg_available:
            self.ffmpeg_label.config(text="ffmpeg: available (high quality supported)", foreground='#006600')

        format_frame = ttk.LabelFrame(main_frame, text="Available Formats / Resolutions", padding="8")
        format_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        columns = ('id', 'resolution', 'vcodec', 'acodec', 'fps', 'size', 'note')
        self.format_tree = ttk.Treeview(format_frame, columns=columns, show='headings', height=8, selectmode='browse')
        self.format_tree.heading('id', text='ID')
        self.format_tree.heading('resolution', text='Resolution')
        self.format_tree.heading('vcodec', text='Video Codec')
        self.format_tree.heading('acodec', text='Audio Codec')
        self.format_tree.heading('fps', text='FPS')
        self.format_tree.heading('size', text='Size')
        self.format_tree.heading('note', text='Note')

        self.format_tree.column('id', width=60, anchor=tk.CENTER)
        self.format_tree.column('resolution', width=120, anchor=tk.CENTER)
        self.format_tree.column('vcodec', width=100)
        self.format_tree.column('acodec', width=100)
        self.format_tree.column('fps', width=50, anchor=tk.CENTER)
        self.format_tree.column('size', width=80, anchor=tk.CENTER)
        self.format_tree.column('note', width=180)

        vsb = ttk.Scrollbar(format_frame, orient=tk.VERTICAL, command=self.format_tree.yview)
        self.format_tree.configure(yscrollcommand=vsb.set)
        self.format_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(8, 0))

        dir_frame = ttk.Frame(bottom_frame)
        dir_frame.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(dir_frame, text="Save to:").pack(side=tk.LEFT)
        self.dir_var = tk.StringVar(value=str(Path.home() / "Downloads" / "VideoDownloader"))
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var)
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 4))
        ttk.Button(dir_frame, text="Browse", command=self.browse_dir).pack(side=tk.RIGHT)

        action_frame = ttk.Frame(bottom_frame)
        action_frame.pack(fill=tk.X)

        self.dl_selected_btn = ttk.Button(action_frame, text="Download Selected Format", command=self.download_selected, style='Accent.TButton')
        self.dl_selected_btn.pack(side=tk.LEFT, padx=(0, 4))

        self.dl_best_btn = ttk.Button(action_frame, text="Best Video", command=lambda: self.quick_download('best'))
        self.dl_best_btn.pack(side=tk.LEFT, padx=(0, 4))

        self.dl_mp4_btn = ttk.Button(action_frame, text="Best MP4", command=lambda: self.quick_download('mp4'))
        self.dl_mp4_btn.pack(side=tk.LEFT, padx=(0, 4))

        self.dl_audio_btn = ttk.Button(action_frame, text="Audio (MP3)", command=lambda: self.quick_download('audio'))
        self.dl_audio_btn.pack(side=tk.LEFT, padx=(0, 4))

        self.dl_photo_btn = ttk.Button(action_frame, text="Photo", command=lambda: self.quick_download('photo'))
        self.dl_photo_btn.pack(side=tk.LEFT)

        self.cancel_btn = ttk.Button(action_frame, text="Cancel", command=self.cancel_download, state='disabled')
        self.cancel_btn.pack(side=tk.RIGHT, padx=(4, 0))

        self.clear_btn = ttk.Button(action_frame, text="Clear", command=self.clear_all)
        self.clear_btn.pack(side=tk.RIGHT)

        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(6, 0))

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.status_var).pack(anchor=tk.W)

        self.progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(2, 0))

        self.disable_download_buttons()

    def disable_download_buttons(self):
        self.dl_selected_btn.config(state='disabled')
        self.dl_best_btn.config(state='disabled')
        self.dl_mp4_btn.config(state='disabled')
        self.dl_audio_btn.config(state='disabled')
        self.dl_photo_btn.config(state='disabled')

    def enable_download_buttons(self):
        self.dl_best_btn.config(state='normal')
        self.dl_mp4_btn.config(state='normal')
        self.dl_audio_btn.config(state='normal')
        self.dl_photo_btn.config(state='normal')
        self.dl_selected_btn.config(state='normal')

    def browse_dir(self):
        d = filedialog.askdirectory(initialdir=self.dir_var.get())
        if d:
            self.dir_var.set(d)

    def log(self, msg):
        self.info_text.config(state='normal')
        self.info_text.insert(tk.END, msg + '\n')
        self.info_text.see(tk.END)
        self.info_text.config(state='disabled')

    def clear_log(self):
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.config(state='disabled')

    def fetch_info(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Please enter a URL first.")
            return

        self.fetch_btn.config(state='disabled', text='Fetching...')
        self.disable_download_buttons()
        self.clear_log()
        self.log(f"Fetching info for: {url}")
        self.status_var.set("Fetching info...")
        self.progress['value'] = 0

        for item in self.format_tree.get_children():
            self.format_tree.delete(item)

        def task():
            try:
                info = self.downloader.get_info(url)
                self.current_info = info
                title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)
                uploader = info.get('uploader', info.get('channel', 'Unknown'))

                mins, secs = divmod(int(duration), 60)
                hrs, mins = divmod(mins, 60)
                dur_str = f"{hrs}h {mins}m {secs}s" if hrs else f"{mins}m {secs}s"

                formats = info.get('formats', [])

                def update_ui():
                    self.clear_log()
                    self.log(f"Title: {title}")
                    self.log(f"Uploader: {uploader}  |  Duration: {dur_str}  |  Formats: {len(formats)}")
                    ffmpeg_status = "available" if self.downloader.ffmpeg_available else "NOT installed"
                    self.log(f"ffmpeg: {ffmpeg_status} {'(HD/4K requires ffmpeg)' if not self.downloader.ffmpeg_available else ''}")
                    self.log(f"Tip: Select a format with 'Video+Audio' note for instant play, or 'Video only' + 'Audio only' separately (needs ffmpeg)")
                    self.log("-" * 60)

                    self.current_formats = formats
                    self.populate_formats(formats)
                    self.status_var.set(f"Ready: {title[:60]}")
                    self.enable_download_buttons()

                self.root.after(0, update_ui)
            except Exception as e:
                self.root.after(0, lambda: self.log(f"ERROR: {e}"))
                self.root.after(0, lambda: self.status_var.set("Error fetching info"))
            finally:
                self.root.after(0, lambda: (self.fetch_btn.config(state='normal', text='Fetch Info')))

        threading.Thread(target=task, daemon=True).start()

    def populate_formats(self, formats):
        for item in self.format_tree.get_children():
            self.format_tree.delete(item)

        seen = set()
        for f in formats:
            fid = f.get('format_id', '?')
            height = f.get('height', 0) or 0
            width = f.get('width', 0) or 0
            vcodec = f.get('vcodec', 'none')
            acodec = f.get('acodec', 'none')
            fps = f.get('fps', '') or ''
            filesize = f.get('filesize', 0) or 0
            tbr = f.get('tbr', 0) or 0
            abr = f.get('abr', 0) or 0

            if vcodec == 'none' and acodec == 'none':
                continue

            if vcodec != 'none':
                res = f"{width}x{height}" if width and height else f"{height}p"
            else:
                res = "Audio only"

            size_str = ""
            if filesize:
                if filesize > 1024 * 1024:
                    size_str = f"{filesize / 1024 / 1024:.0f} MB"
                else:
                    size_str = f"{filesize / 1024:.0f} KB"

            note = ""
            if vcodec != 'none' and acodec != 'none':
                note = "Video+Audio"
            elif vcodec != 'none':
                note = "Video only"
                if tbr:
                    note += f" ({tbr:.0f}k)"
            elif acodec != 'none':
                note = "Audio only"
                if abr:
                    note += f" ({abr:.0f}k)"

            dedup_key = (fid, height, width)
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            self.format_tree.insert('', tk.END, values=(
                fid,
                res if height else f"Audio {abr:.0f}k" if abr else "Audio",
                vcodec if vcodec != 'none' else '-',
                acodec if acodec != 'none' else '-',
                str(fps) if fps else '',
                size_str,
                note
            ))

    def get_selected_format_id(self):
        sel = self.format_tree.selection()
        if not sel:
            messagebox.showinfo("Select Format", "Please select a format from the list first.")
            return None
        values = self.format_tree.item(sel[0], 'values')
        return values[0]

    def download_selected(self):
        fid = self.get_selected_format_id()
        if fid is None:
            return
        url = self.url_var.get().strip()
        if not url:
            return
        self.status_var.set(f"Downloading format {fid}...")

        sel = self.format_tree.selection()
        values = self.format_tree.item(sel[0], 'values')
        self.log(f"Downloading format {fid} ({values[1]})...")
        self.do_download(url, format_spec=fid)

    def quick_download(self, mode):
        url = self.url_var.get().strip()
        if not url:
            return
        mode_names = {'best': 'Best Video', 'mp4': 'Best MP4', 'audio': 'Audio (MP3)', 'photo': 'Photo'}
        self.status_var.set(f"Downloading {mode_names.get(mode, mode)}...")
        self.log(f"Downloading: {mode_names.get(mode, mode)}...")
        self.do_download(url, mode=mode)

    def do_download(self, url, mode=None, format_spec=None):
        self.downloader.download_dir = self.dir_var.get()
        self.disable_download_buttons()
        self.cancel_btn.config(state='normal')
        self.progress['value'] = 0

        def hook(d):
            try:
                if d['status'] == 'downloading':
                    total = d.get('total_bytes') or d.get('total_bytes_estimate', 0) or 0
                    downloaded = d.get('downloaded_bytes', 0) or 0
                    pct = 0
                    if total > 0:
                        pct = min(int(downloaded / total * 100), 100)
                        self.root.after(0, lambda p=pct: self.progress.configure(value=p))
                    speed = d.get('speed', 0) or 0
                    if speed and total > 0:
                        speed_kb = speed / 1024
                        p = pct
                        d_mb = downloaded / 1024 / 1024
                        t_mb = total / 1024 / 1024
                        self.root.after(0, lambda: self.status_var.set(
                            f"{p}% - {d_mb:.1f}MB / {t_mb:.1f}MB @ {speed_kb:.0f} KB/s"
                        ))
                    elif speed:
                        speed_kb = speed / 1024
                        self.root.after(0, lambda s=speed_kb: self.status_var.set(
                            f"Downloading... @ {s:.0f} KB/s"
                        ))
                elif d['status'] == 'finished':
                    self.root.after(0, lambda: self.progress.configure(value=100))
                    self.root.after(0, lambda: self.status_var.set("Processing..."))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Hook error: {e}"))

        self.downloader.on_progress(hook)

        def task():
            try:
                if mode == 'audio':
                    self.downloader.download_audio(url)
                elif mode == 'photo':
                    self.downloader.download_thumbnail(url)
                elif mode == 'mp4':
                    self.downloader.download_mp4(url)
                elif mode == 'best':
                    self.downloader.download_best_video(url)
                else:
                    self.downloader.download(url, format_spec=format_spec)
                self.root.after(0, lambda: self.log("Download complete!"))
                self.root.after(0, lambda: self.status_var.set("Download complete!"))
                self.root.after(0, lambda: self.progress.configure(value=100))
                self.root.after(0, lambda: self.list_downloaded_files())
            except Exception as e:
                import traceback
                self.root.after(0, lambda: self.log(f"ERROR: {e}"))
                self.root.after(0, lambda: self.log(traceback.format_exc()))
                self.root.after(0, lambda: self.status_var.set(f"Error: {e}"))
            finally:
                self.downloader.remove_progress_hook(hook)
                self.root.after(0, self.enable_download_buttons)
                self.root.after(0, lambda: self.cancel_btn.config(state='disabled'))

        self.download_thread = threading.Thread(target=task, daemon=True)
        self.download_thread.start()

    def list_downloaded_files(self):
        dl_dir = self.dir_var.get()
        if os.path.isdir(dl_dir):
            files = [f for f in os.listdir(dl_dir) if os.path.isfile(os.path.join(dl_dir, f))]
            if files:
                self.log(f"Files in '{dl_dir}':")
                for f in files[-10:]:
                    filepath = os.path.join(dl_dir, f)
                    size = os.path.getsize(filepath)
                    size_str = f"{size/1024/1024:.1f}MB" if size > 1024*1024 else f"{size/1024:.0f}KB"
                    self.log(f"  {f} ({size_str})")
            else:
                self.log(f"WARNING: No files found in '{dl_dir}'")

    def cancel_download(self):
        self.downloader.cancel()
        self.status_var.set("Cancelling...")
        self.log("Cancelling download...")

    def clear_all(self):
        self.url_var.set("")
        self.clear_log()
        self.progress['value'] = 0
        self.status_var.set("Ready")
        self.disable_download_buttons()
        self.current_formats = []
        self.current_info = None
        for item in self.format_tree.get_children():
            self.format_tree.delete(item)


def main():
    root = tk.Tk()
    app = DesktopApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
