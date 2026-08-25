#!/usr/bin/env bash
set -euo pipefail

APP_NAME="MediaDownloader"
APP_ID="media-downloader"
VERSION="3.0.0"
ARCH="x86_64"

SOURCE_DIR="${1:-$(pwd)/Media_Downloader-3.0.0}"
WORK_DIR="${PWD}/appimage-build"
APPDIR="$WORK_DIR/${APP_NAME}.AppDir"
OUTPUT="${PWD}/${APP_NAME}-${VERSION}-${ARCH}.AppImage"

FFMPEG_URL="https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
APPIMAGETOOL_URL="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "[ERROR] Missing build command: $1" >&2
    exit 1
  }
}

for cmd in wget tar find chmod cp rm mkdir; do
  need_cmd "$cmd"
done

if [[ ! -f "$SOURCE_DIR/app.py" || ! -f "$SOURCE_DIR/requirements.txt" ]]; then
  echo "[ERROR] Source directory is invalid: $SOURCE_DIR" >&2
  echo "Usage: $0 /path/to/Media_Downloader-3.0.0" >&2
  exit 1
fi

echo "=========================================================="
echo " Media Downloader ${VERSION} - AppImage source/VENV build"
echo "=========================================================="

rm -rf "$WORK_DIR"
mkdir -p \
  "$APPDIR/usr/share/$APP_ID" \
  "$APPDIR/usr/bin" \
  "$APPDIR/usr/share/applications" \
  "$APPDIR/usr/share/icons/hicolor/256x256/apps" \
  "$WORK_DIR/downloads"

# Copy source code. The writable VENV is deliberately NOT stored in AppImage.
echo "[*] Copying application source..."
cp -a "$SOURCE_DIR/." "$APPDIR/usr/share/$APP_ID/"
rm -rf \
  "$APPDIR/usr/share/$APP_ID/.git" \
  "$APPDIR/usr/share/$APP_ID/.github" \
  "$APPDIR/usr/share/$APP_ID/.venv" \
  "$APPDIR/usr/share/$APP_ID/venv" \
  "$APPDIR/usr/share/$APP_ID/__pycache__" \
  "$APPDIR/usr/share/$APP_ID/build" \
  "$APPDIR/usr/share/$APP_ID/dist"

# Bundle BtbN static FFmpeg/FFprobe.
echo "[*] Downloading BtbN static FFmpeg..."
wget -q --show-progress -O "$WORK_DIR/downloads/ffmpeg.tar.xz" "$FFMPEG_URL"
mkdir -p "$WORK_DIR/ffmpeg"
tar -xJf "$WORK_DIR/downloads/ffmpeg.tar.xz" -C "$WORK_DIR/ffmpeg"

FFMPEG_BIN="$(find "$WORK_DIR/ffmpeg" -type f -path '*/bin/ffmpeg' -print -quit)"
FFPROBE_BIN="$(find "$WORK_DIR/ffmpeg" -type f -path '*/bin/ffprobe' -print -quit)"

if [[ -z "$FFMPEG_BIN" || -z "$FFPROBE_BIN" ]]; then
  echo "[ERROR] ffmpeg/ffprobe not found in downloaded archive." >&2
  exit 1
fi

cp "$FFMPEG_BIN" "$APPDIR/usr/bin/ffmpeg"
cp "$FFPROBE_BIN" "$APPDIR/usr/bin/ffprobe"
chmod 0755 "$APPDIR/usr/bin/ffmpeg" "$APPDIR/usr/bin/ffprobe"

# Desktop integration.
ICON_SRC=""
for candidate in \
  "$SOURCE_DIR/asset/Icon.png" \
  "$SOURCE_DIR/icon.png" \
  "$SOURCE_DIR/assets/icon.png"; do
  if [[ -f "$candidate" ]]; then
    ICON_SRC="$candidate"
    break
  fi
done

