#!/bin/bash
# ============================================================================
#  Media Downloader - Flatpak build & install script
#  --------------------------------
#  بناء نسخة Flatpak للتطبيق من ملف manifest (مع إصلاح دعم X11).
#
#  الاستخدام:
#    ./build_flatpak.sh            # بناء + تثبيت من الـ repo المحلي
#    ./build_flatpak.sh --bundle   # بناء + تثبيت + توليد ملف .flatpak للنشر
#    ./build_flatpak.sh --help
# ============================================================================
set -euo pipefail

APP_ID="io.github.hmidani_abdelilah.Media_Downloader"
MANIFEST="flatpak/io.github.hmidani_abdelilah.Media_Downloader.json"
REPO_DIR="repo"
BUILD_DIR="builddir"
REMOTE_NAME="media-downloader-local"
BUNDLE_FILE="${APP_ID}.flatpak"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

MAKE_BUNDLE=0
for arg in "$@"; do
    case "$arg" in
        --bundle) MAKE_BUNDLE=1 ;;
        --help|-h)
            sed -n '1,13p' "$0"
            exit 0
            ;;
        *) echo "خيار غير معروف: $arg" >&2; exit 1 ;;
    esac
done

# ---------------------------------------------------------------
# 1) فحص المتطلبات
# ---------------------------------------------------------------
if ! command -v flatpak >/dev/null 2>&1; then
    echo "خطأ: flatpak غير مثبت. ثبّته أولاً:  sudo apt install flatpak" >&2
    exit 1
fi
if ! command -v flatpak-builder >/dev/null 2>&1; then
    echo "خطأ: flatpak-builder غير مثبت. ثبّته أولاً:  sudo apt install flatpak-builder" >&2
    exit 1
fi

# ---------------------------------------------------------------
# 2) تثبيت SDK/Runtime (24.08) إذا لم يكن موجوداً
# ---------------------------------------------------------------
RUNTIME="org.freedesktop.Platform//24.08"
SDK="org.freedesktop.Sdk//24.08"
if ! flatpak list --runtime >/dev/null 2>&1 | grep -q "org.freedesktop.Sdk.*24.08"; then
    echo "=== تثبيت الـ SDK/Runtime 24.08 (قد يتطلب المصادقة) ==="
    sudo flatpak install -y --noninteractive flathub "$SDK"
fi
if ! flatpak list --runtime >/dev/null 2>&1 | grep -q "org.freedesktop.Platform.*24.08"; then
    sudo flatpak install -y --noninteractive flathub "$RUNTIME"
fi

# ---------------------------------------------------------------
# 3) البناء
# ---------------------------------------------------------------
echo "=== بناء Flatpak (قد يستغرق دقائق) ==="
flatpak-builder --force-clean --disable-rofiles-fuse --repo="$REPO_DIR" "$BUILD_DIR" "$MANIFEST"

# ---------------------------------------------------------------
# 4) الإضافة إلى remote محلي (بدون GPG) والتثبيت للمستخدم
# ---------------------------------------------------------------
echo "=== تسجيل الـ remote المحلي ==="
flatpak remote-delete --user "$REMOTE_NAME" >/dev/null 2>&1 || true
flatpak remote-add --user --if-not-exists --no-gpg-verify "$REMOTE_NAME" "$REPO_DIR"

echo "=== تثبيت التطبيق ==="
flatpak install --user --reinstall -y "$REMOTE_NAME" "$APP_ID"

# ---------------------------------------------------------------
# 5) فرض مقبس X11 فقط (إصلاح عدم ظهور النافذة على Wayland).
#    التطبيق Tkinter يتطلب X11 ولا يدعم Wayland.
# ---------------------------------------------------------------
echo "=== ضبط مقبس X11 ==="
flatpak override --user --socket=x11 "$APP_ID"

# ---------------------------------------------------------------
# 6) توليد ملف .flatpak قابل للنشر (اختياري)
# ---------------------------------------------------------------
if [ "$MAKE_BUNDLE" = "1" ]; then
    echo "=== توليد ملف النشر $BUNDLE_FILE ==="
    flatpak build-bundle "$REPO_DIR" "$BUNDLE_FILE" "$APP_ID" master
    echo "تم توليد: $(pwd)/$BUNDLE_FILE"
fi

echo ""
echo "=== تم بنجاح! شغّل التطبيق عبر: ==="
echo "    flatpak run ${APP_ID}"
