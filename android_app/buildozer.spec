[app]

title = Video Downloader
package.name = videodownloader
package.domain = org.videodownloader
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
version.revision = 0
requirements = python3, kivy, kivymd, yt-dlp, certifi
orientation = portrait
osx.public_version = 1.0
osx.bundle_identifier = org.videodownloader
fullscreen = 0

# Android specific
android.api = 34
android.minapi = 21
android.sdk_version = 34
android.ndk_version = 27
android.build_tools = 34.0.0
android.gradle_dependencies =
android.add_src =
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE, FOREGROUND_SERVICE
android.archs = arm64-v8a
android.allow_backup = 1
android.window_soft_input_mode = adjustResize
android.ndk = 27
android.accept_sdk_license = True

# Python-for-android
p4a.branch = develop
p4a.local_recipes =
p4a.hooks =

[buildozer]

log_level = 2
warn_on_root = 1
