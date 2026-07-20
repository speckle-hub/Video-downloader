import os
import sys
import threading
from pathlib import Path
from kivy.utils import platform

if platform == "android":
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])

DOWNLOAD_DIR = str(Path.home() / "VideoDownloader")
try:
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
except:
    DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

from kivy.clock import Clock
from kivy.metrics import dp

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.appbar import MDTopAppBar, MDTopAppBarTitle
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFilledButton, MDTextButton, MDIconButton
from kivymd.uix.list import MDList, OneLineAvatarListItem, IconLeftWidget, TwoLineAvatarListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.progress import MDLinearProgressIndicator
from kivymd.uix.label import MDLabel
from kivymd.uix.divider import MDDivider
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.tooltip import MDTooltip
from kivymd.utils.set_bars_colors import set_bars_colors


class FormatCard(MDCard):
    def __init__(self, fmt_info, on_select, **kwargs):
        super().__init__(**kwargs)
        self.fmt_info = fmt_info
        self.on_select = on_select
        self.size_hint_y = None
        self.height = dp(72)
        self.padding = dp(12)
        self.radius = 12
        self.elevation = 0
        self.theme_bg_color = "Custom"
        self.md_bg_color = (0.2, 0.2, 0.25, 1)
        self.bind(on_release=lambda x: self.select())

    def select(self):
        self.on_select(self.fmt_info)


class MainScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.formats = []
        self.downloading = False
        self.selected_format = None
        self.build_ui()

    def build_ui(self):
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.anchorlayout import AnchorLayout

        main = BoxLayout(orientation='vertical', spacing=0)

        appbar = MDTopAppBar(
            md_bg_color=(0.1, 0.1, 0.15, 1),
            elevation=0,
        )
        appbar.add_widget(MDTopAppBarTitle(text="Video Downloader"))
        main.add_widget(appbar)

        scroll = MDScrollView()
        content = BoxLayout(orientation='vertical', padding=[16, 8, 16, 16], spacing=12, size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        self.url_field = MDTextField(
            hint_text="Paste video URL here",
            mode="filled",
            max_height=dp(56),
            size_hint_x=1,
        )
        content.add_widget(self.url_field)

        btn_row = BoxLayout(spacing=8, size_hint_y=None, height=dp(48))
        self.fetch_btn = MDFilledButton(
            text="Fetch Info",
            style="filled",
            on_release=self.fetch_info,
        )
        btn_row.add_widget(self.fetch_btn)
        content.add_widget(btn_row)

        self.info_label = MDLabel(
            text="",
            font_size=dp(13),
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(20),
        )
        content.add_widget(self.info_label)

        formats_header = BoxLayout(size_hint_y=None, height=dp(30))
        formats_header.add_widget(MDLabel(text="Available Formats", font_size=dp(15), bold=True))
        content.add_widget(formats_header)

        self.formats_container = BoxLayout(orientation='vertical', spacing=6, size_hint_y=None)
        self.formats_container.bind(minimum_height=self.formats_container.setter('height'))
        content.add_widget(self.formats_container)

        self.progress_indicator = MDLinearProgressIndicator(
            size_hint_x=1,
            value=0,
            md_bg_color=(0.3, 0.3, 0.35, 1),
        )
        self.progress_indicator.opacity = 0
        content.add_widget(self.progress_indicator)

        self.status_label = MDLabel(
            text="",
            font_size=dp(12),
            theme_text_color="Secondary",
            halign="center",
            size_hint_y=None,
            height=dp(20),
        )
        content.add_widget(self.status_label)

        self.dl_btn = MDFilledButton(
            text="Download Selected",
            style="filled",
            disabled=True,
            on_release=self.start_download,
            size_hint_x=1,
        )
        content.add_widget(self.dl_btn)

        scroll.add_widget(content)
        main.add_widget(scroll)
        self.add_widget(main)

    def fetch_info(self, *args):
        url = self.url_field.text.strip()
        if not url:
            Snackbar(text="Please enter a URL").open()
            return

        self.fetch_btn.disabled = True
        self.fetch_btn.text = "Fetching..."
        self.info_label.text = ""
        self.formats_container.clear_widgets()
        self.selected_format = None
        self.dl_btn.disabled = True

        def task():
            try:
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from core.downloader import Downloader
                d = Downloader()
                info = d.get_info(url)
                title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)
                uploader = info.get('uploader', info.get('channel', 'Unknown'))
                mins, secs = divmod(int(duration), 60)
                dur_str = f"{mins}m {secs}s"

                raw_formats = info.get('formats', [])
                parsed = []
                seen = set()
                for f in raw_formats:
                    fid = f.get('format_id', '?')
                    h = f.get('height', 0) or 0
                    w = f.get('width', 0) or 0
                    v = f.get('vcodec', 'none')
                    a = f.get('acodec', 'none')
                    if v == 'none' and a == 'none':
                        continue
                    dedup = (fid, h, w)
                    if dedup in seen:
                        continue
                    seen.add(dedup)
                    if v != 'none' and a != 'none':
                        note = "Video+Audio"
                    elif v != 'none':
                        note = "Video only"
                    else:
                        note = "Audio only"
                    res = f"{h}p" if h else "Audio"
                    parsed.append({"id": fid, "resolution": res, "note": note, "height": h})

                Clock.schedule_once(lambda dt: self.show_formats(title, uploader, dur_str, parsed))
            except Exception as e:
                Clock.schedule_once(lambda dt: self.show_error(str(e)))

        threading.Thread(target=task, daemon=True).start()

    def show_formats(self, title, uploader, duration, formats):
        self.fetch_btn.disabled = False
        self.fetch_btn.text = "Fetch Info"
        self.info_label.text = f"{title}  |  {uploader}  |  {duration}"
        self.formats = formats
        self.formats_container.clear_widgets()

        for fmt in formats:
            card = FormatCard(fmt, self.on_format_selected)
            from kivy.uix.boxlayout import BoxLayout
            from kivymd.uix.label import MDLabel
            row = BoxLayout(orientation='horizontal', spacing=8)
            id_label = MDLabel(text=fmt["id"], font_size=dp(12), halign="center", size_hint_x=0.15)
            res_label = MDLabel(text=fmt["resolution"], font_size=dp(14), bold=True, size_hint_x=0.3)
            note_label = MDLabel(text=fmt["note"], font_size=dp(12), theme_text_color="Secondary", size_hint_x=0.4)
            row.add_widget(id_label)
            row.add_widget(res_label)
            row.add_widget(note_label)
            card.add_widget(row)
            self.formats_container.add_widget(card)

    def show_error(self, msg):
        self.fetch_btn.disabled = False
        self.fetch_btn.text = "Fetch Info"
        Snackbar(text=f"Error: {msg}").open()

    def on_format_selected(self, fmt):
        self.selected_format = fmt
        self.dl_btn.disabled = False
        self.dl_btn.text = f"Download {fmt['id']} ({fmt['resolution']})"
        for child in self.formats_container.children:
            if isinstance(child, FormatCard):
                child.md_bg_color = (0.25, 0.25, 0.3, 1) if child.fmt_info["id"] != fmt["id"] else (0.3, 0.5, 0.8, 0.4)

    def start_download(self, *args):
        if not self.selected_format or self.downloading:
            return
        url = self.url_field.text.strip()
        if not url:
            return

        self.downloading = True
        self.dl_btn.disabled = True
        self.dl_btn.text = "Downloading..."
        self.progress_indicator.opacity = 1
        self.progress_indicator.value = 0
        self.status_label.text = "Starting..."

        def task():
            try:
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from core.downloader import Downloader

                def hook(d):
                    if d['status'] == 'downloading':
                        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0) or 0
                        downloaded = d.get('downloaded_bytes', 0) or 0
                        if total > 0:
                            pct = min(int(downloaded / total * 100), 100)
                            Clock.schedule_once(lambda dt: setattr(self.progress_indicator, 'value', pct / 100))
                            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', f"{pct}%"))
                    elif d['status'] == 'finished':
                        Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', "Processing..."))

                downloader = Downloader(download_dir=DOWNLOAD_DIR)
                downloader.on_progress(hook)
                fid = self.selected_format["id"]
                downloader.download(url, format_spec=fid)
                Clock.schedule_once(self.download_complete)
            except Exception as e:
                Clock.schedule_once(lambda dt: self.download_error(str(e)))

        threading.Thread(target=task, daemon=True).start()

    def download_complete(self, *args):
        self.downloading = False
        self.dl_btn.disabled = False
        self.dl_btn.text = "Download Selected"
        self.progress_indicator.value = 1
        self.status_label.text = "Download complete!"
        Snackbar(text=f"Saved to {DOWNLOAD_DIR}").open()
        Clock.schedule_once(lambda dt: setattr(self.progress_indicator, 'opacity', 0), 2)

    def download_error(self, msg):
        self.downloading = False
        self.dl_btn.disabled = False
        self.dl_btn.text = "Download Selected"
        self.progress_indicator.value = 0
        self.status_label.text = f"Error: {msg}"
        Snackbar(text=f"Error: {msg}").open()


class VideoDownloaderApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.material_style = "M3"
        return MainScreen()

    def on_start(self):
        set_bars_colors(
            (0.1, 0.1, 0.15, 1),
            (0.9, 0.9, 0.95, 1),
        )


if __name__ == "__main__":
    VideoDownloaderApp().run()