if [[ -n "$ICON_SRC" ]]; then
  cp "$ICON_SRC" "$APPDIR/$APP_ID.png"
  cp "$ICON_SRC" "$APPDIR/usr/share/icons/hicolor/256x256/apps/$APP_ID.png"
else
  echo "[WARN] PNG icon was not found."
fi

cat > "$APPDIR/$APP_ID.desktop" <<EOF_DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=Media Downloader
Comment=Download videos and audio using yt-dlp
Exec=$APP_ID
Icon=$APP_ID
Terminal=false
Categories=Network;Utility;
StartupNotify=true
EOF_DESKTOP
cp "$APPDIR/$APP_ID.desktop" "$APPDIR/usr/share/applications/$APP_ID.desktop"

# AppRun creates a writable per-user VENV. This keeps the in-app dependency
# updater working because gui.py calls: sys.executable -m pip install --upgrade.
cat > "$APPDIR/AppRun" <<'EOF_APPRUN'
#!/usr/bin/env bash
set -euo pipefail

APPDIR="${APPDIR:-$(dirname "$(readlink -f "$0")")}" 
APP_SRC="$APPDIR/usr/share/media-downloader"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
DATA_DIR="$DATA_HOME/media-downloader"
VENV="$DATA_DIR/venv"

export PATH="$APPDIR/usr/bin:$VENV/bin:$PATH"
export MEDIA_DOWNLOADER_APPIMAGE=1
export MEDIA_DOWNLOADER_APPDIR="$APPDIR"
export PYTHONUTF8=1
export PYTHONUNBUFFERED=1

mkdir -p "$DATA_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Media Downloader requires Python 3 on the host system." >&2
  exit 20
fi

# tkinter is provided by the distribution's Python packages and is required
# by CustomTkinter/TkinterDnD.
if ! python3 -c 'import tkinter' >/dev/null 2>&1; then
  echo "Python tkinter is missing. Install python3-tk (Debian/Ubuntu) or python3-tkinter (Fedora/RHEL)." >&2
  exit 21
fi

create_venv() {
  rm -rf "$VENV"
  if ! python3 -m venv "$VENV"; then
    echo "Could not create the virtual environment." >&2
    echo "On Debian/Ubuntu install python3-venv. On Fedora/RHEL install python3 and python3-pip." >&2
    exit 22
  fi

  "$VENV/bin/python" -m pip install --upgrade pip setuptools wheel
  "$VENV/bin/python" -m pip install --upgrade -r "$APP_SRC/requirements.txt"
}

if [[ ! -x "$VENV/bin/python" ]]; then
  create_venv
fi

# Repair an incomplete/corrupt VENV automatically.
if ! "$VENV/bin/python" -c 'import customtkinter, tkinterdnd2, yt_dlp' >/dev/null 2>&1; then
  create_venv
fi

cd "$APP_SRC"
exec "$VENV/bin/python" app.py "$@"
EOF_APPRUN
chmod 0755 "$APPDIR/AppRun"

ln -sfn AppRun "$APPDIR/$APP_ID"

# Download appimagetool and build.
echo "[*] Downloading appimagetool..."
wget -q --show-progress -O "$WORK_DIR/appimagetool.AppImage" "$APPIMAGETOOL_URL"
chmod 0755 "$WORK_DIR/appimagetool.AppImage"

rm -f "$OUTPUT"
echo "[*] Building AppImage..."
ARCH="$ARCH" "$WORK_DIR/appimagetool.AppImage" --appimage-extract-and-run "$APPDIR" "$OUTPUT"
chmod 0755 "$OUTPUT"

echo
echo "=========================================================="
echo " Build completed"
echo " Output: $OUTPUT"
echo "=========================================================="
echo
echo "Runtime notes:"
echo "  - Python packages live in: ~/.local/share/media-downloader/venv"
echo "  - The app's Update Dependencies button updates that VENV."
echo "  - FFmpeg and FFprobe are bundled inside the AppImage."
echo "  - Host Python 3 + tkinter + venv support are still required."
