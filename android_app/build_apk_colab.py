# Video Downloader APK Builder for Google Colab
# ==============================================
# How to use:
# 1. Go to https://colab.research.google.com/
# 2. Create a new notebook
# 3. Paste this entire script into a code cell
# 4. Run the cell
# 5. Download the APK from the files panel

# Step 1: Upload the android_app folder
import os, sys, zipfile, shutil, glob
from google.colab import files

print("=" * 50)
print("Video Downloader APK Builder")
print("=" * 50)
print()
print("Step 1: Upload your android_app folder as a ZIP file")
print("(Zip the android_app folder first, then upload it here)")
print()

uploaded = files.upload()
zip_filename = list(uploaded.keys())[0]

# Extract
extract_dir = "/content/video_downloader"
if os.path.exists(extract_dir):
    shutil.rmtree(extract_dir)
os.makedirs(extract_dir)

with zipfile.ZipFile(zip_filename, 'r') as zf:
    # Handle if zip contains a top-level folder
    top_level = None
    for name in zf.namelist():
        if '/' in name:
            candidate = name.split('/')[0]
            if top_level is None:
                top_level = candidate
            elif candidate != top_level:
                top_level = None
                break
        else:
            top_level = None
            break

    if top_level and top_level in ('android_app', 'video_downloader'):
        for name in zf.namelist():
            dest = os.path.join(extract_dir, '/'.join(name.split('/')[1:]))
            if name.endswith('/'):
                os.makedirs(dest, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with zf.open(name) as src, open(dest, 'wb') as dst:
                    dst.write(src.read())
    else:
        zf.extractall(extract_dir)

print(f"Files extracted to {extract_dir}")
print(os.listdir(extract_dir))

# Step 2: Install dependencies
print()
print("Step 2: Installing Buildozer and dependencies...")
!apt-get update -qq
!apt-get install -y -qq python3-pip python3-dev build-essential git zip unzip openjdk-17-jdk
!pip install -q buildozer cython

# Step 3: Build the APK
print()
print("Step 3: Building APK (this takes 15-30 minutes)...")
os.chdir(extract_dir)

# Fix permissions issue
!sudo dpkg --add-architecture i386
!sudo apt-get install -y -qq libncurses5:i386 libstdc++6:i386 zlib1g:i386

!buildozer android debug

# Step 4: Find and download APK
print()
print("Step 4: Locating APK...")
apk_paths = glob.glob(os.path.join(extract_dir, "bin", "*.apk"))
if apk_paths:
    apk_path = apk_paths[0]
    print(f"APK built: {apk_path}")
    print(f"Size: {os.path.getsize(apk_path) / 1024 / 1024:.1f} MB")
    print()
    print("Downloading APK to your computer...")
    files.download(apk_path)
else:
    print("ERROR: APK not found in bin/ directory")
    print("Contents of bin/:")
    !ls -la bin/ 2>/dev/null || echo "(no bin directory)"
    print()
    print("Buildozer output:")
    !cat buildozer.log 2>/dev/null | tail -50 || echo "(no log)"
