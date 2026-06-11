#!/bin/bash

# -----------------------------------------------------------------------------
# مشروع: Media_Downloader
# وصف: سكريبت جلب المتطلبات، إنشاء بيئة وهمية، وتثبيت ملف الـ Desktop (يدعم عائلة Arch)
# الكاتب الأصلي للمشروع: Abdelilah Hmidani
# -----------------------------------------------------------------------------

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== بدء تثبيت برنامج Media Downloader ===${NC}"

# 1. التحقق من صلاحيات الـ Root لتثبيت حزم النظام
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ خطأ ] يرجى تشغيل السكريبت بصلاحيات الـ Root (sudo ./installer.sh)${NC}"
    exit 1
fi

# 2. التعرف على التوزيعة وتثبيت Python3 و FFmpeg
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    LIKE=$ID_LIKE
else
    echo -e "${RED}[ خطأ ] تعذر التعرف على النظام.${NC}"
    exit 1
fi

install_system_deps() {
    case "$OS" in
        ubuntu|debian|kali|raspbian|linuxmint)
            echo -e "${BLUE}[ تثبيت ] تحديث الحزم وتثبيت python3-venv و ffmpeg...${NC}"
            apt-get update -y
            apt-get install -y python3 python3-pip python3-venv ffmpeg
            ;;
        fedora)
            echo -e "${BLUE}[ تثبيت ] تثبيت python3 و ffmpeg عبر DNF...${NC}"
            dnf install -y python3 python3-pip ffmpeg
            ;;
        rhel|centos|rocky|almalinux)
            echo -e "${BLUE}[ تثبيت ] تفعيل مستودع EPEL وتثبيت المتطلبات...${NC}"
            if [ "$OS" != "fedora" ]; then
                dnf install -y epel-release || yum install -y epel-release
            fi
            dnf install -y python3 python3-pip ffmpeg || yum install -y python3 python3-pip ffmpeg
            ;;
        arch|manjaro|endeavouros|garuda)
            echo -e "${BLUE}[ تثبيت ] تحديث المستودعات وتثبيت python و ffmpeg عبر Pacman...${NC}"
            # في Arch، حزمة python تأتي مدمجة مع pip و venv تلقائياً
            pacman -Sy --noconfirm --needed python python-pip ffmpeg
            ;;
        *)
            # فحص السلالة الجانبية في حال لم يطابق الاسم المباشر
            if [[ "$LIKE" == *"arch"* ]]; then
                pacman -Sy --noconfirm --needed python python-pip ffmpeg
            elif [[ "$LIKE" == *"debian"* || "$LIKE" == *"ubuntu"* ]]; then
                apt-get update -y && apt-get install -y python3 python3-pip python3-venv ffmpeg
            elif [[ "$LIKE" == *"rhel"* || "$LIKE" == *"fedora"* ]]; then
                dnf install -y python3 python3-pip ffmpeg || yum install -y python3 python3-pip ffmpeg
            else
                echo -e "${RED}[ تحذير ] التوزيعة غير معروفة بشكل قياسي، تأكد من تثبيت python3 و ffmpeg يدوياً.${NC}"
            fi
            ;;
    esac
}

install_system_deps

# 3. إعداد البيئة الوهمية (Virtual Environment) للمشروع
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$APP_DIR/venv"

echo -e "${BLUE}[ إعداد ] إنشاء بيئة بايثون وهمية في: $VENV_DIR...${NC}"
rm -rf "$VENV_DIR" 
python3 -m venv "$VENV_DIR"

# تفعيل البيئة وتثبيت مكتبات بايثون
source "$VENV_DIR/bin/activate"
echo -e "${BLUE}[ تثبيت ] تحديث pip وتثبيت مكتبات Python المطلوبة...${NC}"
pip install --upgrade pip

# التثبيت المباشر للمكتبات الأساسية للمشروع لضمان عمل الواجهة والمحرك
pip install PySide6 customtkinter yt-dlp requests

deactivate

# 4. بناء ملف الـ Desktop (.desktop) لسطح المكتب
DESKTOP_FILE="/usr/share/applications/media-downloader.desktop"
MAIN_SCRIPT="$APP_DIR/main.py" 

if [ -f "$APP_DIR/icon.png" ]; then
    ICON_PATH="$APP_DIR/icon.png"
else
    ICON_PATH="video-player"
fi

echo -e "${BLUE}[ إعداد ] إنشاء ملف تشغيل سطح المكتب في $DESKTOP_FILE...${NC}"

cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Version=1.0
Type=Application
Name=Media Downloader
Comment=Download videos and audio from the internet using yt-dlp
Exec="$VENV_DIR/bin/python3" "$MAIN_SCRIPT"
Icon=$ICON_PATH
Terminal=false
Categories=Network;Utility;
StartupNotify=true
EOF

chmod 644 "$DESKTOP_FILE"

echo -e "${GREEN}[ نجاح ] تم التثبيت بنجاح على توزيعتك الشغالة بنظام عائلة $OS!${NC}"
